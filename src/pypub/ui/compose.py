from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QComboBox, QPushButton, QMessageBox, QHBoxLayout
from pypub.domain.models import Draft

class ComposeWidget(QWidget):
    def __init__(self, post_service):
        super().__init__()
        self.post_service = post_service
        self.account = None
        self.current_draft_id = None

        layout = QVBoxLayout(self)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["note", "article", "photo", "reply", "like", "repost"])

        self.title_input = QLineEdit()
        self.content_input = QTextEdit()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["markdown", "html", "plain"])
        
        self.reply_in = QLineEdit()
        self.like_in = QLineEdit()
        self.repost_in = QLineEdit()

        form = QFormLayout()
        form.addRow("Type:", self.type_combo)
        form.addRow("Title:", self.title_input)
        form.addRow("In-Reply-To:", self.reply_in)
        form.addRow("Like-Of:", self.like_in)
        form.addRow("Repost-Of:", self.repost_in)
        form.addRow("Mode:", self.mode_combo)
        
        layout.addLayout(form)
        layout.addWidget(self.content_input)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Draft")
        btn_save.clicked.connect(self.save_draft)
        btn_publish = QPushButton("Publish")
        btn_publish.clicked.connect(self.publish)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_publish)
        
        layout.addLayout(btn_layout)

    def set_account(self, account):
        self.account = account
        self.current_draft_id = None

    def save_draft(self):
        if not self.account:
            return
        
        draft = Draft(
            id=self.current_draft_id,
            account_id=self.account.id,
            entry_type=self.type_combo.currentText(),
            title=self.title_input.text() or None,
            content_mode=self.mode_combo.currentText(),
            in_reply_to=self.reply_in.text() or None,
            like_of=self.like_in.text() or None,
            repost_of=self.repost_in.text() or None
        )

        if draft.content_mode == "markdown":
            draft.content_markdown_source = self.content_input.toPlainText()
        elif draft.content_mode == "html":
            draft.content_html = self.content_input.toPlainText()
        else:
            draft.content_plain = self.content_input.toPlainText()
        
        self.current_draft_id = self.post_service.save_draft(draft)
        QMessageBox.information(self, "Draft Saved", "Draft saved locally.")

    def publish(self):
        if not self.account:
            return
        self.save_draft()
        # Retrieve actual fresh draft from DB or just construct
        draft = Draft(
            id=self.current_draft_id,
            account_id=self.account.id,
            entry_type=self.type_combo.currentText(),
            title=self.title_input.text() or None,
            content_mode=self.mode_combo.currentText(),
            in_reply_to=self.reply_in.text() or None,
            like_of=self.like_in.text() or None,
            repost_of=self.repost_in.text() or None
        )
        if draft.content_mode == "markdown":
            draft.content_markdown_source = self.content_input.toPlainText()
        elif draft.content_mode == "html":
            draft.content_html = self.content_input.toPlainText()
        else:
            draft.content_plain = self.content_input.toPlainText()

        try:
            url = self.post_service.publish_draft(self.account, draft)
            QMessageBox.information(self, "Published", f"Published at {url}")
            # Reset
            self.title_input.clear()
            self.content_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Publish failed: {e}")
