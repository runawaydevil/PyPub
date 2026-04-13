"""Preset-specific context blocks in the main compose column (URLs, hints)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class PresetContextPanel(QWidget):
    """Hosts in-reply-to, like-of, etc. Visibility only — never clears editor HTML."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PresetContextPanel")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 8)
        root.setSpacing(8)

        self.reply_block, self.reply_in = self._url_block("Respondendo a")
        self.reply_hint = QLabel(
            "Cole a URL do post alvo. (Pré-visualização do alvo pode vir numa versão futura.)"
        )
        self.reply_hint.setWordWrap(True)
        self.reply_hint.setObjectName("PresetHint")
        self.reply_block.layout().addWidget(self.reply_hint)
        root.addWidget(self.reply_block)

        self.like_block, self.like_in = self._url_block("Like of (URL)")
        self.like_hint = QLabel("Conteúdo opcional no corpo abaixo.")
        self.like_hint.setWordWrap(True)
        self.like_hint.setObjectName("PresetHint")
        self.like_block.layout().addWidget(self.like_hint)
        root.addWidget(self.like_block)

        self.repost_block, self.repost_in = self._url_block("Repost of (URL)")
        self.repost_hint = QLabel("Opcional: nota ou comentário no corpo.")
        self.repost_hint.setWordWrap(True)
        self.repost_hint.setObjectName("PresetHint")
        self.repost_block.layout().addWidget(self.repost_hint)
        root.addWidget(self.repost_block)

        self.bookmark_block, self.bookmark_in = self._url_block("Bookmark of (URL)")
        self.bookmark_hint = QLabel("Título e resumo opcionais aparecem acima do corpo quando visíveis.")
        self.bookmark_hint.setWordWrap(True)
        self.bookmark_hint.setObjectName("PresetHint")
        self.bookmark_block.layout().addWidget(self.bookmark_hint)
        root.addWidget(self.bookmark_block)

        self.photo_strip = QFrame()
        self.photo_strip.setObjectName("PhotoPresetStrip")
        ps = QHBoxLayout(self.photo_strip)
        ps.setContentsMargins(8, 8, 8, 8)
        self.photo_lbl = QLabel(
            "<b>Foto</b> — use o painel <b>Media</b> à direita para anexar, ordem e texto alternativo. "
            "Insira imagens no corpo pela toolbar ou arrastando para o editor."
        )
        self.photo_lbl.setWordWrap(True)
        self.photo_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        ps.addWidget(self.photo_lbl)
        root.addWidget(self.photo_strip)

        root.addStretch(0)

    def _url_block(self, title: str) -> tuple[QFrame, QLineEdit]:
        fr = QFrame()
        fr.setObjectName("PresetUrlBlock")
        lay = QVBoxLayout(fr)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.addWidget(QLabel(f"<b>{title}</b>"))
        ed = QLineEdit()
        ed.setPlaceholderText("https://…")
        lay.addWidget(ed)
        return fr, ed

    def apply_entry_type(self, entry_type: str) -> None:
        t = (entry_type or "note").lower()
        self.reply_block.setVisible(t == "reply")
        self.like_block.setVisible(t == "like")
        self.repost_block.setVisible(t == "repost")
        self.bookmark_block.setVisible(t == "bookmark")
        self.photo_strip.setVisible(t == "photo")
