"""Soft formatting toolbar with grouped writing controls."""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from pypub.ui.editor.document_editor import DocumentEditor


class FormatToolbar(QWidget):
    def __init__(
        self,
        editor: DocumentEditor,
        on_toggle_preview: Callable[[bool], None],
        on_toggle_metadata: Callable[[bool], None],
        on_toggle_inspector: Callable[[bool], None],
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("FormatToolbar")
        self._editor = editor
        self._preview_checked = False
        self._meta_checked = False
        self._insp_checked = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(10)

        def add_sep():
            s = QFrame()
            s.setFrameShape(QFrame.Shape.VLine)
            s.setFrameShadow(QFrame.Shadow.Sunken)
            s.setFixedWidth(1)
            lay.addWidget(s)

        def add_group_label(text: str):
            lbl = QLabel(text)
            lbl.setObjectName("ToolbarGroupLabel")
            lay.addWidget(lbl)

        def tb(text: str, slot, tip: str = ""):
            button = QToolButton()
            button.setObjectName("FormatChip")
            button.setText(text)
            if tip:
                button.setToolTip(tip)
            button.setAutoRaise(True)
            button.clicked.connect(slot)
            lay.addWidget(button)
            return button

        add_group_label("Polish")
        tb("Undo", editor.undo, "Undo (Ctrl+Z)")
        tb("Redo", editor.redo, "Redo (Ctrl+Y)")
        add_sep()

        add_group_label("Text")
        tb("Bold", editor.toggle_bold, "Bold (Ctrl+B)")
        tb("Italic", editor.toggle_italic, "Italic (Ctrl+I)")
        tb("Underline", editor.toggle_underline, "Underline")
        tb("Strike", editor.toggle_strike, "Strikethrough")
        add_sep()

        add_group_label("Structure")
        tb("Paragraph", editor.set_paragraph, "Paragraph")
        tb("H1", lambda: editor.set_heading(1), "Heading 1")
        tb("H2", lambda: editor.set_heading(2), "Heading 2")
        tb("List", editor.toggle_bullet_list, "Bullet list")
        tb("Quote", editor.apply_blockquote, "Blockquote")
        tb("Code", editor.insert_code_block, "Code block")
        tb("Link", editor.insert_or_edit_link, "Link")
        tb("Image", editor.insert_image_interactive, "Image")
        add_sep()

        add_group_label("Views")
        self._btn_preview = tb(
            "Preview",
            lambda: self._flip_toggle("preview", on_toggle_preview),
            "Toggle reading preview",
        )
        self._btn_meta = tb(
            "Side panel",
            lambda: self._flip_toggle("meta", on_toggle_metadata),
            "Toggle media and remote panel",
        )
        self._btn_insp = tb(
            "Inspector",
            lambda: self._flip_toggle("insp", on_toggle_inspector),
            "Toggle technical inspector",
        )

        stretch = QWidget()
        stretch.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lay.addWidget(stretch)

    def set_toggle_memory(self, preview: bool, metadata_drawer: bool, inspector: bool) -> None:
        self._preview_checked = preview
        self._meta_checked = metadata_drawer
        self._insp_checked = inspector

    def _flip_toggle(self, which: str, cb: Callable[[bool], None]):
        if which == "preview":
            self._preview_checked = not self._preview_checked
            cb(self._preview_checked)
        elif which == "meta":
            self._meta_checked = not self._meta_checked
            cb(self._meta_checked)
        else:
            self._insp_checked = not self._insp_checked
            cb(self._insp_checked)
