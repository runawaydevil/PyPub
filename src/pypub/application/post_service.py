from pypub.domain.models import Draft, Account, ServerCapabilities
from pypub.infrastructure.db import Database
from pypub.infrastructure.micropub import MicropubClient
from pypub.infrastructure.keyring_store import KeyringStore
import json

class PostService:
    def __init__(self, db: Database, keyring_store: KeyringStore):
        self.db = db
        self.keyring_store = keyring_store

    def get_drafts(self, account_id: int) -> list[Draft]:
        return self.db.get_drafts(account_id)

    def save_draft(self, draft: Draft) -> int:
        return self.db.save_draft(draft)

    def fetch_capabilities(self, account: Account) -> ServerCapabilities:
        token = self.keyring_store.get_token(account.id)
        if not token:
            raise ValueError("No access token found for account.")
        
        client = MicropubClient(account.micropub_endpoint, token)
        config = client.get_config()
        client.close()

        media_endpoint = config.get("media-endpoint")
        if media_endpoint:
            account.media_endpoint = media_endpoint
            self.db.save_account(account)

        caps = ServerCapabilities(
            account_id=account.id,
            supports_media_endpoint=bool(media_endpoint),
            supports_q_config=True, # It worked
            supports_q_source=bool(config.get("q", []) and "source" in config.get("q")),
            supports_q_syndicate_to=bool("syndicate-to" in config),
            supported_syndication_targets_json=json.dumps(config.get("syndicate-to", [])),
            raw_config_json=json.dumps(config)
        )
        return caps

    def upload_attachment(self, account: Account, file_path: str, mime_type: str) -> str:
        token = self.keyring_store.get_token(account.id)
        if not token:
            raise ValueError("No access token found.")
        if not account.media_endpoint:
            raise ValueError("Media endpoint not discovered yet.")
        
        client = MicropubClient(account.micropub_endpoint, token)
        url = client.upload_media(account.media_endpoint, file_path, mime_type)
        client.close()
        return url

    def publish_draft(self, account: Account, draft: Draft) -> str:
        token = self.keyring_store.get_token(account.id)
        if not token:
            raise ValueError("No access token found.")

        # Converts Markdown local view to HTML if needed?
        if draft.content_mode == "markdown":
            try:
                from markdown_it import MarkdownIt
                md = MarkdownIt('commonmark')
                draft.content_html = md.render(draft.content_markdown_source or "")
                draft.content_mode = "html" # prepare for sending
            except ImportError:
                draft.content_plain = draft.content_markdown_source

        client = MicropubClient(account.micropub_endpoint, token)
        location = client.create_post(draft)
        client.close()

        draft.status = "published"
        draft.remote_post_url = location
        self.db.save_draft(draft)
        return location
