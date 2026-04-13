from pathlib import Path

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout

from pypub.ui.about_panel import AboutPanel


class AboutDialog(QDialog):
    """Optional modal about — same content as the inline About panel."""

    def __init__(self, app_data_dir: str, config_dir: str, log_dir: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PyPub")
        self.resize(480, 520)
        layout = QVBoxLayout(self)
        layout.addWidget(
            AboutPanel(Path(app_data_dir), Path(config_dir), Path(log_dir) if log_dir else None, self),
            1,
        )
        row = QHBoxLayout()
        row.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        layout.addLayout(row)
