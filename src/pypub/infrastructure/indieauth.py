import httpx
import secrets
import hashlib
import base64
import urllib.parse
import json
from bs4 import BeautifulSoup
from pypub.domain.exceptions import IndieAuthError

def generate_pkce() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(hashed).decode('ascii').rstrip('=')
    return code_verifier, code_challenge

class IndieAuthClient:
    def __init__(self, client_id: str, redirect_uri: str):
        self.client_id = client_id
        self.redirect_uri = redirect_uri

    def discover_endpoints(self, me_url: str) -> dict:
        """
        Descobre os endpoints a partir do `me_url` do usuário usando Link headers ou HTML.
        """
        try:
            r = httpx.get(me_url, follow_redirects=True, timeout=10.0)
            r.raise_for_status()
        except Exception as e:
            raise IndieAuthError(f"Failed to fetch {me_url}: {e}")

        links = {}
        # Simple HTML parsing (In a real app, also check HTTP Link headers)
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.find_all('link'):
                rel = link.get('rel', [])
                href = link.get('href')
                if not href:
                    continue
                if isinstance(rel, list):
                    for r_val in rel:
                        if r_val not in links:
                            links[r_val] = href
                else:
                    if rel not in links:
                        links[rel] = href
        except ImportError:
            pass # Requires beautifulsoup4, fallback to regex could be added here if not installed

        # Extract metadata if available
        metadata_url = links.get('indieauth-metadata')
        if metadata_url:
            metadata_url = urllib.parse.urljoin(str(r.url), metadata_url)
            try:
                mr = httpx.get(metadata_url, timeout=10.0)
                mr.raise_for_status()
                metadata = mr.json()
                return {
                    "me": str(r.url),
                    "authorization_endpoint": metadata.get("authorization_endpoint"),
                    "token_endpoint": metadata.get("token_endpoint"),
                    "micropub": links.get("micropub"),
                    "raw_metadata": json.dumps(metadata)
                }
            except Exception:
                pass # Fallback to direct links if metadata fetching fails

        return {
            "me": str(r.url),
            "authorization_endpoint": links.get("authorization_endpoint"),
            "token_endpoint": links.get("token_endpoint"),
            "micropub": links.get("micropub", ""),
            "raw_metadata": "{}"
        }

    def build_authorization_url(self, authorization_endpoint: str, me: str, state: str, code_challenge: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "me": me,
            "scope": "create update delete undelete media"
        }
        return f"{authorization_endpoint}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, token_endpoint: str, code: str, code_verifier: str) -> dict:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier
        }
        try:
            r = httpx.post(token_endpoint, data=data, timeout=10.0)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise IndieAuthError(f"Failed to exchange code: {e}")
