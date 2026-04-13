"""Smoke tests for editor_sync (no Qt widgets)."""

from pypub.application import editor_sync
from pypub.application.editor_sync import (
    attachment_url,
    merge_attachments_from_html,
    prepare_draft_for_publish,
    sync_draft_body_from_editor,
)
from pypub.domain.models import Draft


def test_attachment_url_roundtrip_prefix():
    aid = "abc-123"
    u = attachment_url(aid)
    assert u.startswith(editor_sync.ATTACHMENT_PREFIX)
    assert aid in u


def test_merge_attachments_from_html_creates_row_for_embedded_ref():
    aid = "11111111-1111-1111-1111-111111111111"
    html = f'<p><img src="{attachment_url(aid)}" alt="x" /></p>'
    merged = merge_attachments_from_html(html, [])
    ids = {str(m["id"]) for m in merged}
    assert aid in ids


def test_sync_draft_body_from_editor_sets_fields():
    d = Draft(account_id=1)
    out = sync_draft_body_from_editor(
        d,
        "T",
        "S",
        "<p>hi</p>",
        "article",
        "https://reply.example",
        None,
        None,
        "https://bm.example",
        "[]",
    )
    assert out.title == "T"
    assert out.summary == "S"
    assert out.entry_type == "article"
    assert out.in_reply_to == "https://reply.example"
    assert out.bookmark_of == "https://bm.example"
    assert out.content_mode == "rich_text"


def test_prepare_draft_for_publish_replaces_pypub_src():
    aid = "22222222-2222-2222-2222-222222222222"
    d = Draft(
        account_id=1,
        content_mode="rich_text",
        content_html=f'<img src="{attachment_url(aid)}" alt="" />',
        attachments_json='[{"id":"'
        + aid
        + '","local_path":"","mime_type":"image/png","alt_text":"","uploaded_url":"https://cdn.example/i.png","upload_state":"uploaded"}]',
    )
    out = prepare_draft_for_publish(d)
    assert out.content_mode == "html"
    assert "https://cdn.example/i.png" in (out.content_html or "")
    assert attachment_url(aid) not in (out.content_html or "")
