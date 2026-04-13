"""
Rich document editor: QTextEdit with headings, lists, links, images, slash trigger.
"""

from __future__ import annotations

import html as html_module
import mimetypes
import os
import uuid
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer, QMimeData
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QImage,
    QTextCharFormat,
    QTextCursor,
    QTextBlockFormat,
    QTextListFormat,
    QKeySequence,
)
from PySide6.QtWidgets import QApplication, QTextEdit, QFileDialog, QMenu, QMessageBox, QDialog

from pypub.application.editor_sync import ATTACHMENT_PREFIX, attachment_url
from pypub.ui.editor.link_image_handlers import LinkEditDialog, AltTextDialog


class DocumentEditor(QTextEdit):
    """White-surface rich text editor with Medium-like editing affordances."""

    imageAttached = Signal(str, str)  # attachment_id, local_path
    slashMenuRequested = Signal()
    selectionChangedForToolbar = Signal()

    def __init__(self, media_cache_dir: str, enable_slash: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentEditor")
        self._media_cache = media_cache_dir
        os.makedirs(self._media_cache, exist_ok=True)
        self._enable_slash = enable_slash

        self.setAcceptRichText(True)
        self.setUndoRedoEnabled(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.document().setDefaultStyleSheet(
            """
            body { font-family: Georgia, 'Times New Roman', serif; line-height: 1.55; }
            h1 { font-size: 2em; font-weight: 600; margin-top: 0.6em; margin-bottom: 0.3em; }
            h2 { font-size: 1.5em; font-weight: 600; margin-top: 0.5em; }
            h3 { font-size: 1.2em; font-weight: 600; margin-top: 0.4em; }
            pre { background: #f4f4f4; padding: 10px; border-radius: 4px; font-family: Consolas, monospace; }
            blockquote { border-left: 4px solid #ccc; margin-left: 0; padding-left: 12px; color: #555; }
            hr { border: none; border-top: 1px solid #ddd; margin: 16px 0; }
            """
        )

        self.cursorPositionChanged.connect(self._on_cursor_moved)
        self.selectionChanged.connect(self.selectionChangedForToolbar.emit)

    def set_slash_menu_enabled(self, on: bool) -> None:
        self._enable_slash = bool(on)

    def _on_cursor_moved(self):
        self.selectionChangedForToolbar.emit()

    # --- Character formats ---
    def merge_char_fmt(self, fmt: QTextCharFormat):
        c = self.textCursor()
        if c.hasSelection():
            c.mergeCharFormat(fmt)
            self.setTextCursor(c)
        else:
            self.mergeCurrentCharFormat(fmt)

    def toggle_bold(self):
        fmt = self.currentCharFormat()
        w = 700 if fmt.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal
        nf = QTextCharFormat()
        nf.setFontWeight(w)
        self.merge_char_fmt(nf)

    def toggle_italic(self):
        fmt = self.currentCharFormat()
        nf = QTextCharFormat()
        nf.setFontItalic(not fmt.fontItalic())
        self.merge_char_fmt(nf)

    def toggle_underline(self):
        fmt = self.currentCharFormat()
        nf = QTextCharFormat()
        nf.setFontUnderline(not fmt.fontUnderline())
        self.merge_char_fmt(nf)

    def toggle_strike(self):
        fmt = self.currentCharFormat()
        nf = QTextCharFormat()
        nf.setFontStrikeOut(not fmt.fontStrikeOut())
        self.merge_char_fmt(nf)

    def clear_char_formatting(self):
        c = self.textCursor()
        c.setCharFormat(QTextCharFormat())
        self.setTextCursor(c)

    # --- Block / structure ---
    def set_paragraph(self):
        c = self.textCursor()
        bf = QTextBlockFormat()
        bf.setHeadingLevel(0)
        bf.setTopMargin(4)
        c.setBlockFormat(bf)

    def set_heading(self, level: int):
        """level 1..3 = H1..H3; 0 = paragraph."""
        c = self.textCursor()
        bf = QTextBlockFormat()
        bf.setHeadingLevel(level)
        sizes = {1: 28, 2: 22, 3: 18, 0: 16}
        cf = QTextCharFormat()
        cf.setFontWeight(QFont.Weight.Bold)
        cf.setFontPointSize(sizes.get(level, 16))
        c.beginEditBlock()
        c.setBlockFormat(bf)
        c.mergeCharFormat(cf)
        c.endEditBlock()

    def toggle_bullet_list(self):
        c = self.textCursor()
        lf = QTextListFormat()
        lf.setStyle(QTextListFormat.ListStyleDiscMarker)
        c.createList(lf)

    def toggle_numbered_list(self):
        c = self.textCursor()
        lf = QTextListFormat()
        lf.setStyle(QTextListFormat.ListStyleDecimalMarker)
        c.createList(lf)

    def insert_checklist_item(self):
        c = self.textCursor()
        c.insertText("☐ ")
        self.setTextCursor(c)

    def apply_blockquote(self):
        c = self.textCursor()
        bf = QTextBlockFormat()
        bf.setLeftMargin(16)
        bf.setIndent(1)
        cf = QTextCharFormat()
        cf.setFontItalic(True)
        c.beginEditBlock()
        c.mergeBlockFormat(bf)
        c.mergeCharFormat(cf)
        c.endEditBlock()

    def insert_horizontal_rule(self):
        c = self.textCursor()
        c.insertHtml("<hr/>")

    def insert_code_block(self):
        c = self.textCursor()
        c.insertHtml("<pre><code>code</code></pre><p><br/></p>")

    def apply_inline_code(self):
        c = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontFamily("Consolas")
        fmt.setBackground(QColor("#f0f0f0"))
        if c.hasSelection():
            c.mergeCharFormat(fmt)
        else:
            c.mergeCharFormat(fmt)

    def insert_or_edit_link(self):
        c = self.textCursor()
        current = ""
        if c.charFormat().isAnchor():
            current = c.charFormat().anchorHref() or ""
        dlg = LinkEditDialog(current, self)
        if dlg.exec() != QDialog.Accepted:
            return
        url = dlg.url()
        fmt = QTextCharFormat()
        fmt.setAnchor(True)
        fmt.setAnchorHref(url)
        fmt.setForeground(QColor("#0645ad"))
        fmt.setFontUnderline(True)
        if not c.hasSelection():
            c.insertText(url, fmt)
        else:
            c.mergeCharFormat(fmt)

    def remove_link(self):
        c = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setAnchor(False)
        fmt.setForeground(QColor("#1a1a1a"))
        fmt.setFontUnderline(False)
        c.mergeCharFormat(fmt)

    def insert_image_interactive(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Insert image", "", "Images (*.png *.jpg *.jpeg *.gif *.webp)"
        )
        for p in paths:
            self.insert_image_from_path(p)

    def insert_image_from_path(
        self, path: str, alt: str | None = None, prompt_alt: bool = True
    ) -> str | None:
        path = os.path.normpath(path)
        if not os.path.isfile(path):
            return None
        aid = str(uuid.uuid4())
        ext = Path(path).suffix.lower() or ".png"
        dest = os.path.join(self._media_cache, f"{aid}{ext}")
        try:
            import shutil

            shutil.copy2(path, dest)
        except OSError:
            QMessageBox.warning(self, "Image", f"Could not copy image:\n{path}")
            return None
        if prompt_alt:
            dlg = AltTextDialog(alt or "", self)
            if dlg.exec() != QDialog.Accepted:
                return None
            alt = dlg.alt_text()
        else:
            alt = alt or ""
        url = attachment_url(aid)
        alt_esc = html_module.escape(alt, quote=True)
        html = f'<p><img src="{url}" alt="{alt_esc}" /></p>'
        self.textCursor().insertHtml(html)
        mime, _ = mimetypes.guess_type(dest)
        self.imageAttached.emit(aid, dest)
        return aid

    def paste_plain(self):
        from PySide6.QtGui import QClipboard

        clip = QApplication.clipboard()
        t = clip.text(QClipboard.Mode.Clipboard)
        self.textCursor().insertText(t)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            self.textCursor().insertHtml("<br/>")
            event.accept()
            return
        if self._enable_slash and event.key() == Qt.Key.Key_Slash:
            c = self.textCursor()
            block = c.block().text()
            pos = c.positionInBlock()
            prefix = block[:pos]
            if prefix.strip() == "":
                self.slashMenuRequested.emit()
                event.accept()
                return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Bold", self.toggle_bold, QKeySequence("Ctrl+B"))
        menu.addAction("Italic", self.toggle_italic, QKeySequence("Ctrl+I"))
        menu.addAction("Paste without formatting", self.paste_plain)
        if self.textCursor().charFormat().isAnchor():
            menu.addAction("Edit link…", self.insert_or_edit_link)
            menu.addAction("Remove link", self.remove_link)
        menu.addSeparator()
        menu.addAction("Insert image…", self.insert_image_interactive)
        menu.exec(event.globalPos())

    def canInsertFromMimeData(self, source: QMimeData) -> bool:
        if source.hasImage() or source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source: QMimeData):
        if source.hasImage():
            img = source.imageData()
            if isinstance(img, QImage) and not img.isNull():
                fname = f"paste_{uuid.uuid4().hex[:10]}.png"
                dest = os.path.join(self._media_cache, fname)
                img.save(dest, "PNG")
                self.insert_image_from_path(dest, alt="", prompt_alt=False)
            return
        if source.hasUrls():
            for url in source.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    low = path.lower()
                    if low.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                        self.insert_image_from_path(path)
                        return
            super().insertFromMimeData(source)
            return
        super().insertFromMimeData(source)
