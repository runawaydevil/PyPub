import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from pypub.domain.editor_modes import normalize_editor_mode
from pypub.domain.models import Account, Draft, ServerCapabilities

class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
        self._migrate_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    display_name TEXT,
                    me_url TEXT UNIQUE,
                    canonical_me_url TEXT,
                    client_id TEXT,
                    client_uri TEXT,
                    redirect_uri TEXT,
                    authorization_endpoint TEXT,
                    token_endpoint TEXT,
                    micropub_endpoint TEXT,
                    media_endpoint TEXT,
                    last_discovered_at TIMESTAMP,
                    scopes_granted TEXT,
                    raw_metadata_json TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    status TEXT,
                    entry_type TEXT,
                    title TEXT,
                    summary TEXT,
                    content_plain TEXT,
                    content_html TEXT,
                    content_markdown_source TEXT,
                    content_mode TEXT,
                    categories TEXT,
                    published_at TEXT,
                    updated_at TEXT,
                    in_reply_to TEXT,
                    like_of TEXT,
                    repost_of TEXT,
                    bookmark_of TEXT,
                    syndication_targets TEXT,
                    post_status TEXT,
                    visibility TEXT,
                    location_name TEXT,
                    location_geo_uri TEXT,
                    extra_properties_json TEXT,
                    attachments_json TEXT,
                    remote_post_url TEXT,
                    created_at TIMESTAMP,
                    modified_at TIMESTAMP,
                    FOREIGN KEY(account_id) REFERENCES accounts(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS capabilities (
                    account_id INTEGER PRIMARY KEY,
                    supports_media_endpoint BOOLEAN,
                    supports_q_config BOOLEAN,
                    supports_q_source BOOLEAN,
                    supports_q_syndicate_to BOOLEAN,
                    supported_syndication_targets_json TEXT,
                    raw_config_json TEXT,
                    FOREIGN KEY(account_id) REFERENCES accounts(id)
                )
            """)
            conn.commit()

    def _migrate_db(self):
        # Phase 2 migrations
        cols = [
            ("rich_text_html_snapshot", "TEXT"),
            ("recovery_snapshot_json", "TEXT"),
            ("is_dirty", "BOOLEAN DEFAULT False"),
            ("last_autosave_at", "TIMESTAMP")
        ]
        with sqlite3.connect(self.db_path) as conn:
            for col_name, col_type in cols:
                try:
                    conn.execute(f"ALTER TABLE drafts ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass # Column exists

    # --- ACCOUNTS ---
    def save_account(self, account: Account) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = """
            INSERT INTO accounts (
                display_name, me_url, canonical_me_url, client_id, client_uri, redirect_uri,
                authorization_endpoint, token_endpoint, micropub_endpoint, media_endpoint,
                last_discovered_at, scopes_granted, raw_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(me_url) DO UPDATE SET
                display_name=excluded.display_name,
                canonical_me_url=excluded.canonical_me_url,
                authorization_endpoint=excluded.authorization_endpoint,
                token_endpoint=excluded.token_endpoint,
                micropub_endpoint=excluded.micropub_endpoint,
                media_endpoint=excluded.media_endpoint,
                last_discovered_at=excluded.last_discovered_at,
                scopes_granted=excluded.scopes_granted,
                raw_metadata_json=excluded.raw_metadata_json
            """
            cursor.execute(query, (
                account.display_name, account.me_url, account.canonical_me_url, account.client_id,
                account.client_uri, account.redirect_uri, account.authorization_endpoint,
                account.token_endpoint, account.micropub_endpoint, account.media_endpoint,
                account.last_discovered_at.isoformat() if account.last_discovered_at else None,
                account.scopes_granted, account.raw_metadata_json
            ))
            conn.commit()
            if cursor.lastrowid:
                return cursor.lastrowid
            cursor.execute("SELECT id FROM accounts WHERE me_url = ?", (account.me_url,))
            return cursor.fetchone()[0]

    def get_accounts(self) -> List[Account]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts ORDER BY id ASC")
            return [Account(**dict(row)) for row in cursor.fetchall()]

    def delete_account(self, account_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM capabilities WHERE account_id = ?", (account_id,))
            conn.execute("DELETE FROM drafts WHERE account_id = ?", (account_id,))
            conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            conn.commit()

    # --- CAPABILITIES ---
    def save_capabilities(self, capabilities: ServerCapabilities) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO capabilities (
                    account_id, supports_media_endpoint, supports_q_config,
                    supports_q_source, supports_q_syndicate_to,
                    supported_syndication_targets_json, raw_config_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id) DO UPDATE SET
                    supports_media_endpoint=excluded.supports_media_endpoint,
                    supports_q_config=excluded.supports_q_config,
                    supports_q_source=excluded.supports_q_source,
                    supports_q_syndicate_to=excluded.supports_q_syndicate_to,
                    supported_syndication_targets_json=excluded.supported_syndication_targets_json,
                    raw_config_json=excluded.raw_config_json
                """,
                (
                    capabilities.account_id,
                    capabilities.supports_media_endpoint,
                    capabilities.supports_q_config,
                    capabilities.supports_q_source,
                    capabilities.supports_q_syndicate_to,
                    capabilities.supported_syndication_targets_json,
                    capabilities.raw_config_json,
                ),
            )
            conn.commit()

    def get_capabilities(self, account_id: int) -> Optional[ServerCapabilities]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM capabilities WHERE account_id = ?", (account_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return ServerCapabilities(**dict(row))

    # --- DRAFTS ---
    def save_draft(self, draft: Draft) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if draft.id is None:
                cursor.execute("""
                    INSERT INTO drafts (
                        account_id, status, entry_type, title, summary, content_plain, content_html,
                        content_markdown_source, content_mode, categories, published_at, updated_at,
                        in_reply_to, like_of, repost_of, bookmark_of, syndication_targets,
                        post_status, visibility, location_name, location_geo_uri, extra_properties_json,
                        attachments_json, remote_post_url, created_at, modified_at,
                        rich_text_html_snapshot, recovery_snapshot_json, is_dirty, last_autosave_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    draft.account_id, draft.status, draft.entry_type, draft.title, draft.summary,
                    draft.content_plain, draft.content_html, draft.content_markdown_source, draft.content_mode,
                    json.dumps(draft.categories), draft.published_at, draft.updated_at,
                    draft.in_reply_to, draft.like_of, draft.repost_of, draft.bookmark_of,
                    json.dumps(draft.syndication_targets), draft.post_status, draft.visibility,
                    draft.location_name, draft.location_geo_uri, draft.extra_properties_json,
                    draft.attachments_json, draft.remote_post_url,
                    draft.created_at.isoformat() if draft.created_at else None,
                    draft.modified_at.isoformat() if draft.modified_at else None,
                    draft.rich_text_html_snapshot, draft.recovery_snapshot_json, draft.is_dirty,
                    draft.last_autosave_at.isoformat() if draft.last_autosave_at else None
                ))
                draft.id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE drafts SET
                        status=?, entry_type=?, title=?, summary=?, content_plain=?, content_html=?,
                        content_markdown_source=?, content_mode=?, categories=?, published_at=?, updated_at=?,
                        in_reply_to=?, like_of=?, repost_of=?, bookmark_of=?, syndication_targets=?,
                        post_status=?, visibility=?, location_name=?, location_geo_uri=?, extra_properties_json=?,
                        attachments_json=?, remote_post_url=?, modified_at=?,
                        rich_text_html_snapshot=?, recovery_snapshot_json=?, is_dirty=?, last_autosave_at=?
                    WHERE id=? AND account_id=?
                """, (
                    draft.status, draft.entry_type, draft.title, draft.summary, draft.content_plain, draft.content_html,
                    draft.content_markdown_source, draft.content_mode, json.dumps(draft.categories), draft.published_at, draft.updated_at,
                    draft.in_reply_to, draft.like_of, draft.repost_of, draft.bookmark_of, json.dumps(draft.syndication_targets),
                    draft.post_status, draft.visibility, draft.location_name, draft.location_geo_uri, draft.extra_properties_json,
                    draft.attachments_json, draft.remote_post_url, draft.modified_at.isoformat() if draft.modified_at else None,
                    draft.rich_text_html_snapshot, draft.recovery_snapshot_json, draft.is_dirty, draft.last_autosave_at.isoformat() if draft.last_autosave_at else None,
                    draft.id, draft.account_id
                ))
            conn.commit()
            return draft.id
            
    @staticmethod
    def _draft_from_row(row: sqlite3.Row) -> Draft:
        d = dict(row)
        d["categories"] = json.loads(d["categories"]) if d.get("categories") else []
        d["syndication_targets"] = (
            json.loads(d["syndication_targets"]) if d.get("syndication_targets") else []
        )
        d["is_dirty"] = bool(d.get("is_dirty", False))
        d["content_mode"] = normalize_editor_mode(d.get("content_mode"))
        return Draft(**d)

    def get_drafts(self, account_id: int) -> List[Draft]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drafts WHERE account_id = ? ORDER BY id DESC", (account_id,))
            rows = cursor.fetchall()
            return [self._draft_from_row(row) for row in rows]

    def get_draft_by_id(self, account_id: int, draft_id: int) -> Optional[Draft]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM drafts WHERE account_id = ? AND id = ?",
                (account_id, draft_id),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._draft_from_row(row)
