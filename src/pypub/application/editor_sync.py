"""
Sync between QTextDocument HTML, Draft fields, and attachments_json.
Uses pypub://attachment/<uuid> in HTML for stable references before publish.
"""

from __future__ import annotations

import json
import uuid
from html.parser import HTMLParser
from typing import Any

from pypub.domain.editor_modes import normalize_editor_mode
from pypub.domain.models import Draft


ATTACHMENT_PREFIX = "pypub://attachment/"


def _parse_attachments(raw: str) -> list[dict[str, Any]]:
    if not raw or raw.strip() in ("", "[]"):
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _dump_attachments(items: list[dict[str, Any]]) -> str:
    return json.dumps(items, ensure_ascii=False)


def ensure_attachment_ids(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for it in items:
        row = dict(it)
        if not row.get("id"):
            row["id"] = str(uuid.uuid4())
        row.setdefault("mime_type", "application/octet-stream")
        row.setdefault("alt_text", "")
        row.setdefault("upload_state", "pending")
        row.setdefault("uploaded_url", None)
        row.setdefault("embedded_in_document", False)
        row.setdefault("order", 0)
        row.setdefault("width_preset", "full")
        row.setdefault("align", "default")
        out.append(row)
    return out


class _ImgSrcCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        ad = {k.lower(): v for k, v in attrs if v is not None}
        src = ad.get("src")
        if src:
            self.srcs.append(src)


def collect_img_srcs_from_html(html: str) -> list[str]:
    p = _ImgSrcCollector()
    try:
        p.feed(html or "")
        p.close()
    except Exception:
        pass
    return p.srcs


def merge_attachments_from_html(
    html: str,
    existing: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Ensure every pypub://attachment/id in HTML has a row; keep other rows with local_path."""
    by_id = {str(a.get("id")): dict(a) for a in existing if a.get("id")}
    for src in collect_img_srcs_from_html(html):
        if not src.startswith(ATTACHMENT_PREFIX):
            continue
        aid = src[len(ATTACHMENT_PREFIX) :].split("/")[0].split("?")[0]
        if aid and aid not in by_id:
            by_id[aid] = {
                "id": aid,
                "local_path": "",
                "mime_type": "image/png",
                "alt_text": "",
                "uploaded_url": None,
                "upload_state": "pending",
                "embedded_in_document": True,
                "order": len(by_id),
            }
    merged = list(by_id.values())
    merged.sort(key=lambda x: int(x.get("order", 0)))
    return ensure_attachment_ids(merged)


def attachment_url(att_id: str) -> str:
    return f"{ATTACHMENT_PREFIX}{att_id}"


def prepare_draft_for_publish(draft: Draft) -> Draft:
    """
    Normalize rich_text / html body so MicropubClient receives content_mode 'html'
    and resolved image URLs in content_html.
    """
    from pathlib import Path

    from PySide6.QtCore import QUrl

    d = draft.model_copy(deep=True)
    d.content_mode = normalize_editor_mode(d.content_mode)
    html = d.content_html or d.rich_text_html_snapshot or ""
    if d.content_mode in ("rich_text", "html") and html:
        atts = _parse_attachments(d.attachments_json)
        for att in atts:
            url = att.get("uploaded_url")
            aid = att.get("id")
            if not url or not aid:
                continue
            token = attachment_url(str(aid))
            html = html.replace(token, url)
            lp = att.get("local_path") or ""
            if lp and Path(lp).is_file():
                fu = QUrl.fromLocalFile(str(Path(lp).resolve())).toString()
                html = html.replace(fu, url)
        d.content_html = html
        d.content_mode = "html"
    elif d.content_mode == "rich_text" and d.rich_text_html_snapshot:
        d.content_html = d.rich_text_html_snapshot
        d.content_mode = "html"
    elif d.content_mode == "plain":
        d.content_html = None
        d.rich_text_html_snapshot = None
    elif d.content_mode == "markdown":
        d.content_html = None
    return d


def sync_draft_body_from_editor(
    draft: Draft,
    title: str | None,
    summary: str | None,
    body_html: str,
    entry_type: str,
    in_reply_to: str | None,
    like_of: str | None,
    repost_of: str | None,
    bookmark_of: str | None,
    existing_attachments_json: str,
) -> Draft:
    d = draft.model_copy(deep=True)
    d.title = title or None
    d.summary = summary or None
    d.content_mode = normalize_editor_mode("rich_text")
    d.content_plain = None
    d.content_markdown_source = None
    d.content_html = body_html
    d.rich_text_html_snapshot = body_html
    d.entry_type = entry_type
    d.in_reply_to = in_reply_to or None
    d.like_of = like_of or None
    d.repost_of = repost_of or None
    d.bookmark_of = bookmark_of or None
    merged = merge_attachments_from_html(body_html, _parse_attachments(existing_attachments_json))
    d.attachments_json = _dump_attachments(merged)
    return d
