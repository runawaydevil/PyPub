from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from pypub import __user_agent__
from pypub.domain.editor_modes import normalize_editor_mode
from pypub.domain.exceptions import MicropubError
from pypub.domain.models import Draft


class MicropubClient:
    def __init__(
        self,
        endpoint: str,
        access_token: str,
        *,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ):
        self.endpoint = endpoint
        self.access_token = access_token
        self.client = client or httpx.Client(
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
                "User-Agent": __user_agent__,
            },
            timeout=timeout,
        )
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def get_config(self) -> dict:
        try:
            response = self.client.get(self.endpoint, params={"q": "config"})
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise MicropubError(f"Failed to fetch Micropub config: {exc}") from exc

    def get_source(self, url: str) -> dict:
        try:
            response = self.client.get(self.endpoint, params={"q": "source", "url": url})
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise MicropubError(f"Failed to fetch source: {exc}") from exc

    def upload_media(self, media_endpoint: str, file_path: str, mime_type: str) -> str:
        try:
            with open(file_path, "rb") as file_obj:
                files = {"file": (Path(file_path).name, file_obj, mime_type)}
                response = self.client.post(media_endpoint, files=files)
                response.raise_for_status()
            location = response.headers.get("Location")
            if not location:
                raise MicropubError("Media endpoint did not return a Location header")
            return location
        except MicropubError:
            raise
        except Exception as exc:
            raise MicropubError(f"Media upload failed: {exc}") from exc

    def build_payload(self, draft: Draft, custom_properties: dict | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": ["h-entry"],
            "properties": {},
        }
        mode = normalize_editor_mode(draft.content_mode)

        if draft.title:
            payload["properties"]["name"] = [draft.title]
        if draft.summary:
            payload["properties"]["summary"] = [draft.summary]
        if draft.categories:
            payload["properties"]["category"] = draft.categories
        if draft.in_reply_to:
            payload["properties"]["in-reply-to"] = [draft.in_reply_to]
        if draft.like_of:
            payload["properties"]["like-of"] = [draft.like_of]
        if draft.repost_of:
            payload["properties"]["repost-of"] = [draft.repost_of]
        if draft.bookmark_of:
            payload["properties"]["bookmark-of"] = [draft.bookmark_of]

        if mode in ("html", "rich_text"):
            html_content = draft.content_html or draft.rich_text_html_snapshot
            if html_content:
                payload["properties"]["content"] = [{"html": html_content}]
        elif mode == "markdown":
            if draft.content_markdown_source:
                payload["properties"]["content"] = [draft.content_markdown_source]
        elif draft.content_plain:
            payload["properties"]["content"] = [draft.content_plain]

        attachments = json.loads(draft.attachments_json or "[]")
        photos = []
        for attachment in attachments:
            uploaded_url = attachment.get("uploaded_url")
            if not uploaded_url:
                continue
            alt_text = (attachment.get("alt_text") or "").strip()
            if alt_text:
                photos.append({"value": uploaded_url, "alt": alt_text})
            else:
                photos.append(uploaded_url)
        if photos:
            payload["properties"]["photo"] = photos

        if custom_properties:
            payload["properties"].update(custom_properties)

        return payload

    def create_post(self, draft: Draft, custom_properties: dict | None = None) -> str:
        payload = self.build_payload(draft, custom_properties=custom_properties)
        try:
            response = self.client.post(self.endpoint, json=payload)
            response.raise_for_status()
            return response.headers.get("Location", "")
        except httpx.HTTPStatusError as exc:
            error_details = exc.response.text
            raise MicropubError(
                f"Micropub publish failed: {exc.response.status_code} - {error_details}"
            ) from exc
        except Exception as exc:
            raise MicropubError(f"Failed to create post: {exc}") from exc
