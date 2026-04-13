import json

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QCheckBox, QPushButton, QHBoxLayout
from pypub.domain.models import Draft

class PublishConfirmationDialog(QDialog):
    def __init__(self, account_url: str, draft: Draft, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review before publishing")
        self.resize(350, 400)
        self.draft = draft
        self.account_url = account_url

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Target:</b> {self.account_url}"))
        layout.addWidget(QLabel(f"<b>Mode:</b> {draft.content_mode}"))
        layout.addWidget(QLabel(f"<b>Type:</b> {draft.entry_type}"))
        layout.addWidget(QLabel(f"<b>Visibility:</b> {draft.visibility or 'default'}"))

        # Checagens inteligentes
        has_media = bool(json.loads(draft.attachments_json or "[]"))
        if has_media:
            lbl_media = QLabel("Images are attached. Review alt text before publishing.")
            lbl_media.setObjectName("MediaWarning")
            layout.addWidget(lbl_media)

        if draft.content_mode == "rich_text":
            lbl_rich = QLabel("Rich text will be published as HTML.")
            layout.addWidget(lbl_rich)

        layout.addStretch()

        self.chk_confirm = QCheckBox("I reviewed this post and want to publish it.")
        layout.addWidget(self.chk_confirm)

        h_btns = QHBoxLayout()
        self.btn_publish = QPushButton("Publish now")
        self.btn_publish.setEnabled(False)
        self.btn_publish.setObjectName("PrimaryAction")
        self.btn_cancel = QPushButton("Cancel")
        
        self.chk_confirm.stateChanged.connect(self._toggle_btn)
        self.btn_publish.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        h_btns.addWidget(self.btn_cancel)
        h_btns.addWidget(self.btn_publish)
        layout.addLayout(h_btns)

    def _toggle_btn(self, state):
        self.btn_publish.setEnabled(self.chk_confirm.isChecked())
