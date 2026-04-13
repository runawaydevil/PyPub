"""Document column: faixa branca tipo página — largura até A4 (config) e altura da viewport."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pypub.domain.settings import AppSettings
from pypub.ui.editor.document_editor import DocumentEditor

# Largura mínima útil quando a janela é estreita
_MIN_STRIP_PX = 360


class DocumentCanvas(QWidget):
    def __init__(self, media_cache_dir: str, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._max_w = settings.editor_document_max_width_px
        self._settings = settings

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._inner = QWidget()
        self._inner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        row = QHBoxLayout(self._inner)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addStretch(1)

        self.card = QFrame()
        self.card.setObjectName("DocumentCard")
        self.card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(32, 28, 40, 40)
        card_lay.setSpacing(14)

        self.title_edit = QLineEdit()
        self.title_edit.setObjectName("DocTitle")
        self.title_edit.setPlaceholderText("Title")
        card_lay.addWidget(self.title_edit)

        self.summary_edit = QPlainTextEdit()
        self.summary_edit.setObjectName("DocSummary")
        self.summary_edit.setPlaceholderText("Excerpt / summary (optional)")
        self.summary_edit.setFixedHeight(92)
        self.summary_edit.setTabChangesFocus(True)
        self.summary_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        card_lay.addWidget(self.summary_edit)

        top_meta = QHBoxLayout()
        self.preset_chip = QLabel("note")
        self.preset_chip.setObjectName("PresetChip")
        self.status_lbl = QLabel("Ready")
        self.status_lbl.setObjectName("ContextStatus")
        top_meta.addWidget(self.preset_chip)
        top_meta.addStretch()
        top_meta.addWidget(self.status_lbl)
        card_lay.addLayout(top_meta)

        self.editor = DocumentEditor(
            media_cache_dir,
            enable_slash=settings.enable_slash_menu,
            parent=self.card,
        )
        card_lay.addWidget(self.editor, 1)

        # Sem AlignTop: o cartão preenche a altura da viewport (área de escrita grande).
        row.addWidget(self.card)
        row.addStretch(1)

        self._scroll.setWidget(self._inner)
        outer.addWidget(self._scroll, 1)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._sync_strip_geometry()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._sync_strip_geometry()

    def _sync_strip_geometry(self) -> None:
        """Largura da faixa = min(teto editorial, viewport); corpo usa o resto da altura."""
        vw = self._scroll.viewport().width()
        avail = max(_MIN_STRIP_PX, vw)
        w = min(self._max_w, avail)
        self.card.setFixedWidth(w)

        vh = self._scroll.viewport().height()
        reserved = 200
        self.editor.setMinimumHeight(max(320, vh - reserved))

    def apply_max_width(self, px: int) -> None:
        self._max_w = max(_MIN_STRIP_PX, px)
        self._sync_strip_geometry()

    def set_preset_label(self, text: str) -> None:
        self.preset_chip.setText(text)

    def set_status(self, text: str) -> None:
        self.status_lbl.setText(text)

    def apply_entry_type_ui(self, entry_type: str) -> None:
        """Title / excerpt / chip hierarchy by Micropub preset."""
        t = (entry_type or "note").lower()
        is_article = False
        if t == "note":
            self.title_edit.setVisible(False)
            self.summary_edit.setVisible(False)
            self.title_edit.setPlaceholderText("Title")
        elif t == "article":
            self.title_edit.setVisible(True)
            self.summary_edit.setVisible(True)
            self.title_edit.setPlaceholderText("Article title")
            self.summary_edit.setPlaceholderText("Excerpt or dek (optional)")
            is_article = True
        elif t in ("like", "repost"):
            self.title_edit.setVisible(False)
            self.summary_edit.setVisible(False)
        elif t == "bookmark":
            self.title_edit.setVisible(True)
            self.summary_edit.setVisible(True)
            self.title_edit.setPlaceholderText("Title (optional)")
            self.summary_edit.setPlaceholderText("Note or description (optional)")
        elif t == "photo":
            self.title_edit.setVisible(True)
            self.summary_edit.setVisible(True)
            self.title_edit.setPlaceholderText("Title (optional)")
            self.summary_edit.setPlaceholderText("Caption (optional)")
        else:
            self.title_edit.setVisible(True)
            self.summary_edit.setVisible(True)
            self.title_edit.setPlaceholderText("Title")
            self.summary_edit.setPlaceholderText("Subtitle or summary (optional)")
        self.title_edit.setProperty("articleTitle", is_article)
        self.title_edit.style().unpolish(self.title_edit)
        self.title_edit.style().polish(self.title_edit)
        self.summary_edit.style().unpolish(self.summary_edit)
        self.summary_edit.style().polish(self.summary_edit)
