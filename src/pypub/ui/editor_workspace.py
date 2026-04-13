"""
Compose workspace: document-first column, collapsible right drawer, bottom tabs.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from pypub.application.conversion import ConversionManager
from pypub.application.editor_sync import (
    attachment_url,
    prepare_draft_for_publish,
    sync_draft_body_from_editor,
)
from pypub.application.sanitization import sanitize_html
from pypub.domain.editor_modes import DEFAULT_EDITOR_MODE, normalize_editor_mode
from pypub.domain.models import Draft
from pypub.ui.editor.compose_header import ComposeHeader
from pypub.ui.editor.document_canvas import DocumentCanvas
from pypub.ui.editor.floating_format_bar import FloatingFormatBar
from pypub.ui.editor.format_toolbar import FormatToolbar
from pypub.ui.editor.preset_layouts import PresetContextPanel
from pypub.ui.editor.slash_menu import SlashMenuPopup
from pypub.ui.media_panel import MediaPanel
from pypub.ui.remote_edit import RemoteEditPanel


class EditorWorkspace(QWidget):
    def __init__(self, post_service, app_data_dir, settings_manager):
        super().__init__()
        self.setObjectName("ComposeWorkspace")
        self.post_service = post_service
        self.app_data_dir = app_data_dir
        self.settings_manager = settings_manager

        self.account = None
        self.current_draft = Draft(account_id=-1, content_mode=DEFAULT_EDITOR_MODE)
        self.conversion_manager = ConversionManager()

        self.autosave_timer = QTimer()
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self._autosave)

        self._float_timer = QTimer()
        self._float_timer.setSingleShot(True)
        self._float_timer.timeout.connect(self._reposition_float)

        self._slash_popup = SlashMenuPopup(self)
        self._floating: FloatingFormatBar | None = None

        self._preview_tab_index: int | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        s = self.settings_manager.settings
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.compose_header = ComposeHeader(self.save_draft_manual, self.publish, self)
        self.compose_header.type_combo.currentTextChanged.connect(self._on_preset_changed)
        root.addWidget(self.compose_header)

        self.canvas = DocumentCanvas(
            os.path.join(self.app_data_dir, "media_cache"),
            s,
            self,
        )
        self.format_toolbar = FormatToolbar(
            self.canvas.editor,
            self._toggle_preview,
            self._toggle_metadata_drawer,
            self._toggle_inspector_tab,
            self,
        )
        root.addWidget(self.format_toolbar)

        self.outer_split = QSplitter(Qt.Orientation.Horizontal)
        self.outer_split.setObjectName("ComposeOuterSplit")

        self.center_column = QWidget()
        cc_lay = QVBoxLayout(self.center_column)
        cc_lay.setContentsMargins(0, 0, 0, 0)
        cc_lay.setSpacing(0)

        self.preset_panel = PresetContextPanel(self.center_column)
        cc_lay.addWidget(self.preset_panel)

        self.center_doc_split = QSplitter(Qt.Orientation.Horizontal)
        self.center_doc_split.setObjectName("CenterDocSplit")

        self.doc_wrap = QWidget()
        dw = QVBoxLayout(self.doc_wrap)
        dw.setContentsMargins(0, 0, 0, 0)
        dw.addWidget(self.canvas, 1)
        self.center_doc_split.addWidget(self.doc_wrap)

        self.preview_side_host = QWidget()
        self.preview_side_host.setMinimumWidth(200)
        self._side_preview_layout = QVBoxLayout(self.preview_side_host)
        self._side_preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_side_host.setVisible(False)
        self.center_doc_split.addWidget(self.preview_side_host)

        self.center_doc_split.setStretchFactor(0, 1)
        self.center_doc_split.setStretchFactor(1, 0)

        cc_lay.addWidget(self.center_doc_split, 1)

        self.outer_split.addWidget(self.center_column)

        self.drawer = QWidget()
        self.drawer.setObjectName("DrawerPanel")
        self.drawer.setMinimumWidth(260)
        self.drawer.setMaximumWidth(480)
        dv = QVBoxLayout(self.drawer)
        dv.setContentsMargins(16, 16, 16, 16)
        dv.setSpacing(12)
        dt = QHBoxLayout()
        self.btn_drawer = QToolButton()
        self.btn_drawer.setObjectName("DrawerToggle")
        self.btn_drawer.setText("Hide panel")
        self.btn_drawer.clicked.connect(self._toggle_drawer_visible)
        title_block = QVBoxLayout()
        drawer_title = QLabel("Side panel")
        drawer_title.setObjectName("DrawerTitle")
        drawer_subtitle = QLabel("Media, remote posts, and related details are available here.")
        drawer_subtitle.setObjectName("DrawerSubtitle")
        drawer_subtitle.setWordWrap(True)
        title_block.addWidget(drawer_title)
        title_block.addWidget(drawer_subtitle)
        dt.addLayout(title_block)
        dt.addStretch()
        dt.addWidget(self.btn_drawer)
        dv.addLayout(dt)

        self.tabs = QTabWidget()
        self.media_panel = MediaPanel(
            self.post_service, os.path.join(self.app_data_dir, "media_cache"), self
        )
        self.media_panel.set_insert_callback(self._insert_image_ref_at_cursor)
        self.media_panel.attachmentsChanged.connect(self._trigger_autosave)
        self.tabs.addTab(self.media_panel, "Media")

        self.remote_panel = RemoteEditPanel(self.post_service, self._on_remote_loaded)
        self.tabs.addTab(self.remote_panel, "Remote")
        dv.addWidget(self.tabs, 1)
        self.outer_split.addWidget(self.drawer)

        self.outer_split.setStretchFactor(0, 5)
        self.outer_split.setStretchFactor(1, 1)
        root.addWidget(self.outer_split, 1)

        self.bottom = QFrame()
        self.bottom.setObjectName("BottomPanel")
        bl = QVBoxLayout(self.bottom)
        bl.setContentsMargins(4, 2, 4, 4)
        self.bottom_tabs = QTabWidget()
        self.preview_browser = QTextBrowser()
        self.preview_browser.setObjectName("PreviewReading")

        self._preview_bottom_host = QWidget()
        self._bottom_preview_layout = QVBoxLayout(self._preview_bottom_host)
        self._bottom_preview_layout.setContentsMargins(0, 0, 0, 0)
        self._bottom_preview_layout.addWidget(self.preview_browser)

        self.inspector = QTextEdit()
        self.inspector.setObjectName("InspectorLog")
        self.inspector.setReadOnly(True)

        self.bottom_tabs.addTab(self._preview_bottom_host, "Preview")
        self.bottom_tabs.addTab(self.inspector, "Inspector")
        bl.addWidget(self.bottom_tabs)
        root.addWidget(self.bottom)

        self._drawer_visible = not s.default_metadata_collapsed
        self.drawer.setVisible(self._drawer_visible)

        self._apply_preview_placement(init=True)

        self.canvas.editor.textChanged.connect(self._trigger_autosave)
        self.canvas.editor.selectionChangedForToolbar.connect(self._schedule_float)
        self.canvas.editor.slashMenuRequested.connect(self._open_slash_menu)
        self.canvas.editor.imageAttached.connect(self._on_image_attached)

        self.format_toolbar.set_toggle_memory(
            self.bottom.isVisible(),
            self.drawer.isVisible(),
            self.inspector.isVisible(),
        )

        self.title_edit = self.canvas.title_edit
        self.summary_edit = self.canvas.summary_edit
        self.title_edit.textChanged.connect(self._trigger_autosave)
        self.summary_edit.textChanged.connect(self._trigger_autosave)
        self.preset_panel.reply_in.textChanged.connect(self._trigger_autosave)
        self.preset_panel.like_in.textChanged.connect(self._trigger_autosave)
        self.preset_panel.repost_in.textChanged.connect(self._trigger_autosave)
        self.preset_panel.bookmark_in.textChanged.connect(self._trigger_autosave)

        self._floating = FloatingFormatBar(self.canvas.editor, self)

    def _detach_preview_browser(self) -> None:
        self._bottom_preview_layout.removeWidget(self.preview_browser)
        self._side_preview_layout.removeWidget(self.preview_browser)
        self.preview_browser.setParent(None)

    def _apply_preview_placement(self, init: bool = False) -> None:
        s = self.settings_manager.settings
        mode = s.default_preview_mode
        side_w = max(200, s.preview_side_panel_width_px)

        self._detach_preview_browser()
        if mode == "side":
            self._side_preview_layout.addWidget(self.preview_browser)
            self.preview_side_host.setVisible(True)
            self.preview_side_host.setMinimumWidth(side_w)
            self.preview_side_host.setMaximumWidth(side_w + 160)
            self.center_doc_split.setSizes([720, side_w])
            self.bottom_tabs.setTabVisible(0, False)
        else:
            self._bottom_preview_layout.addWidget(self.preview_browser)
            self.preview_side_host.setVisible(False)
            self.bottom_tabs.setTabVisible(0, True)

        if not init:
            return
        if mode == "hidden":
            self.bottom.setVisible(False)
        else:
            self.bottom.setVisible(True)
            self.inspector.setVisible(not s.default_inspector_collapsed)
            if not s.default_inspector_collapsed:
                self.bottom_tabs.setCurrentWidget(self.inspector)
            else:
                self.bottom_tabs.setCurrentWidget(self._preview_bottom_host)

    def apply_settings_after_save(self) -> None:
        s = self.settings_manager.settings
        self.canvas.apply_max_width(s.editor_document_max_width_px)
        self.canvas.editor.set_slash_menu_enabled(s.enable_slash_menu)
        self.canvas.editor.setLineWrapMode(
            self.canvas.editor.WidgetWidth if s.wrap_lines else self.canvas.editor.NoWrap
        )
        self._apply_preview_placement()
        self._drawer_visible = not s.default_metadata_collapsed
        self.drawer.setVisible(self._drawer_visible)
        self.btn_drawer.setText("Hide panel" if self._drawer_visible else "Show panel")

    def _toggle_drawer_visible(self) -> None:
        self._drawer_visible = not self._drawer_visible
        self.drawer.setVisible(self._drawer_visible)
        self.btn_drawer.setText("Hide panel" if self._drawer_visible else "Show panel")

    def _toggle_preview(self, checked: bool) -> None:
        mode = self.settings_manager.settings.default_preview_mode
        if mode == "hidden":
            self.bottom.setVisible(checked)
            if checked:
                self._update_preview()
            return
        self.bottom.setVisible(checked)
        if checked:
            self._update_preview()

    def _toggle_metadata_drawer(self, checked: bool) -> None:
        self.drawer.setVisible(checked)
        self._drawer_visible = checked

    def _toggle_inspector_tab(self, checked: bool) -> None:
        self.inspector.setVisible(checked)
        if checked:
            self.bottom.setVisible(True)
            self.bottom_tabs.setCurrentWidget(self.inspector)

    def _on_preset_changed(self, text: str) -> None:
        self.canvas.set_preset_label(text)
        self.canvas.apply_entry_type_ui(text)
        self.preset_panel.apply_entry_type(text)
        if text.lower() == "photo":
            self._drawer_visible = True
            self.drawer.setVisible(True)
            self.btn_drawer.setText("Hide panel")
        self._trigger_autosave()

    def _open_slash_menu(self) -> None:
        c = self.canvas.editor.textCursor()
        rect = self.canvas.editor.cursorRect(c)
        pos = self.canvas.editor.mapToGlobal(rect.bottomLeft())
        self._slash_popup.show_at(pos, self.canvas.editor)

    def _schedule_float(self) -> None:
        if not self.settings_manager.settings.show_floating_toolbar:
            self._floating.hide()
            return
        self._float_timer.start(120)

    def _reposition_float(self) -> None:
        if not self.settings_manager.settings.show_floating_toolbar:
            return
        c = self.canvas.editor.textCursor()
        if c.hasSelection() and c.selectedText().strip():
            self._floating.reposition()
        else:
            self._floating.hide()

    def _insert_image_ref_at_cursor(self, aid: str) -> None:
        url = attachment_url(aid)
        self.canvas.editor.textCursor().insertHtml(f'<p><img src="{url}" alt="" /></p>')
        self.media_panel.mark_embedded(aid, True)
        self._trigger_autosave()

    def _on_image_attached(self, aid: str, dest: str) -> None:
        import mimetypes

        mime, _ = mimetypes.guess_type(dest)
        self.media_panel.register_attachment(
            {
                "id": aid,
                "local_path": dest,
                "mime_type": mime or "image/png",
                "alt_text": "",
                "uploaded_url": None,
                "upload_state": "pending",
                "embedded_in_document": True,
            }
        )

    def set_account(self, account) -> None:
        self.account = account
        self.media_panel.set_account(account)
        self.remote_panel.set_account(account)
        self.current_draft = Draft(account_id=account.id, content_mode=DEFAULT_EDITOR_MODE)
        self.compose_header.set_account_line(
            f"{account.display_name} — {account.me_url}"
        )
        self._load_draft_into_ui()

    def load_draft(self, draft: Draft) -> None:
        self.current_draft = draft
        self._load_draft_into_ui()

    def _trigger_autosave(self) -> None:
        self.canvas.set_status("Unsaved…")
        self.compose_header.set_status_line("Unsaved changes")
        self.current_draft.is_dirty = True
        self.autosave_timer.start(self.settings_manager.settings.autosave_interval_ms)
        self._update_preview()

    def _update_preview(self) -> None:
        html = self.canvas.editor.toHtml()
        self.preview_browser.setHtml(sanitize_html(html))

    def _sync_ui_to_draft(self) -> None:
        att_json = self.media_panel.get_attachments_json()
        self.current_draft = sync_draft_body_from_editor(
            self.current_draft,
            self.canvas.title_edit.text() or None,
            self.canvas.summary_edit.toPlainText().strip() or None,
            self.canvas.editor.toHtml(),
            self.compose_header.type_combo.currentText(),
            self.preset_panel.reply_in.text() or None,
            self.preset_panel.like_in.text() or None,
            self.preset_panel.repost_in.text() or None,
            self.preset_panel.bookmark_in.text() or None,
            att_json,
        )

    def _load_draft_into_ui(self) -> None:
        d = self.current_draft
        d.content_mode = normalize_editor_mode(d.content_mode)
        self.canvas.title_edit.setText(d.title or "")
        self.canvas.summary_edit.setPlainText(d.summary or "")
        self.compose_header.type_combo.blockSignals(True)
        self.compose_header.type_combo.setCurrentText(d.entry_type or "note")
        self.compose_header.type_combo.blockSignals(False)
        self.compose_header.set_content_mode_label(d.content_mode or "rich_text")
        self.canvas.set_preset_label(self.compose_header.type_combo.currentText())
        self.canvas.apply_entry_type_ui(self.compose_header.type_combo.currentText())
        self.preset_panel.apply_entry_type(self.compose_header.type_combo.currentText())

        self.preset_panel.reply_in.setText(d.in_reply_to or "")
        self.preset_panel.like_in.setText(d.like_of or "")
        self.preset_panel.repost_in.setText(d.repost_of or "")
        self.preset_panel.bookmark_in.setText(d.bookmark_of or "")

        mode = normalize_editor_mode(d.content_mode)
        self.canvas.editor.blockSignals(True)
        if mode == "markdown":
            html = self.conversion_manager.markdown_to_html(d.content_markdown_source or "")
            self.canvas.editor.setHtml(html)
        elif mode in ("rich_text", "html"):
            body = d.rich_text_html_snapshot or d.content_html or ""
            self.canvas.editor.setHtml(body)
        else:
            self.canvas.editor.setPlainText(d.content_plain or "")
        self.canvas.editor.blockSignals(False)

        self.media_panel.load_from_json(d.attachments_json)
        self._update_preview()
        self.canvas.set_status("Ready")
        self.compose_header.set_status_line("Ready")

    def _autosave(self) -> None:
        if not self.account:
            return
        self._sync_ui_to_draft()
        now = datetime.now()
        if self.current_draft.created_at is None:
            self.current_draft.created_at = now
        self.current_draft.modified_at = now
        self.current_draft.last_autosave_at = datetime.now()
        draft_id = self.post_service.save_draft(self.current_draft)
        self.current_draft.id = draft_id
        ts = datetime.now().strftime("%H:%M:%S")
        self.canvas.set_status(f"Saved {ts}")
        self.compose_header.set_status_line(f"Saved at {ts}")
        self.current_draft.is_dirty = False

    def save_draft_manual(self) -> None:
        if not self.account:
            QMessageBox.warning(self, "No account", "Select an account first.")
            return
        self._autosave()
        QMessageBox.information(self, "Saved", "Draft saved locally.")

    def _upload_pending_media(self) -> None:
        raw = self.media_panel.get_attachments_json()
        items = json.loads(raw) if raw else []
        if not items or not self.account:
            return
        if not self.account.media_endpoint:
            return
        changed = False
        for att in items:
            if att.get("upload_state") == "uploaded" and att.get("uploaded_url"):
                continue
            lp = att.get("local_path")
            if not lp or not os.path.isfile(lp):
                continue
            try:
                mime = att.get("mime_type") or "application/octet-stream"
                url = self.post_service.upload_attachment(self.account, lp, mime)
                att["uploaded_url"] = url
                att["upload_state"] = "uploaded"
                changed = True
            except Exception as e:
                att["upload_state"] = "failed"
                att["upload_error"] = str(e)
                changed = True
        if changed:
            self.media_panel.load_from_json(json.dumps(items))
            self._sync_ui_to_draft()

    def _on_remote_loaded(self, url: str, props: dict) -> None:
        self.current_draft = Draft(account_id=self.account.id, remote_post_url=url)
        content = props.get("content", [""])[0]
        if isinstance(content, dict) and "html" in content:
            self.current_draft.content_mode = "html"
            self.current_draft.content_html = content["html"]
            self.current_draft.rich_text_html_snapshot = content["html"]
        else:
            self.current_draft.content_mode = "plain"
            self.current_draft.content_plain = str(content)
        nm = props.get("name", [None])
        self.current_draft.title = nm[0] if nm else None
        self._load_draft_into_ui()
        QMessageBox.information(self, "Remote", f"Remote post loaded into the editor.\n\n{url}")

    def publish(self) -> None:
        if not self.account:
            return
        self._autosave()
        if self.settings_manager.settings.auto_upload_media and json.loads(
            self.media_panel.get_attachments_json() or "[]"
        ):
            try:
                self.post_service.fetch_capabilities(self.account)
            except Exception as e:
                QMessageBox.warning(self, "Micropub", f"Could not refresh capabilities: {e}")
        try:
            if self.settings_manager.settings.auto_upload_media:
                self._upload_pending_media()
        except Exception as e:
            QMessageBox.warning(self, "Upload", str(e))

        self._sync_ui_to_draft()
        warn = self.settings_manager.settings.warn_missing_alt_text
        if warn:
            for att in json.loads(self.current_draft.attachments_json or "[]"):
                if att.get("mime_type", "").startswith("image") and not (att.get("alt_text") or "").strip():
                    r = QMessageBox.question(
                        self,
                        "Alt text",
                        "Some images still need alt text. Publish anyway this time?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if r != QMessageBox.StandardButton.Yes:
                        return
                    break

        from pypub.ui.publish_dialog import PublishConfirmationDialog

        if self.settings_manager.settings.confirm_before_publish:
            dlg = PublishConfirmationDialog(self.account.me_url, self.current_draft, self)
            if not dlg.exec():
                return
        try:
            to_send = prepare_draft_for_publish(self.current_draft)
            url = self.post_service.publish_draft(self.account, to_send)
            QMessageBox.information(self, "Published", f"Your post is live now:\n{url}")
            self.current_draft = Draft(account_id=self.account.id, content_mode=DEFAULT_EDITOR_MODE)
            self._load_draft_into_ui()
        except Exception as e:
            QMessageBox.critical(self, "Publish error", f"PyPub couldn't publish yet: {e}")

    def log_inspector(self, msg: str) -> None:
        self.inspector.append(msg)
