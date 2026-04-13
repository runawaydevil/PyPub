import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from pypub.domain.models import Account, Draft, Attachment

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
            cursor.execute("SELECT * FROM accounts")
            return [Account(**dict(row)) for row in cursor.fetchall()]

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
            
    def get_drafts(self, account_id: int) -> List[Draft]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drafts WHERE account_id = ? ORDER BY id DESC", (account_id,))
            rows = cursor.fetchall()
            drafts = []
            for row in rows:
                d = dict(row)
                d['categories'] = json.loads(d['categories']) if d['categories'] else []
                d['syndication_targets'] = json.loads(d['syndication_targets']) if d['syndication_targets'] else []
                
                # Check for is_dirty boolean mapping correctly
                d['is_dirty'] = bool(d.get('is_dirty', False))

                drafts.append(Draft(**d))
            return drafts
