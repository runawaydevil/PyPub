import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
                               QTabWidget, QComboBox, QLineEdit, QPushButton,
                               QTextBrowser, QLabel, QMessageBox)
from PySide6.QtCore import Qt, QTimer

from pypub.domain.models import Draft
from pypub.ui.editor_core import RichTextEditor
from pypub.ui.media_panel import MediaPanel
from pypub.ui.remote_edit import RemoteEditPanel
from pypub.application.sanitization import sanitize_html
from pypub.application.conversion import ConversionManager

class EditorWorkspace(QWidget):
    def __init__(self, post_service, app_data_dir, settings_manager):
        super().__init__()
        self.post_service = post_service
        self.app_data_dir = app_data_dir
        self.settings_manager = settings_manager
        
        # Injete settings manager in post service just in case
        self.post_service.settings_manager = self.settings_manager
        
        self.account = None
        self.current_draft = Draft(account_id=-1)
        self.conversion_manager = ConversionManager()
        
        # Debounce Timer for Auto-Save and Preview
        self.autosave_timer = QTimer()
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self._autosave)

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # Header Toolbar
        header_layout = QHBoxLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["note", "article", "photo", "reply", "like", "repost", "bookmark"])
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["rich_text", "markdown", "html", "plain"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)

        self.btn_save = QPushButton("Save Draft")
        self.btn_save.clicked.connect(self.save_draft_manual)

        self.btn_publish = QPushButton("Publish")
        self.btn_publish.clicked.connect(self.publish)
        self.btn_publish.setStyleSheet("background-color: #2e8b57; color: white;")

        self.lbl_status = QLabel("Ready")

        header_layout.addWidget(QLabel("Preset:"))
        header_layout.addWidget(self.type_combo)
        header_layout.addWidget(QLabel("Mode:"))
        header_layout.addWidget(self.mode_combo)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_status)
        header_layout.addWidget(self.btn_save)
        header_layout.addWidget(self.btn_publish)

        main_layout.addLayout(header_layout)

        # Splitter and Tabs
        splitter = QSplitter(Qt.Horizontal)

        # Left Side (Content)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Title (optional)")
        left_layout.addWidget(self.title_input)

        # Core Editor
        self.editor = RichTextEditor(media_cache_dir=os.path.join(self.app_data_dir, "media_cache"))
        self.editor.textChanged.connect(self._trigger_autosave)
        left_layout.addWidget(self.editor)

        splitter.addWidget(left_widget)

        # Right Side (Tabs)
        self.right_tabs = QTabWidget()
        
        # Metadata Tab
        meta_widget = QWidget()
        meta_layout = QVBoxLayout(meta_widget)
        self.reply_in = QLineEdit()
        self.reply_in.setPlaceholderText("In-Reply-To URL")
        meta_layout.addWidget(QLabel("Reply Target:"))
        meta_layout.addWidget(self.reply_in)
        meta_layout.addStretch()
        self.right_tabs.addTab(meta_widget, "Metadata")

        # Media Tab
        self.media_panel = MediaPanel(self.post_service, os.path.join(self.app_data_dir, "media_cache"))
        self.right_tabs.addTab(self.media_panel, "Media")

        # Remote Tab
        self.remote_panel = RemoteEditPanel(self.post_service, self._on_remote_loaded)
        self.right_tabs.addTab(self.remote_panel, "Remote")

        # Preview Tab
        self.preview_browser = QTextBrowser()
        self.right_tabs.addTab(self.preview_browser, "Preview")

        splitter.addWidget(self.right_tabs)
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter)

    def set_account(self, account):
        self.account = account
        self.media_panel.account = account
        self.remote_panel.account = account
        self.current_draft = Draft(account_id=account.id)
        self._load_draft_into_ui()
    
    def _trigger_autosave(self):
        self.lbl_status.setText("Unsaved changes...")
        self.current_draft.is_dirty = True
        self.autosave_timer.start(2000) # 2 seconds debounce
        self._update_preview()

    def _update_preview(self):
        # Update preview securely
        mode = self.mode_combo.currentText()
        content = self.editor.toPlainText()
        if mode == "rich_text":
            html = self.editor.toHtml()
            # nh3 sanitization
            safe_html = sanitize_html(html)
            self.preview_browser.setHtml(safe_html)
        elif mode == "markdown":
            raw_html = self.conversion_manager.markdown_to_html(content)
            self.preview_browser.setHtml(sanitize_html(raw_html))
        else:
            self.preview_browser.setHtml(sanitize_html(content))

    def _on_mode_changed(self, new_mode: str):
        old_mode = self.current_draft.content_mode
        if old_mode == new_mode:
            return
            
        warn, msg = self.conversion_manager.validate_conversion(old_mode, new_mode)
        if warn:
            reply = QMessageBox.question(self, "Conversion Warning", msg, QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                self.mode_combo.setCurrentText(old_mode)
                return
        
        # Proceed with conversion logic depending on states (mocked for flow):
        if old_mode == "rich_text" and new_mode == "markdown":
            # Very lossy, standard QTextEdit toHtml is terrible for direct markdown conversion
            pass
        
        self.current_draft.content_mode = new_mode
        self._trigger_autosave()

    def _sync_ui_to_draft(self):
        self.current_draft.title = self.title_input.text() or None
        mode = self.mode_combo.currentText()
        self.current_draft.content_mode = mode
        
        if mode == "rich_text":
            self.current_draft.content_html = self.editor.toHtml()
            self.current_draft.rich_text_html_snapshot = self.editor.toHtml()
        elif mode == "markdown":
            self.current_draft.content_markdown_source = self.editor.toPlainText()
        elif mode == "html":
            self.current_draft.content_html = self.editor.toPlainText()
        else:
            self.current_draft.content_plain = self.editor.toPlainText()
            
        self.current_draft.in_reply_to = self.reply_in.text() or None
        self.current_draft.entry_type = self.type_combo.currentText()

    def _load_draft_into_ui(self):
        self.title_input.setText(self.current_draft.title or "")
        mode = self.current_draft.content_mode
        self.mode_combo.setCurrentText(mode)
        
        # Blocks signal to prevent autosave trigger on load
        self.editor.blockSignals(True)
        if mode == "rich_text":
            self.editor.setHtml(self.current_draft.rich_text_html_snapshot or "")
        elif mode == "markdown":
            self.editor.setPlainText(self.current_draft.content_markdown_source or "")
        elif mode == "html":
            self.editor.setPlainText(self.current_draft.content_html or "")
        else:
            self.editor.setPlainText(self.current_draft.content_plain or "")
        self.editor.blockSignals(False)

        self.reply_in.setText(self.current_draft.in_reply_to or "")
        self.type_combo.setCurrentText(self.current_draft.entry_type)
        self._update_preview()

    def _autosave(self):
        if not self.account:
            return
        self._sync_ui_to_draft()
        from datetime import datetime
        self.current_draft.last_autosave_at = datetime.now()
        
        draft_id = self.post_service.save_draft(self.current_draft)
        self.current_draft.id = draft_id
        self.lbl_status.setText(f"Autosaved at {datetime.now().strftime('%H:%M:%S')}")
        self.current_draft.is_dirty = False

    def save_draft_manual(self):
        self._autosave()
        QMessageBox.information(self, "Saved", "Draft saved manually.")

    def _on_remote_loaded(self, url: str, props: dict):
        self.current_draft = Draft(account_id=self.account.id, remote_post_url=url)
        content = props.get("content", [""])[0]
        if isinstance(content, dict) and "html" in content:
            self.current_draft.content_mode = "html"
            self.current_draft.content_html = content["html"]
        else:
            self.current_draft.content_mode = "plain"
            self.current_draft.content_plain = content

        self.current_draft.title = props.get("name", [None])[0]
        self._load_draft_into_ui()
        QMessageBox.information(self, "Remote", f"Loaded remote post from {url}")

    def publish(self):
        if not self.account:
            return
        self.save_draft_manual() # Ensure updated
        
        # Phase 3: Pre-publish Checklist Check
        from pypub.ui.publish_dialog import PublishConfirmationDialog
        if self.post_service.settings_manager.settings.confirm_before_publish:
            dialog = PublishConfirmationDialog(self.account.me_url, self.current_draft, self)
            if not dialog.exec():
                return
                
        # Fallback to PostService
        try:
            url = self.post_service.publish_draft(self.account, self.current_draft)
            QMessageBox.information(self, "Published", f"Published at: {url}")
            # Reset
            self.current_draft = Draft(account_id=self.account.id)
            self._load_draft_into_ui()
        except Exception as e:
            QMessageBox.critical(self, "Publish Error", str(e))
