"""Compose header with identity, status and primary actions."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ComposeHeader(QWidget):
    ENTRY_TYPES = ("note", "article", "photo", "reply", "like", "repost", "bookmark")

    def __init__(
        self,
        on_save: Callable[[], None],
        on_publish: Callable[[], None],
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("ComposeHeader")
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(3)
        self.kicker_lbl = QLabel("Compose")
        self.kicker_lbl.setObjectName("ComposeKicker")
        left.addWidget(self.kicker_lbl)

        self.account_lbl = QLabel("Select an account to begin")
        self.account_lbl.setObjectName("ComposeHeaderAccount")
        self.account_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        left.addWidget(self.account_lbl)

        self.hint_lbl = QLabel("Autosave keeps local changes up to date while you work.")
        self.hint_lbl.setObjectName("ComposeHeaderHint")
        self.hint_lbl.setWordWrap(True)
        left.addWidget(self.hint_lbl)
        root.addLayout(left, 1)

        center = QFrame()
        center.setObjectName("PageCard")
        center_layout = QHBoxLayout(center)
        center_layout.setContentsMargins(14, 10, 14, 10)
        center_layout.setSpacing(12)
        center_layout.addWidget(QLabel("Post type"), 0, Qt.AlignmentFlag.AlignVCenter)
        self.type_combo = QComboBox()
        self.type_combo.addItems(list(self.ENTRY_TYPES))
        center_layout.addWidget(self.type_combo)

        self.mode_lbl = QLabel("rich_text")
        self.mode_lbl.setObjectName("ComposeHeaderMode")
        center_layout.addWidget(self.mode_lbl)

        self.status_lbl = QLabel("Ready")
        self.status_lbl.setObjectName("ComposeHeaderStatus")
        center_layout.addWidget(self.status_lbl)
        root.addWidget(center)

        actions = QVBoxLayout()
        actions.setSpacing(8)
        self.btn_save = QPushButton("Save draft")
        self.btn_save.clicked.connect(on_save)
        actions.addWidget(self.btn_save)

        self.btn_publish = QPushButton("Publish")
        self.btn_publish.setObjectName("ComposePublishButton")
        self.btn_publish.clicked.connect(on_publish)
        actions.addWidget(self.btn_publish)
        root.addLayout(actions)

    def set_account_line(self, text: str) -> None:
        self.account_lbl.setText(text)

    def set_content_mode_label(self, mode: str) -> None:
        readable = {
            "rich_text": "Rich text",
            "html": "HTML",
            "markdown": "Markdown",
            "plain": "Plain text",
        }
        self.mode_lbl.setText(readable.get(mode or "rich_text", mode or "Rich text"))

    def set_status_line(self, text: str) -> None:
        self.status_lbl.setText(text)
