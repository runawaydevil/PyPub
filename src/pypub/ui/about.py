import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from pypub import __version__, __app_name__, __author__, __contact__

class AboutDialog(QDialog):
    def __init__(self, app_data_dir: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {__app_name__}")
        self.resize(400, 250)
        
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel(f"<h2>{__app_name__}</h2>")
        lbl_title.setAlignment(Qt.AlignCenter)
        
        lbl_version = QLabel(f"<b>Version:</b> {__version__}")
        lbl_author = QLabel(f"<b>Author:</b> {__author__} ({__contact__})")
        lbl_data = QLabel(f"<b>Data AppDir:</b> {app_data_dir}")
        lbl_data.setWordWrap(True)
        lbl_desc = QLabel("A desktop Micropub client built with PySide6.")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_version)
        layout.addWidget(lbl_author)
        layout.addWidget(lbl_desc)
        layout.addWidget(lbl_data)
        
        layout.addStretch()
        
        btn_update = QPushButton("Check for Updates (Manual)")
        btn_update.clicked.connect(self._check_updates)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        
        actions = QHBoxLayout()
        actions.addWidget(btn_update)
        actions.addWidget(btn_close)
        
        layout.addLayout(actions)

    def _check_updates(self):
        QMessageBox.information(
            self, 
            "Update Check", 
            "You are running the latest version! (This is currently a manual stub without remote server)."
        )
