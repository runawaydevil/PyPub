from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)

from pypub.application.export_service import ExportService


class DraftRow(QWidget):
    def __init__(self, draft, parent=None):
        super().__init__(parent)
        self.setObjectName("PageCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        badge = QLabel((draft.entry_type or "note").upper())
        badge.setObjectName("PresetChip")
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(4)

        title = QLabel(draft.title or "Untitled draft")
        title.setObjectName("DraftTitle")
        title.setWordWrap(True)
        content.addWidget(title)

        meta_bits = [draft.status.capitalize()]
        if draft.is_dirty:
            meta_bits.append("Unsaved changes waiting")
        if draft.modified_at:
            meta_bits.append(f"Updated {draft.modified_at}")
        meta = QLabel(" · ".join(meta_bits))
        meta.setObjectName("DraftMeta")
        meta.setWordWrap(True)
        content.addWidget(meta)

        summary_text = draft.summary or draft.content_plain or ""
        summary = QLabel(summary_text[:140] + ("…" if len(summary_text) > 140 else ""))
        summary.setObjectName("CardMeta")
        summary.setWordWrap(True)
        summary.setVisible(bool(summary_text))
        content.addWidget(summary)

        layout.addLayout(content, 1)

        status = QLabel("Ready to revisit")
        if draft.status == "published":
            status.setText("Already published")
        elif draft.is_dirty:
            status.setText("Still settling in")
        status.setObjectName("DraftStatus")
        status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(status)


class DraftsWidget(QWidget):
    def __init__(self, post_service, app_data_path=None):
        super().__init__()
        self.post_service = post_service
        self.account = None
        self.app_data_path = app_data_path
        self._all_drafts = []

        self.setObjectName("PageSurface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        intro = QWidget()
        intro_lay = QVBoxLayout(intro)
        intro_lay.setContentsMargins(0, 0, 0, 0)
        intro_lay.setSpacing(4)
        title = QLabel("Draft library")
        title.setObjectName("PageHeroTitle")
        subtitle = QLabel("Browse drafts by status or title and open any item with a double click.")
        subtitle.setObjectName("PageHeroSubtitle")
        subtitle.setWordWrap(True)
        intro_lay.addWidget(title)
        intro_lay.addWidget(subtitle)
        layout.addWidget(intro)

        controls = QFrame()
        controls.setObjectName("PageCard")
        h_filter = QHBoxLayout(controls)
        h_filter.setContentsMargins(18, 18, 18, 18)
        h_filter.setSpacing(10)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by title or content")
        self.search_box.textChanged.connect(self._apply_filters)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "draft", "published", "trash"])
        self.filter_combo.currentTextChanged.connect(self._apply_filters)

        h_filter.addWidget(self.search_box, 1)
        h_filter.addWidget(QLabel("Status"))
        h_filter.addWidget(self.filter_combo)
        layout.addWidget(controls)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(10)
        layout.addWidget(self.list_widget, 1)

        footer = QFrame()
        footer.setObjectName("PageCard")
        h_actions = QHBoxLayout(footer)
        h_actions.setContentsMargins(18, 14, 18, 14)
        self.selection_hint = QLabel("Select an account to load drafts.")
        self.selection_hint.setObjectName("SectionHint")
        self.btn_export = QPushButton("Export drafts")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._export_drafts)
        h_actions.addWidget(self.selection_hint)
        h_actions.addStretch()
        h_actions.addWidget(self.btn_export)
        layout.addWidget(footer)

    def set_account(self, account):
        self.account = account
        self.btn_export.setEnabled(self.account is not None)
        self.selection_hint.setText(
            f"Showing drafts for {account.display_name}." if account else "Select an account to load drafts."
        )
        self.refresh()

    def refresh(self):
        self._all_drafts = []
        if self.account:
            self._all_drafts = self.post_service.get_drafts(self.account.id)
        self._apply_filters()

    def _apply_filters(self):
        self.list_widget.clear()
        if not self.account:
            self._add_empty_card(
                "No account selected",
                "Select an account first to view its local drafts.",
            )
            return

        term = self.search_box.text().lower().strip()
        status_f = self.filter_combo.currentText()
        visible = []
        for draft in self._all_drafts:
            if status_f != "All" and draft.status != status_f:
                continue
            searchable = " ".join(
                [draft.title or "", draft.summary or "", draft.content_plain or ""]
            ).lower()
            if term and term not in searchable:
                continue
            visible.append(draft)

        if not visible:
            self._add_empty_card(
                "No drafts match the current filters",
                "Try another status or refine the search terms.",
            )
            return

        for draft in visible:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, draft.id)
            row = DraftRow(draft, self.list_widget)
            item.setSizeHint(QSize(0, 92))
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row)

    def _add_empty_card(self, title: str, body: str) -> None:
        item = QListWidgetItem()
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        card = QFrame()
        card.setObjectName("EmptyCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(6)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("EmptyTitle")
        body_lbl = QLabel(body)
        body_lbl.setObjectName("EmptyBody")
        body_lbl.setWordWrap(True)
        lay.addWidget(title_lbl)
        lay.addWidget(body_lbl)
        item.setSizeHint(QSize(0, 100))
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, card)

    def _export_drafts(self):
        if not self.account:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Drafts", "", "PyPub Archive (*.pypub)")
        if file_path:
            exp_service = ExportService(self.post_service)
            try:
                exp_service.export_drafts(self.account.id, file_path)
                QMessageBox.information(
                    self,
                    "Drafts exported",
                    "The selected drafts were exported to a PyPub archive.",
                )
            except Exception as e:
                QMessageBox.critical(self, "Export failed", f"Could not export drafts: {e}")
