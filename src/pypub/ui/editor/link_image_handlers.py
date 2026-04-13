"""Simple dialogs for link and image alt text."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox


class LinkEditDialog(QDialog):
    def __init__(self, current_url: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Link")
        self._url = current_url
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.url_edit = QLineEdit(current_url)
        self.url_edit.setPlaceholderText("https://")
        form.addRow("URL:", self.url_edit)
        layout.addLayout(form)
        row = QHBoxLayout()
        ok = QPushButton("OK")
        ok.clicked.connect(self._ok)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        row.addWidget(ok)
        layout.addLayout(row)

    def _ok(self):
        u = self.url_edit.text().strip()
        if not u:
            QMessageBox.warning(self, "Link", "URL cannot be empty.")
            return
        self._url = u
        self.accept()

    def url(self) -> str:
        return self._url


class AltTextDialog(QDialog):
    def __init__(self, current_alt: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image description")
        self._alt = current_alt
        layout = QVBoxLayout(self)
        self.alt_edit = QLineEdit(current_alt)
        self.alt_edit.setPlaceholderText("Describe the image for accessibility")
        layout.addWidget(self.alt_edit)
        row = QHBoxLayout()
        ok = QPushButton("OK")
        ok.clicked.connect(self._ok)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        row.addWidget(ok)
        layout.addLayout(row)

    def _ok(self):
        self._alt = self.alt_edit.text().strip()
        self.accept()

    def alt_text(self) -> str:
        return self._alt
