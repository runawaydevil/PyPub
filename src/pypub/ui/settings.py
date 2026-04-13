from pathlib import Path

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout

from pypub.ui.settings_panel import SettingsPanel


class SettingsDialog(QDialog):
    """Modal settings — same form as the inline Settings panel."""

    def __init__(self, settings_manager, app_data_dir: Path, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.app_data_dir = Path(app_data_dir)
        self.setWindowTitle("PyPub Settings")
        self.resize(520, 480)

        layout = QVBoxLayout(self)
        self.panel = SettingsPanel(settings_manager, self.app_data_dir, self)
        layout.addWidget(self.panel, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        ok = QPushButton("OK")
        ok.clicked.connect(self._accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        actions.addWidget(ok)
        actions.addWidget(cancel)
        layout.addLayout(actions)

    def _accept(self) -> None:
        self.panel.apply_to_manager()
        self.accept()
