import sys
import logging
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QListWidget, QStackedWidget, QPushButton, 
                               QLabel, QFormLayout, QLineEdit, QComboBox, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt

from pypub.application.auth_service import AuthService
from pypub.application.post_service import PostService
from pypub.ui.login import LoginDialog
from pypub.ui.compose import ComposeWidget
from pypub.ui.drafts import DraftsWidget
from pypub.ui.technical import TechnicalWidget

logger = logging.getLogger("pypub")

        
from pypub.ui.settings import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self, auth_service: AuthService, post_service: PostService, settings_manager, app_data_path):
        super().__init__()
        self.auth_service = auth_service
        self.post_service = post_service
        self.settings_manager = settings_manager
        self.app_data_path = app_data_path
        self.current_account = None

        self.setWindowTitle("PyPub - Micropub Desktop Client")
        self.resize(1000, 700)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        h_layout = QHBoxLayout(main_widget)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(200)
        self.sidebar.addItem("Accounts")
        self.sidebar.addItem("Drafts")
        self.sidebar.addItem("Compose")
        self.sidebar.addItem("Settings")
        self.sidebar.addItem("Technical")
        self.sidebar.addItem("About")
        self.sidebar.currentRowChanged.connect(self.change_tab)

        # Stack
        self.stack = QStackedWidget()
        
        # Views
        self.accounts_view = self._build_accounts_view()
        self.drafts_view = DraftsWidget(self.post_service, str(self.app_data_path))
        
        # IMPORT PHASE 2 EDITOR
        from pypub.ui.editor_workspace import EditorWorkspace
        self.compose_view = EditorWorkspace(self.post_service, str(self.app_data_path), self.settings_manager)
        
        self.tech_view = TechnicalWidget()

        self.stack.addWidget(self.accounts_view)
        self.stack.addWidget(self.drafts_view)
        self.stack.addWidget(self.compose_view)
        self.stack.addWidget(self.tech_view) 
        
        # Settings Wrapper
        settings_wrapper = QWidget()
        sw_layout = QVBoxLayout(settings_wrapper)
        btn_open_settings = QPushButton("Open Settings Panel")
        btn_open_settings.clicked.connect(self._open_settings)
        sw_layout.addWidget(QLabel("Settings Configurator"))
        sw_layout.addWidget(btn_open_settings)
        sw_layout.addStretch()
        
        # About Wrapper
        about_wrapper = QWidget()
        aw_layout = QVBoxLayout(about_wrapper)
        btn_open_about = QPushButton("Open About Info")
        btn_open_about.clicked.connect(self._open_about)
        aw_layout.addWidget(QLabel("About PyPub"))
        aw_layout.addWidget(btn_open_about)
        aw_layout.addStretch()
        
        self.stack.addWidget(settings_wrapper)
        self.stack.addWidget(self.tech_view) 
        self.stack.addWidget(about_wrapper)

        h_layout.addWidget(self.sidebar)
        h_layout.addWidget(self.stack)

        self.refresh_accounts()

    def _open_settings(self):
        d = SettingsDialog(self.settings_manager, self.app_data_path, self)
        d.exec()
        
    def _open_about(self):
        from pypub.ui.about import AboutDialog
        d = AboutDialog(str(self.app_data_path), self)
        d.exec()

    def _build_accounts_view(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("<h2>Accounts</h2>"))
        
        from PySide6.QtWidgets import QSplitter, QTextBrowser
        splitter = QSplitter(Qt.Horizontal)
        
        left = QWidget()
        l_layout = QVBoxLayout(left)
        self.account_list = QListWidget()
        self.account_list.itemClicked.connect(self.select_account)
        l_layout.addWidget(self.account_list)

        btn_add = QPushButton("Add Account (IndieAuth)")
        btn_add.clicked.connect(self.add_account)
        l_layout.addWidget(btn_add)
        splitter.addWidget(left)
        
        right = QWidget()
        r_layout = QVBoxLayout(right)
        self.acc_details = QTextBrowser()
        r_layout.addWidget(self.acc_details)
        
        btn_refresh = QPushButton("Refresh Metadata")
        btn_refresh.clicked.connect(self._refresh_meta)
        btn_revoke = QPushButton("Revoke Local Session/Token")
        btn_revoke.clicked.connect(self._revoke_session)
        btn_remove = QPushButton("Remove Account Completely")
        btn_remove.setStyleSheet("color: red;")
        btn_remove.clicked.connect(self._remove_account)
        
        r_layout.addWidget(btn_refresh)
        r_layout.addWidget(btn_revoke)
        r_layout.addWidget(btn_remove)
        splitter.addWidget(right)
        
        layout.addWidget(splitter)
        return w

    def refresh_accounts(self):
        self.account_list.clear()
        for acc in self.auth_service.get_accounts():
            self.account_list.addItem(f"{acc.display_name} ({acc.me_url})")

    def select_account(self, item):
        idx = self.account_list.currentRow()
        accounts = self.auth_service.get_accounts()
        if idx >= 0 and idx < len(accounts):
            self.current_account = accounts[idx]
            self.drafts_view.set_account(self.current_account)
            self.compose_view.set_account(self.current_account)
            logger.info(f"Selected account: {self.current_account.me_url}")
            
            # Populate Details
            details = f"<h3>{self.current_account.display_name}</h3>"
            details += f"<p><b>Me URL:</b> {self.current_account.me_url}</p>"
            details += f"<p><b>Micropub Endpoint:</b> {self.current_account.micropub_endpoint}</p>"
            details += f"<p><b>Media Endpoint:</b> {self.current_account.media_endpoint}</p>"
            details += f"<p><b>Scopes Granted:</b> {self.current_account.scopes_granted}</p>"
            
            has_token = self.auth_service.keyring_store.get_token(self.current_account.id) is not None
            details += f"<p><b>Local Token:</b> {'ACTIVE' if has_token else 'MISSING/REVOKED'}</p>"
            
            self.acc_details.setHtml(details)
            
            # Fetch Capabilities silent
            try:
                caps = self.post_service.fetch_capabilities(self.current_account)
                self.tech_view.log(f"Capabilities loaded: {caps.raw_config_json}")
            except Exception as e:
                self.tech_view.log(f"Failed to load capabilities: {e}")

    def _refresh_meta(self):
        if not self.current_account: return
        QMessageBox.information(self, "Info", "In a full version, this triggers a re-fetch of rel=micropub endpoints.")
        
    def _revoke_session(self):
        if not self.current_account: return
        # Wipe token locally
        self.auth_service.keyring_store.delete_token(self.current_account.id)
        self.select_account(None) # Refresh panel
        QMessageBox.warning(self, "Revoked", "Local token removed. You must login again.")
        
    def _remove_account(self):
        if not self.current_account: return
        rep = QMessageBox.question(self, "Remove", "Remove account from PyPub completely? Drafts may be orphaned.")
        if rep == QMessageBox.Yes:
            # Need to implement in db.py delete_account, for now wiping token.
            self.auth_service.keyring_store.delete_token(self.current_account.id)
            QMessageBox.information(self, "Removed", "Account detached.")

    def add_account(self):
        dialog = LoginDialog(self.auth_service, self)
        if dialog.exec():
            self.refresh_accounts()

    def change_tab(self, index):
        if index == 1 or index == 2:
            if not self.current_account:
                QMessageBox.warning(self, "No Account", "Please select an account first.")
                self.sidebar.setCurrentRow(0)
                return
        self.stack.setCurrentIndex(index)
