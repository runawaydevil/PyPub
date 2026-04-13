from PySide6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, QComboBox, QCheckBox, QPushButton
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

class SettingsDialog(QDialog):
    def __init__(self, settings_manager, app_data_dir, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.app_data_dir = app_data_dir
        self.setWindowTitle("PyPub Settings")
        self.resize(500, 400)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        s = settings_manager.settings
        
        # 1. General
        gen_w = QWidget()
        gen_layout = QFormLayout(gen_w)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["system", "light", "dark"])
        self.theme_combo.setCurrentText(s.theme)
        
        self.chk_confirm_exit = QCheckBox("Confirm before exit")
        self.chk_confirm_exit.setChecked(s.confirm_on_exit)
        
        gen_layout.addRow("Theme:", self.theme_combo)
        gen_layout.addRow(self.chk_confirm_exit)
        tabs.addTab(gen_w, "General")

        # 2. Editor
        ed_w = QWidget()
        ed_layout = QFormLayout(ed_w)
        self.chk_wrap = QCheckBox("Wrap Long Lines")
        self.chk_wrap.setChecked(s.wrap_lines)
        ed_layout.addRow(self.chk_wrap)
        tabs.addTab(ed_w, "Editor")

        # 3. Publishing
        pub_w = QWidget()
        pub_layout = QFormLayout(pub_w)
        self.chk_confirm_pub = QCheckBox("Confirm before publishing via Checklist")
        self.chk_confirm_pub.setChecked(s.confirm_before_publish)
        pub_layout.addRow(self.chk_confirm_pub)
        tabs.addTab(pub_w, "Publishing")

        # 4. Privacy & Storage
        priv_w = QWidget()
        priv_layout = QVBoxLayout(priv_w)
        
        btn_open_data = QPushButton("Open Data Folder (SQLite/Cache)")
        btn_open_data.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.app_data_dir))))
        
        priv_layout.addWidget(btn_open_data)
        priv_layout.addStretch()
        tabs.addTab(priv_w, "Privacy & Storage")

        # 5. Advanced
        adv_w = QWidget()
        adv_layout = QFormLayout(adv_w)
        self.chk_tech = QCheckBox("Show Technical/Metadata Tab")
        self.chk_tech.setChecked(s.show_technical_tab)
        adv_layout.addRow(self.chk_tech)
        tabs.addTab(adv_w, "Advanced")

        layout.addWidget(tabs)

        btn_save = QPushButton("Save Preferences")
        btn_save.clicked.connect(self.save_settings)
        layout.addWidget(btn_save)

    def save_settings(self):
        s = self.settings_manager.settings
        s.theme = self.theme_combo.currentText()
        s.confirm_on_exit = self.chk_confirm_exit.isChecked()
        s.wrap_lines = self.chk_wrap.isChecked()
        s.confirm_before_publish = self.chk_confirm_pub.isChecked()
        s.show_technical_tab = self.chk_tech.isChecked()

        self.settings_manager.save()
        self.accept()
