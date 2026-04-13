import sys
from pathlib import Path

from platformdirs import user_data_dir, user_config_dir, user_log_dir
from PySide6.QtWidgets import QApplication

from pypub import __version__
from pypub.application.auth_service import AuthService
from pypub.application.crash_handler import global_exception_handler
from pypub.application.post_service import PostService
from pypub.domain.settings import SettingsManager
from pypub.infrastructure.db import Database
from pypub.infrastructure.keyring_store import KeyringStore
from pypub.infrastructure.logger import setup_logger
from pypub.ui.app_icon import load_app_icon
from pypub.ui.editor.editor_theme import apply_app_theme
from pypub.ui.shell import MainWindow

def main():
    # Setup global crash handler
    sys.excepthook = global_exception_handler
    
    app = QApplication(sys.argv)
    app.setApplicationName("PyPub")
    app.setApplicationVersion(__version__)
    app_icon = load_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Platform Dirs Config
    app_author = "Pablo Murad"
    app_data = Path(user_data_dir("PyPub", app_author))
    app_config = Path(user_config_dir("PyPub", app_author))
    app_log = Path(user_log_dir("PyPub", app_author))
    
    app_data.mkdir(parents=True, exist_ok=True)
    app_config.mkdir(parents=True, exist_ok=True)
    app_log.mkdir(parents=True, exist_ok=True)

    # Setup Logging
    logger = setup_logger(app_log)
    logger.info("Starting PyPub")
    
    settings_manager = SettingsManager(app_config)
    apply_app_theme(app, settings_manager.settings)

    # Infra
    db = Database(app_data / "pypub.sqlite")
    keyring_store = KeyringStore()

    # For strict IndieAuth servers (like IndieKit), the client_id origin must exactly match the redirect_uri origin.
    # We use 127.0.0.1 instead of localhost to prevent IPv6 fetch failures from Node.js servers.
    client_id = "http://127.0.0.1:8080/"
    redirect_uri = "http://127.0.0.1:8080/callback"

    # Application Services
    auth_service = AuthService(db, keyring_store, client_id, redirect_uri)
    post_service = PostService(db, keyring_store)

    # UI
    window = MainWindow(
        auth_service,
        post_service,
        settings_manager,
        app_data,
        app_config_path=app_config,
        app_log_path=app_log,
    )
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
