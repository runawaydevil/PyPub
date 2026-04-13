"""Media attachments as light cards with thumbnails and actions."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pypub.application.editor_sync import ensure_attachment_ids


class _MediaCard(QFrame):
    """Single attachment row."""

    altChanged = Signal(str, str)  # id, alt_text
    removeRequested = Signal(str)
    insertRequested = Signal(str)
    reorderUp = Signal(str)
    reorderDown = Signal(str)

    def __init__(self, data: dict[str, Any], parent=None):
        super().__init__(parent)
        self.aid = str(data.get("id", ""))
        self.setObjectName("MediaCard")
        self._data = dict(data)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        self.thumb = QLabel()
        self.thumb.setFixedSize(72, 72)
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setObjectName("MediaThumb")
        self._set_thumb()
        lay.addWidget(self.thumb)

        mid = QVBoxLayout()
        name = Path(data.get("local_path") or data.get("uploaded_url") or "?").name
        self.lbl_name = QLabel(name[:48] + ("…" if len(name) > 48 else ""))
        self.lbl_name.setObjectName("DraftTitle")
        mid.addWidget(self.lbl_name)

        emb = bool(data.get("embedded_in_document"))
        self.badge = QLabel("No corpo" if emb else "Anexo")
        self.badge.setObjectName("MediaEmbedBadge")
        mid.addWidget(self.badge)

        st = data.get("upload_state", "pending")
        self.lbl_state = QLabel(f"Upload: {st}")
        self.lbl_state.setObjectName("MediaMeta")
        mid.addWidget(self.lbl_state)

        sz = data.get("size_bytes")
        if sz is None and data.get("local_path") and os.path.isfile(data["local_path"]):
            sz = os.path.getsize(data["local_path"])
        if sz is not None:
            mid.addWidget(QLabel(f"Size: {sz // 1024} KB"))

        self.alt_edit = QLineEdit(data.get("alt_text") or "")
        self.alt_edit.setPlaceholderText("Alt text (accessibility)")
        self.alt_edit.textEdited.connect(lambda t: self.altChanged.emit(self.aid, t))
        mid.addWidget(self.alt_edit)

        warn = not (data.get("alt_text") or "").strip() and data.get("mime_type", "").startswith("image")
        if warn:
            w = QLabel("No alt text")
            w.setObjectName("MediaWarning")
            mid.addWidget(w)

        lay.addLayout(mid, 1)

        btns = QVBoxLayout()
        for label, slot in [
            ("Insert", lambda: self.insertRequested.emit(self.aid)),
            ("↑", lambda: self.reorderUp.emit(self.aid)),
            ("↓", lambda: self.reorderDown.emit(self.aid)),
            ("Copy URL", self._copy_url),
            ("Open local", self._open_local),
            ("Open remote", self._open_remote),
            ("Remove", lambda: self.removeRequested.emit(self.aid)),
        ]:
            b = QPushButton(label)
            b.setFixedHeight(26)
            b.clicked.connect(slot)
            btns.addWidget(b)
        lay.addLayout(btns)

    def _set_thumb(self):
        p = self._data.get("local_path")
        if p and os.path.isfile(p):
            pm = QPixmap(p)
            if not pm.isNull():
                self.thumb.setPixmap(pm.scaled(68, 68, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                return
        self.thumb.setText("IMG")

    def _copy_url(self):
        u = self._data.get("uploaded_url")
        if not u:
            QMessageBox.information(self, "Media", "Not uploaded yet.")
            return
        QApplication.clipboard().setText(u)

    def _open_local(self):
        p = self._data.get("local_path")
        if p and os.path.isfile(p):
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def _open_remote(self):
        u = self._data.get("uploaded_url")
        if u:
            QDesktopServices.openUrl(QUrl(u))

    def refresh(self, data: dict[str, Any]):
        self._data = dict(data)
        self.lbl_state.setText(f"Upload: {data.get('upload_state', 'pending')}")
        emb = bool(data.get("embedded_in_document"))
        self.badge.setText("No corpo" if emb else "Anexo")
        self._set_thumb()


class MediaPanel(QWidget):
    """Card grid synced with attachments_json."""

    attachmentsChanged = Signal()

    def __init__(self, post_service, media_cache_dir: str, parent=None):
        super().__init__(parent)
        self.post_service = post_service
        self.media_cache = media_cache_dir
        os.makedirs(self.media_cache, exist_ok=True)
        self.account = None
        self._items: list[dict[str, Any]] = []
        self._cards: dict[str, _MediaCard] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)
        head = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Media")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Manage local files, alt text, and which items are embedded in the document.")
        subtitle.setObjectName("SectionHint")
        subtitle.setWordWrap(True)
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        head.addLayout(title_block, 1)
        btn = QPushButton("Add files…")
        btn.clicked.connect(self._browse)
        head.addWidget(btn)
        root.addLayout(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._grid_host = QWidget()
        self._grid = QVBoxLayout(self._grid_host)
        self._empty = QLabel("No media added yet. Add files here to attach them to the current draft.")
        self._empty.setObjectName("EmptyBody")
        self._empty.setWordWrap(True)
        self._grid.addWidget(self._empty)
        self._grid.addStretch()
        scroll.setWidget(self._grid_host)
        root.addWidget(scroll, 1)

    def set_account(self, acc):
        self.account = acc

    def load_from_json(self, raw: str):
        self._clear_cards()
        try:
            self._items = json.loads(raw) if raw else []
        except json.JSONDecodeError:
            self._items = []
        if not isinstance(self._items, list):
            self._items = []
        self._items = ensure_attachment_ids(self._items)
        self._sync_order()
        self._empty.setVisible(len(self._items) == 0)
        for it in self._items:
            self._add_card_widget(dict(it))

    def get_attachments_json(self) -> str:
        self._sync_order()
        return json.dumps(self._items, ensure_ascii=False)

    def _clear_cards(self):
        for w in list(self._cards.values()):
            w.deleteLater()
        self._cards.clear()
        self._items = []

    def _add_card_widget(self, data: dict[str, Any]):
        aid = str(data.get("id", ""))
        if not aid:
            import uuid

            data["id"] = str(uuid.uuid4())
            aid = data["id"]
        card = _MediaCard(data, self._grid_host)
        card.altChanged.connect(self._on_alt)
        card.removeRequested.connect(self._on_remove)
        card.insertRequested.connect(self._on_insert)
        card.reorderUp.connect(self._on_up)
        card.reorderDown.connect(self._on_down)
        self._cards[aid] = card
        self._grid.insertWidget(self._grid.count() - 1, card)

    def register_attachment(self, data: dict[str, Any]):
        """Append new attachment from editor (already copied to cache)."""
        self._items.append(data)
        self._sync_order()
        self._empty.setVisible(False)
        self._add_card_widget(data)
        self.attachmentsChanged.emit()

    def _on_alt(self, aid: str, alt: str):
        for it in self._items:
            if str(it.get("id")) == aid:
                it["alt_text"] = alt
                break
        self.attachmentsChanged.emit()

    def _on_remove(self, aid: str):
        self._items = [x for x in self._items if str(x.get("id")) != aid]
        w = self._cards.pop(aid, None)
        if w:
            w.deleteLater()
        self._sync_order()
        self._empty.setVisible(len(self._items) == 0)
        self.attachmentsChanged.emit()

    def _on_insert(self, aid: str):
        # Parent workspace connects to insert image tag at cursor
        if hasattr(self, "_insert_cb") and self._insert_cb:
            self._insert_cb(aid)

    def set_insert_callback(self, cb: Callable[[str], None]):
        self._insert_cb = cb

    def _on_up(self, aid: str):
        idx = next((i for i, x in enumerate(self._items) if str(x.get("id")) == aid), -1)
        if idx > 0:
            self._items[idx - 1], self._items[idx] = self._items[idx], self._items[idx - 1]
            self._rebuild_grid()

    def _on_down(self, aid: str):
        idx = next((i for i, x in enumerate(self._items) if str(x.get("id")) == aid), -1)
        if 0 <= idx < len(self._items) - 1:
            self._items[idx + 1], self._items[idx] = self._items[idx], self._items[idx + 1]
            self._rebuild_grid()

    def _rebuild_grid(self):
        for w in list(self._cards.values()):
            w.deleteLater()
        self._cards.clear()
        self._sync_order()
        for it in self._items:
            self._add_card_widget(dict(it))
        self.attachmentsChanged.emit()

    def _sync_order(self) -> None:
        for idx, item in enumerate(self._items):
            item["order"] = idx

    def _browse(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Media", "", "Images (*.png *.jpg *.jpeg *.gif *.webp);;All (*.*)"
        )
        for p in paths:
            import uuid
            import shutil

            aid = str(uuid.uuid4())
            ext = Path(p).suffix or ".bin"
            dest = os.path.join(self.media_cache, f"{aid}{ext}")
            try:
                shutil.copy2(p, dest)
            except OSError:
                continue
            mime, _ = __import__("mimetypes").guess_type(dest)
            self.register_attachment(
                {
                    "id": aid,
                    "local_path": dest,
                    "mime_type": mime or "application/octet-stream",
                    "alt_text": "",
                    "uploaded_url": None,
                    "upload_state": "pending",
                    "embedded_in_document": False,
                }
            )

    def mark_embedded(self, aid: str, embedded: bool):
        for it in self._items:
            if str(it.get("id")) == aid:
                it["embedded_in_document"] = embedded
                card = self._cards.get(aid)
                if card:
                    card.refresh(it)
                break
        self.attachmentsChanged.emit()
