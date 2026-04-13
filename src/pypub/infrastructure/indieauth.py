from __future__ import annotations

import base64
import hashlib
import json
import secrets
import urllib.parse
from html.parser import HTMLParser

import httpx

from pypub import __user_agent__
from pypub.domain.exceptions import IndieAuthError


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        attr_map = {key.lower(): value for key, value in attrs if value is not None}
        href = attr_map.get("href")
        rel = attr_map.get("rel")
        if not href or not rel:
            return
        for rel_value in rel.split():
            self.links.setdefault(rel_value, href)


def generate_pkce() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(hashed).decode("ascii").rstrip("=")
    return code_verifier, code_challenge


def _collect_html_links(html: str) -> dict[str, str]:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        parser = _LinkCollector()
        parser.feed(html or "")
        parser.close()
        return parser.links

    links: dict[str, str] = {}
    soup = BeautifulSoup(html or "", "html.parser")
    for link in soup.find_all("link"):
        rel_values = link.get("rel", [])
        href = link.get("href")
        if not href:
            continue
        if isinstance(rel_values, str):
            rel_values = rel_values.split()
        for rel_value in rel_values:
            links.setdefault(str(rel_value), href)
    return links


def _collect_header_links(header_value: str | None) -> dict[str, str]:
    if not header_value:
        return {}
    links: dict[str, str] = {}
    for raw_part in header_value.split(","):
        part = raw_part.strip()
        if not (part.startswith("<") and ">;" in part):
            continue
        href, params_blob = part.split(">;", 1)
        href = href[1:]
        rel = None
        for raw_param in params_blob.split(";"):
            param = raw_param.strip()
            if param.startswith("rel="):
                rel = param.split("=", 1)[1].strip().strip('"')
                break
        if not rel:
            continue
        for rel_value in rel.split():
            links.setdefault(rel_value, href)
    return links


def _absolutize_links(base_url: str, links: dict[str, str]) -> dict[str, str]:
    return {rel: urllib.parse.urljoin(base_url, href) for rel, href in links.items()}


class IndieAuthClient:
    def __init__(
        self,
        client_id: str,
        redirect_uri: str,
        *,
        timeout: float = 10.0,
        client: httpx.Client | None = None,
    ):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.timeout = timeout
        self.client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": __user_agent__, "Accept": "application/json, text/html;q=0.9"},
        )
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def discover_endpoints(self, me_url: str) -> dict:
        """
        Discover IndieAuth endpoints from HTTP Link headers, HTML links, and metadata.
        """
        try:
            response = self.client.get(me_url)
            response.raise_for_status()
        except Exception as exc:
            raise IndieAuthError(f"Failed to fetch {me_url}: {exc}") from exc

        discovered = _collect_header_links(response.headers.get("Link"))
        discovered.update(
            {
                rel: href
                for rel, href in _collect_html_links(response.text).items()
                if rel not in discovered
            }
        )
        links = _absolutize_links(str(response.url), discovered)

        metadata_url = links.get("indieauth-metadata")
        metadata: dict[str, object] = {}
        if metadata_url:
            try:
                metadata_response = self.client.get(metadata_url, headers={"Accept": "application/json"})
                metadata_response.raise_for_status()
                metadata = metadata_response.json()
            except Exception:
                metadata = {}

        authorization_endpoint = str(
            metadata.get("authorization_endpoint") or links.get("authorization_endpoint") or ""
        )
        token_endpoint = str(metadata.get("token_endpoint") or links.get("token_endpoint") or "")
        micropub_endpoint = str(metadata.get("micropub") or links.get("micropub") or "")

        if not authorization_endpoint and not token_endpoint and not micropub_endpoint:
            raise IndieAuthError("No IndieAuth or Micropub endpoints were discovered.")

        return {
            "me": str(response.url),
            "authorization_endpoint": authorization_endpoint,
            "token_endpoint": token_endpoint,
            "micropub": micropub_endpoint,
            "raw_metadata": json.dumps(metadata or {}, ensure_ascii=False),
        }

    def build_authorization_url(
        self,
        authorization_endpoint: str,
        me: str,
        state: str,
        code_challenge: str,
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "me": me,
            "scope": "create update delete undelete media",
        }
        return f"{authorization_endpoint}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, token_endpoint: str, code: str, code_verifier: str) -> dict:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier,
        }
        try:
            response = self.client.post(
                token_endpoint,
                data=data,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise IndieAuthError(f"Failed to exchange code: {exc}") from exc
