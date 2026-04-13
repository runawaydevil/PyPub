"""Shell stack and sidebar map to ShellPage."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from pypub.ui.navigation import ShellPage
from pypub.ui.shell import MainWindow


def test_shell_stack_page_order(qtbot, mock_managers):
    auth, post, settings, tmp_path = mock_managers
    window = MainWindow(auth, post, settings, tmp_path)
    qtbot.addWidget(window)
    assert window.stack.count() == 6
    assert window.stack.widget(int(ShellPage.ACCOUNTS)) is window.accounts_view
    assert window.stack.widget(int(ShellPage.COMPOSE)) is window.compose_view
    assert window.stack.widget(int(ShellPage.SETTINGS)) is window.settings_panel
    assert window.stack.widget(int(ShellPage.ABOUT)) is window.about_panel


def test_sidebar_item_has_page_role(qtbot, mock_managers):
    auth, post, settings, tmp_path = mock_managers
    window = MainWindow(auth, post, settings, tmp_path)
    qtbot.addWidget(window)
    for row in range(window.sidebar.count()):
        it = window.sidebar.item(row)
        assert it.data(Qt.ItemDataRole.UserRole) is not None
        ShellPage(int(it.data(Qt.ItemDataRole.UserRole)))


def test_refresh_metadata_updates_selected_account(qtbot, mock_managers, test_db, account_factory, monkeypatch):
    auth, post, settings, tmp_path = mock_managers
    account = account_factory()
    account.id = test_db.save_account(account)

    window = MainWindow(auth, post, settings, tmp_path)
    qtbot.addWidget(window)
    window.refresh_accounts()
    window.account_list.setCurrentRow(0)
    window.select_account(window.account_list.currentItem())

    refreshed = account.model_copy(deep=True)
    refreshed.id = account.id
    refreshed.micropub_endpoint = "https://new.example/micropub"
    refreshed.media_endpoint = "https://new.example/media"

    monkeypatch.setattr(auth, "refresh_account_metadata", lambda current: refreshed)
    monkeypatch.setattr(post, "fetch_capabilities", lambda current: type("Caps", (), {"raw_config_json": "{}"})())
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.StandardButton.Ok)

    window._refresh_meta()

    assert "https://new.example/micropub" in window.acc_details.toHtml()
    assert "https://new.example/media" in window.acc_details.toHtml()


def test_remove_account_deletes_local_data(qtbot, mock_managers, test_db, account_factory, monkeypatch):
    auth, post, settings, tmp_path = mock_managers
    account = account_factory()
    account.id = test_db.save_account(account)

    window = MainWindow(auth, post, settings, tmp_path)
    qtbot.addWidget(window)
    window.refresh_accounts()
    window.account_list.setCurrentRow(0)
    window.select_account(window.account_list.currentItem())

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.StandardButton.Ok)

    window._remove_account()

    assert test_db.get_accounts() == []
    assert window.current_account is None
    assert window.account_list.count() == 0
