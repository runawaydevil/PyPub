import os
import shutil
import uuid
from typing import List
from PySide6.QtGui import QAction, QIcon, QKeySequence, QTextCursor
from PySide6.QtWidgets import (QTextEdit, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QUrl

class RichTextEditor(QTextEdit):
    """
    Extensão do QTextEdit para suporte a Rich Text limpo, Drag-and-Drop 
    e mapeamento local seguro para anexos antes do upload.
    """
    def __init__(self, media_cache_dir: str, parent=None):
        super().__init__(parent)
        self.media_cache_dir = media_cache_dir
        os.makedirs(self.media_cache_dir, exist_ok=True)
        # Placeholder ID tracking
        self.local_attachments = []

    def canInsertFromMimeData(self, source):
        if source.hasImage() or source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        if source.hasImage():
            # Handle Clipboard Paste Image
            image = source.imageData()
            if image:
                file_name = f"paste_{uuid.uuid4().hex[:8]}.png"
                local_path = os.path.join(self.media_cache_dir, file_name)
                image.save(local_path, "PNG")
                self.insert_local_image(local_path)
            return
            
        if source.hasUrls():
            for url in source.urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    # simplistic check
                    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                        self.insert_local_image(path)
            # Accept URLs natively but don't dump them as raw text unless wanted
            return super().insertFromMimeData(source)
            
        super().insertFromMimeData(source)

    def insert_local_image(self, local_path: str):
        # Gera o html interno
        file_url = QUrl.fromLocalFile(local_path).toString()
        cursor = self.textCursor()
        # Aqui podemos introduzir um schema interno data-pypub-attachment... mas por hora image tag basta
        cursor.insertHtml(f'<img src="{file_url}" alt="Local Image" /><br/>')
        self.local_attachments.append(local_path)

    # Basic Toolbar Helpers -> These would typically hook into QActions
    def toggle_bold(self):
        fmt = self.currentCharFormat()
        fmt.setFontWeight(700 if fmt.fontWeight() != 700 else 400)
        self.textCursor().mergeCharFormat(fmt)

    def toggle_italic(self):
        fmt = self.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.textCursor().mergeCharFormat(fmt)
