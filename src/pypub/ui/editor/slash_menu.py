"""Slash command popup: filterable list, keyboard navigation."""

from __future__ import annotations

from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtWidgets import (
    QFrame,
    QLineEdit,
    QListView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QKeyEvent


class _FilterLine(QLineEdit):
    """Arrow keys move list selection instead of moving cursor in empty filter."""

    def __init__(self, list_view: QListView, parent=None):
        super().__init__(parent)
        self._list = list_view

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self._list.keyPressEvent(event)
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.parent()._activate_current()  # type: ignore[attr-defined]
            event.accept()
            return
        super().keyPressEvent(event)


class SlashMenuPopup(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("SlashMenu")
        self._editor = None
        self._commands: list[tuple[str, str, str]] = [
            ("Paragraph", "paragraph", "Normal paragraph"),
            ("Heading 1", "h1", "Large section title"),
            ("Heading 2", "h2", "Section title"),
            ("Heading 3", "h3", "Subsection"),
            ("Quote", "quote", "Blockquote"),
            ("Divider", "divider", "Horizontal rule"),
            ("Image", "image", "Insert image from file"),
            ("Code block", "codeblock", "Preformatted code"),
            ("Bullet list", "bullet", "Unordered list"),
            ("Numbered list", "numbered", "Ordered list"),
            ("Checklist item", "check", "Checkbox line"),
        ]
        lay = QVBoxLayout(self)
        self.list_view = QListView()
        self._model = QStringListModel()
        self.list_view.setModel(self._model)
        self.list_view.setMaximumHeight(280)
        self.filter_edit = _FilterLine(self.list_view, self)
        self.filter_edit.setPlaceholderText("Filter…")
        lay.addWidget(self.filter_edit)
        lay.addWidget(self.list_view)

        self.filter_edit.textChanged.connect(self._refilter)
        self.list_view.doubleClicked.connect(lambda _: self._activate_current())
        self._ids: list[str] = []
        self._refilter()

    def set_editor(self, editor):
        self._editor = editor

    def show_at(self, global_pos, editor):
        self.set_editor(editor)
        self.adjustSize()
        self.move(global_pos)
        self.show()
        self.filter_edit.clear()
        self._refilter()
        self.filter_edit.setFocus()
        if self._model.rowCount() > 0:
            self.list_view.setCurrentIndex(self._model.index(0, 0))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)

    def _refilter(self):
        q = self.filter_edit.text().lower()
        labels = [f"{t[0]} — {t[2]}" for t in self._commands if not q or q in t[0].lower() or q in t[1]]
        ids = [t[1] for t in self._commands if not q or q in t[0].lower() or q in t[1]]
        self._model.setStringList(labels)
        self._ids = ids

    def _activate_current(self):
        idx = self.list_view.currentIndex().row()
        if idx < 0 or idx >= len(getattr(self, "_ids", [])):
            self.close()
            return
        cmd = self._ids[idx]
        ed = self._editor
        if ed:
            self._run(ed, cmd)
        self.close()

    def _run(self, ed, cmd: str):
        if cmd == "paragraph":
            ed.set_paragraph()
        elif cmd == "h1":
            ed.set_heading(1)
        elif cmd == "h2":
            ed.set_heading(2)
        elif cmd == "h3":
            ed.set_heading(3)
        elif cmd == "quote":
            ed.apply_blockquote()
        elif cmd == "divider":
            ed.insert_horizontal_rule()
        elif cmd == "image":
            ed.insert_image_interactive()
        elif cmd == "codeblock":
            ed.insert_code_block()
        elif cmd == "bullet":
            ed.toggle_bullet_list()
        elif cmd == "numbered":
            ed.toggle_numbered_list()
        elif cmd == "check":
            ed.insert_checklist_item()
