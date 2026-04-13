from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QCheckBox, QPushButton, QHBoxLayout, QMessageBox
from pypub.domain.models import Draft

class PublishConfirmationDialog(QDialog):
    def __init__(self, account_url: str, draft: Draft, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review Publish Action")
        self.resize(350, 400)
        self.draft = draft
        self.account_url = account_url

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Target:</b> {self.account_url}"))
        layout.addWidget(QLabel(f"<b>Mode:</b> {draft.content_mode}"))
        layout.addWidget(QLabel(f"<b>Type:</b> {draft.entry_type}"))
        layout.addWidget(QLabel(f"<b>Visibility:</b> {draft.visibility or 'default'}"))

        # Checagens inteligentes
        has_media = len(draft.attachments_json) > 4 # Minimal check if list is not "[]"
        if has_media:
            lbl_media = QLabel("⚠️ Images found. Are alt-texts provided?")
            lbl_media.setStyleSheet("color: #d35400;")
            layout.addWidget(lbl_media)

        if draft.content_mode == "rich_text":
            lbl_rich = QLabel("ℹ️ Rich Text will be published as HTML.")
            layout.addWidget(lbl_rich)

        layout.addStretch()

        self.chk_confirm = QCheckBox("I understand. Proceed with publishing.")
        layout.addWidget(self.chk_confirm)

        h_btns = QHBoxLayout()
        self.btn_publish = QPushButton("Publish Now")
        self.btn_publish.setEnabled(False)
        self.btn_publish.setStyleSheet("background-color: #2e8b57; color: white;")
        self.btn_cancel = QPushButton("Cancel")
        
        self.chk_confirm.stateChanged.connect(self._toggle_btn)
        self.btn_publish.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        h_btns.addWidget(self.btn_cancel)
        h_btns.addWidget(self.btn_publish)
        layout.addLayout(h_btns)

    def _toggle_btn(self, state):
        self.btn_publish.setEnabled(self.chk_confirm.isChecked())
