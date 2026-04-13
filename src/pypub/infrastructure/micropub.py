import httpx
import json
from pathlib import Path
from typing import Optional, Dict, Any
from pypub.domain.models import Draft
from pypub.domain.exceptions import MicropubError

class MicropubClient:
    def __init__(self, endpoint: str, access_token: str):
        self.endpoint = endpoint
        self.access_token = access_token
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=15.0
        )

    def get_config(self) -> dict:
        try:
            r = self.client.get(self.endpoint, params={"q": "config"})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {}

    def get_source(self, url: str) -> dict:
        try:
            r = self.client.get(self.endpoint, params={"q": "source", "url": url})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise MicropubError(f"Failed to fetch source: {e}")

    def upload_media(self, media_endpoint: str, file_path: str, mime_type: str) -> str:
        try:
            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f, mime_type)}
                r = self.client.post(media_endpoint, files=files)
                r.raise_for_status()
                location = r.headers.get("Location")
                if not location:
                    raise MicropubError("Media endpoint did not return a Location header")
                return location
        except Exception as e:
            raise MicropubError(f"Media upload failed: {e}")

    def create_post(self, draft: Draft, custom_properties: dict = None) -> str:
        """
        Builds the payload and creates the post.
        Uses JSON representation.
        """
        payload = {
            "type": ["h-entry"],
            "properties": {}
        }

        # Handle simple properties
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
        
        # Content format decision
        if draft.content_mode == "html" and draft.content_html:
            payload["properties"]["content"] = [{"html": draft.content_html}]
        elif draft.content_plain:
            payload["properties"]["content"] = [draft.content_plain]

        # Attachments mapping
        attachments = json.loads(draft.attachments_json)
        photos = []
        for att in attachments:
            if att.get('uploaded_url'):
                if att.get('alt_text'):
                    photos.append({"value": att.get('uploaded_url'), "alt": att.get('alt_text')})
                else:
                    photos.append(att.get('uploaded_url'))
            # Future: handle audio/video

        if photos:
            payload["properties"]["photo"] = photos

        # Advanced custom properties
        if custom_properties:
            payload["properties"].update(custom_properties)

        try:
            r = self.client.post(self.endpoint, json=payload)
            r.raise_for_status()
            return r.headers.get("Location", "")
        except httpx.HTTPStatusError as e:
            error_details = e.response.text
            raise MicropubError(f"HTTPStatusError building post: {e.response.status_code} - {error_details}")
        except Exception as e:
            raise MicropubError(f"Failed to create post: {e}")

    def close(self):
        self.client.close()
