from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog, QMessageBox, QListWidgetItem)
from PySide6.QtCore import Qt
from pypub.application.export_service import ExportService

class DraftsWidget(QWidget):
    def __init__(self, post_service, app_data_path=None):
        super().__init__()
        self.post_service = post_service
        self.account = None
        self.app_data_path = app_data_path
        self._all_drafts = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Drafts Manager</h2>"))
        
        # Filters
        h_filter = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search titles...")
        self.search_box.textChanged.connect(self._apply_filters)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "draft", "published", "trash"])
        self.filter_combo.currentTextChanged.connect(self._apply_filters)
        
        h_filter.addWidget(self.search_box)
        h_filter.addWidget(QLabel("Status:"))
        h_filter.addWidget(self.filter_combo)
        layout.addLayout(h_filter)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        # Actions
        h_actions = QHBoxLayout()
        self.btn_export = QPushButton("Export All to Archive")
        self.btn_export.clicked.connect(self._export_drafts)
        h_actions.addStretch()
        h_actions.addWidget(self.btn_export)
        
        layout.addLayout(h_actions)

    def set_account(self, account):
        self.account = account
        self.refresh()

    def refresh(self):
        self._all_drafts = []
        if self.account:
            self._all_drafts = self.post_service.get_drafts(self.account.id)
        self._apply_filters()

    def _apply_filters(self):
        self.list_widget.clear()
        if not self.account:
            self.list_widget.addItem("No account selected.")
            return
            
        term = self.search_box.text().lower()
        status_f = self.filter_combo.currentText()
        
        visible_count = 0
        for d in self._all_drafts:
            if status_f != "All" and d.status != status_f:
                continue
            t = d.title or "Untitled"
            if term and term not in t.lower():
                continue
                
            display = f"[{d.entry_type.upper()}] {t} - {d.status}"
            if d.is_dirty:
                display += " *(Unsaved changes)*"
                
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, d.id)
            self.list_widget.addItem(item)
            visible_count += 1
            
        if visible_count == 0:
            self.list_widget.addItem("No drafts found.")

    def _export_drafts(self):
        if not self.account: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Drafts", "", "PyPub Archive (*.pypub)")
        if file_path:
            import platformdirs
            from pathlib import Path
            db_path = Path(self.app_data_path) if self.app_data_path else Path()
            exp_service = ExportService(self.post_service, db_path)
            try:
                exp_service.export_drafts(self.account.id, file_path)
                QMessageBox.information(self, "Success", "Drafts exported securely!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")

