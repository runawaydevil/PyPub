# PyPub - A Desktop Micropub Client
# Developed by Pablo Murad <pmurad@disroot.org>
# Version: 0.0.1

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, HttpUrl, Field

from pypub.domain.editor_modes import DEFAULT_EDITOR_MODE, EditorMode

class Account(BaseModel):
    id: int | None = None
    display_name: str
    me_url: str
    canonical_me_url: str
    client_id: str
    client_uri: str
    redirect_uri: str
    authorization_endpoint: str
    token_endpoint: str
    micropub_endpoint: str
    media_endpoint: str | None = None
    last_discovered_at: datetime
    scopes_granted: str
    raw_metadata_json: str

class TokenInfo(BaseModel):
    account_id: int
    access_token: str # Em memória, o SQLite não salvará isso. Vai para o keyring
    refresh_token: str | None = None
    expires_at: datetime | None = None
    scope: str
    raw_token_response_json: str

class Draft(BaseModel):
    id: int | None = None
    account_id: int
    status: str = "draft" # draft, queued, published, failed
    entry_type: str = "note" # note, article, reply, like, repost, photo
    title: str | None = None
    summary: str | None = None
    content_plain: str | None = None
    content_html: str | None = None
    content_markdown_source: str | None = None
    content_mode: EditorMode = DEFAULT_EDITOR_MODE
    categories: list[str] = Field(default_factory=list)
    published_at: str | None = None
    updated_at: str | None = None
    in_reply_to: str | None = None
    like_of: str | None = None
    repost_of: str | None = None
    bookmark_of: str | None = None
    syndication_targets: list[str] = Field(default_factory=list)
    post_status: str | None = None
    visibility: str | None = None
    location_name: str | None = None
    location_geo_uri: str | None = None
    extra_properties_json: str = "{}"
    attachments_json: str = "[]"
    remote_post_url: str | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None
    
    # Phase 2 Fields
    rich_text_html_snapshot: str | None = None
    recovery_snapshot_json: str | None = None
    is_dirty: bool = False
    last_autosave_at: datetime | None = None

class Attachment(BaseModel):
    id: int | None = None
    draft_id: int
    local_path: str
    mime_type: str
    media_kind: str # photo, video, audio, file
    alt_text: str | None = None
    uploaded_url: str | None = None
    upload_state: str = "pending" # pending, uploaded, failed
    upload_error: str | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    size_bytes: int | None = None

class RemotePostSource(BaseModel):
    url: str
    type_list: list[str] = Field(default_factory=list)
    properties_json: str
    raw_response_json: str
    last_fetched_at: datetime

class ServerCapabilities(BaseModel):
    account_id: int
    supports_media_endpoint: bool = False
    supports_q_config: bool = False
    supports_q_source: bool = False
    supports_q_syndicate_to: bool = False
    supported_syndication_targets_json: str = "[]"
    raw_config_json: str = "{}"
