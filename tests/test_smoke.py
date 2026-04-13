import os
import pytest
from pathlib import Path

from pypub.domain.settings import SettingsManager
from pypub.infrastructure.db import Database
from pypub.ui.shell import MainWindow
from pypub.application.auth_service import AuthService
from pypub.application.post_service import PostService

# Simple in-memory mock for Keyring
class MockKeyring:
    def get_token(self, account_id): return "mock_token"
    def delete_token(self, account_id): pass

@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test.sqlite"
    return Database(db_path)

@pytest.fixture
def mock_managers(tmp_path, test_db):
    config_dir = tmp_path / "config"
    settings = SettingsManager(config_dir)
    auth = AuthService(test_db, MockKeyring(), "mock_id", "mock_uri")
    post = PostService(test_db, MockKeyring())
    return auth, post, settings, tmp_path

def test_settings_persistence(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Check default creates without error
    manager = SettingsManager(config_dir)
    assert manager.settings.theme == "system"
    manager.settings.theme = "dark"
    manager.save()
    
    # Reload from disk
    manager2 = SettingsManager(config_dir)
    assert manager2.settings.theme == "dark"
    assert manager2.settings.wrap_lines == True

def test_mainwindow_smoke(qtbot, mock_managers):
    auth, post, settings, tmp_path = mock_managers
    
    # Initialize the entire UI stack to catch Qt layout/widget errors
    window = MainWindow(auth, post, settings, tmp_path)
    qtbot.addWidget(window)
    
    # Assert sanity
    assert window.isVisible() == False
    assert window.stack.count() >= 4 # We created at least Accounts, Drafts, Compose, Settings, Tech
