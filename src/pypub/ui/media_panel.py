from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
import uuid
import os

class MediaPanel(QWidget):
    def __init__(self, post_service, media_cache_dir):
        super().__init__()
        self.post_service = post_service
        self.media_cache = media_cache_dir
        self.account = None
        self.draft_id = None
        
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        header.addWidget(QLabel("<b>Media Attachments</b>"))
        self.btn_add = QPushButton("Add Media")
        self.btn_add.clicked.connect(self.browse_media)
        header.addWidget(self.btn_add)
        layout.addLayout(header)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

    def browse_media(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Media", "", "Images (*.png *.jpg *.jpeg *.gif *.webp)")
        if not file_paths:
            return
        
        for path in file_paths:
            # Here we should attach it to the backend model Attachment
            if not self.account:
                QMessageBox.warning(self, "No Account", "Please select an account first.")
                return
            
            # Simple UI append for now
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.UserRole, path)
            self.list_widget.addItem(item)
