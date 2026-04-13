import pytest

from pypub.domain.settings import SettingsManager
from pypub.ui.app_icon import app_icon_candidates, load_app_icon
from pypub.ui.shell import MainWindow


def test_settings_persistence(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Check default creates without error
    manager = SettingsManager(config_dir)
    assert manager.settings.theme == "light"
    manager.settings.theme = "dark"
    manager.save()
    
    # Reload from disk
    manager2 = SettingsManager(config_dir)
    assert manager2.settings.theme == "dark"
    assert manager2.settings.wrap_lines == True


def test_settings_migrates_legacy_appearance_preset(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text(
        '{\n  "appearance_preset": "writer_nook",\n  "theme": "system"\n}\n',
        encoding="utf-8",
    )

    manager = SettingsManager(config_dir)

    assert manager.settings.appearance_preset == "office_light"
    assert manager.settings.theme == "system"
    manager.save()
    saved = (config_dir / "settings.json").read_text(encoding="utf-8")
    assert '"appearance_preset": "office_light"' in saved


def test_app_icon_loads():
    assert any(path.exists() for path in app_icon_candidates())
    assert load_app_icon().isNull() is False

def test_mainwindow_smoke(qtbot, mock_managers):
    auth, post, settings, tmp_path = mock_managers
    
    # Initialize the entire UI stack to catch Qt layout/widget errors
    window = MainWindow(auth, post, settings, tmp_path)
    qtbot.addWidget(window)
    
    # Assert sanity
    assert window.isVisible() == False
    assert window.stack.count() == 6
