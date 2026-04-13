"""Floating mini-toolbar near text selection (Medium-style)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QHBoxLayout, QToolButton, QWidget

from pypub.ui.editor.document_editor import DocumentEditor


class FloatingFormatBar(QWidget):
    def __init__(self, editor: DocumentEditor, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._editor = editor
        self.setObjectName("FloatingFormatBar")
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(2)

        def btn(text: str, slot, tip: str):
            b = QToolButton()
            b.setObjectName("FloatingFormatButton")
            b.setText(text)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            row.addWidget(b)

        btn("B", editor.toggle_bold, "Bold (Ctrl+B)")
        btn("I", editor.toggle_italic, "Italic (Ctrl+I)")
        btn("Link", editor.insert_or_edit_link, "Insert or edit link")
        btn("Quote", editor.apply_blockquote, "Quote")
        btn("Code", editor.apply_inline_code, "Inline code")
        btn("H2", lambda: editor.set_heading(2), "Heading 2")
        btn("H3", lambda: editor.set_heading(3), "Heading 3")
        btn("Clear", editor.clear_char_formatting, "Clear character formatting")

    def reposition(self):
        c = self._editor.textCursor()
        if not c.hasSelection():
            self.hide()
            return
        rect = self._editor.cursorRect(c)
        top_left = self._editor.mapToGlobal(rect.bottomLeft())
        self.adjustSize()
        pos = QPoint(top_left.x(), top_left.y() + 6)
        self.move(pos)
        self.show()
        self.raise_()
