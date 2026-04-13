import logging
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from pypub.application.auth_service import AuthService
from pypub.application.post_service import PostService
from pypub.ui.about_panel import AboutPanel
from pypub.ui.drafts import DraftsWidget
from pypub.ui.editor.editor_theme import apply_app_theme, apply_shell_sidebar_style
from pypub.ui.login import LoginDialog
from pypub.ui.navigation import ShellPage
from pypub.ui.settings_panel import SettingsPanel
from pypub.ui.technical import TechnicalWidget

logger = logging.getLogger("pypub")


class AccountListRow(QFrame):
    def __init__(self, account, has_token: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("PageCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        name = QLabel(account.display_name)
        name.setObjectName("AccountName")
        layout.addWidget(name)

        url = QLabel(account.me_url)
        url.setObjectName("AccountMeta")
        url.setWordWrap(True)
        layout.addWidget(url)

        status = "Ready" if has_token else "Sign-in required"
        meta = QLabel(status)
        meta.setObjectName("DraftStatus")
        layout.addWidget(meta)


class MainWindow(QMainWindow):
    def __init__(
        self,
        auth_service: AuthService,
        post_service: PostService,
        settings_manager,
        app_data_path: Path,
        app_config_path: Path | None = None,
        app_log_path: Path | None = None,
    ):
        super().__init__()
        self.auth_service = auth_service
        self.post_service = post_service
        self.settings_manager = settings_manager
        self.app_data_path = Path(app_data_path)
        self.app_config_path = Path(app_config_path) if app_config_path else settings_manager.config_file.parent
        self.app_log_path = Path(app_log_path) if app_log_path else self.app_data_path
        self.current_account = None

        self.setWindowTitle("PyPub - Micropub Desktop Client")
        self.resize(1240, 820)

        main_widget = QWidget()
        main_widget.setObjectName("ShellCentral")
        self.setCentralWidget(main_widget)
        h_layout = QHBoxLayout(main_widget)
        h_layout.setContentsMargins(18, 18, 18, 18)
        h_layout.setSpacing(18)

        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("SidebarFrame")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("SidebarHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(16, 16, 16, 16)
        hero_layout.setSpacing(6)
        hero_layout.addWidget(self._make_label("Desktop publishing", "SidebarEyebrow"))
        hero_layout.addWidget(self._make_label("PyPub", "SidebarTitle"))
        subtitle = self._make_label(
            "Draft, review, and publish posts to your site with a clean desktop workflow.",
            "SidebarSubtitle",
        )
        subtitle.setWordWrap(True)
        hero_layout.addWidget(subtitle)
        self.sidebar_account_chip = self._make_label("No account selected", "SidebarAccountChip")
        self.sidebar_account_chip.setWordWrap(True)
        hero_layout.addWidget(self.sidebar_account_chip)
        sidebar_layout.addWidget(hero)

        self.sidebar = QListWidget()
        self.sidebar.setMinimumWidth(168)
        self.sidebar.setMaximumWidth(280)
        apply_shell_sidebar_style(self.sidebar)
        self.sidebar.currentItemChanged.connect(self._on_sidebar_item_changed)
        sidebar_layout.addWidget(self.sidebar, 1)

        self.stack = QStackedWidget()

        self.accounts_view = self._build_accounts_view()
        self.drafts_view = DraftsWidget(self.post_service, str(self.app_data_path))
        self.drafts_view.list_widget.itemDoubleClicked.connect(self._open_draft_in_compose)

        from pypub.ui.editor_workspace import EditorWorkspace

        self.compose_view = EditorWorkspace(self.post_service, str(self.app_data_path), self.settings_manager)

        self.settings_panel = SettingsPanel(self.settings_manager, self.app_data_path, self)
        self.settings_panel.settingsApplied.connect(self._on_settings_applied)

        self.tech_view = TechnicalWidget()

        self.about_panel = AboutPanel(self.app_data_path, self.app_config_path, self.app_log_path, self)

        self.stack.addWidget(self.accounts_view)  # ShellPage.ACCOUNTS
        self.stack.addWidget(self.drafts_view)
        self.stack.addWidget(self.compose_view)
        self.stack.addWidget(self.settings_panel)
        self.stack.addWidget(self.tech_view)
        self.stack.addWidget(self.about_panel)

        h_layout.addWidget(sidebar_frame)
        h_layout.addWidget(self.stack, 1)

        self._build_sidebar_items()
        self.refresh_accounts()

    def _build_sidebar_items(self) -> None:
        prev: ShellPage | None = None
        cur = self.sidebar.currentItem()
        if cur is not None and cur.data(Qt.ItemDataRole.UserRole) is not None:
            prev = ShellPage(int(cur.data(Qt.ItemDataRole.UserRole)))

        self.sidebar.blockSignals(True)
        self.sidebar.clear()
        for label, page in [
            ("Accounts", ShellPage.ACCOUNTS),
            ("Drafts", ShellPage.DRAFTS),
            ("Compose", ShellPage.COMPOSE),
            ("Settings", ShellPage.SETTINGS),
            ("Technical", ShellPage.TECHNICAL),
            ("About", ShellPage.ABOUT),
        ]:
            if page == ShellPage.TECHNICAL and not self.settings_manager.settings.show_technical_tab:
                continue
            it = QListWidgetItem(label)
            it.setData(Qt.ItemDataRole.UserRole, int(page))
            self.sidebar.addItem(it)
        self.sidebar.blockSignals(False)

        target = prev or ShellPage.ACCOUNTS
        if target == ShellPage.TECHNICAL and not self.settings_manager.settings.show_technical_tab:
            target = ShellPage.SETTINGS
        self._select_sidebar_page(target)

    def _on_sidebar_item_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        raw = current.data(Qt.ItemDataRole.UserRole)
        if raw is None:
            return
        page = ShellPage(int(raw))
        if page in (ShellPage.DRAFTS, ShellPage.COMPOSE):
            if not self.current_account:
                QMessageBox.warning(self, "No account", "Select an account first.")
                self._select_sidebar_page(ShellPage.ACCOUNTS)
                return
        self.stack.setCurrentIndex(int(page))

    def _select_sidebar_page(self, page: ShellPage) -> None:
        for row in range(self.sidebar.count()):
            it = self.sidebar.item(row)
            if it and it.data(Qt.ItemDataRole.UserRole) == int(page):
                self.sidebar.setCurrentRow(row)
                return

    def _on_settings_applied(self) -> None:
        apply_app_theme(QApplication.instance(), self.settings_manager.settings)
        self.compose_view.apply_settings_after_save()
        self._build_sidebar_items()
        self._select_sidebar_page(ShellPage.SETTINGS)

    def _open_draft_in_compose(self, item):
        draft_id = item.data(Qt.ItemDataRole.UserRole)
        if draft_id is None:
            return
        if not self.current_account:
            QMessageBox.warning(self, "No account", "Select an account first.")
            return
        d = self.post_service.get_draft_by_id(self.current_account.id, int(draft_id))
        if d is None:
            QMessageBox.warning(self, "Draft", "Draft not found.")
            return
        self.compose_view.load_draft(d)
        self._select_sidebar_page(ShellPage.COMPOSE)

    def _build_accounts_view(self) -> QWidget:
        w = QWidget()
        w.setObjectName("PageSurface")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.addWidget(self._page_intro(
            "Connect a publishing account",
            "Select an account, refresh its endpoints, and manage local access from one place.",
        ))

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = QFrame()
        left.setObjectName("PageCard")
        l_layout = QVBoxLayout(left)
        l_layout.setContentsMargins(18, 18, 18, 18)
        l_layout.setSpacing(14)
        l_layout.addWidget(self._make_label("Available accounts", "SectionTitle"))
        hint = self._make_label("Manage one or more IndieAuth accounts for publishing.", "SectionHint")
        hint.setWordWrap(True)
        l_layout.addWidget(hint)
        self.account_list = QListWidget()
        self.account_list.itemClicked.connect(self.select_account)
        l_layout.addWidget(self.account_list)

        btn_add = QPushButton("Add account")
        btn_add.setObjectName("PrimaryAction")
        btn_add.clicked.connect(self.add_account)
        l_layout.addWidget(btn_add)
        splitter.addWidget(left)

        right = QFrame()
        right.setObjectName("DetailCard")
        r_layout = QVBoxLayout(right)
        r_layout.setContentsMargins(18, 18, 18, 18)
        r_layout.setSpacing(14)
        r_layout.addWidget(self._make_label("Account details", "SectionTitle"))
        detail_hint = self._make_label(
            "Review endpoints, permissions, and local session status.",
            "SectionHint",
        )
        detail_hint.setWordWrap(True)
        r_layout.addWidget(detail_hint)
        self.acc_details = QTextBrowser()
        self.acc_details.setObjectName("AccountDetailsBrowser")
        r_layout.addWidget(self.acc_details)

        btn_refresh = QPushButton("Refresh metadata")
        btn_refresh.clicked.connect(self._refresh_meta)
        btn_revoke = QPushButton("Remove local session")
        btn_revoke.clicked.connect(self._revoke_session)
        btn_remove = QPushButton("Remove account completely")
        btn_remove.setObjectName("DangerAction")
        btn_remove.clicked.connect(self._remove_account)

        r_layout.addWidget(btn_refresh)
        r_layout.addWidget(btn_revoke)
        r_layout.addWidget(btn_remove)
        splitter.addWidget(right)

        layout.addWidget(splitter)
        return w

    def refresh_accounts(self):
        previous_id = self.current_account.id if self.current_account else None
        self.account_list.clear()
        for acc in self.auth_service.get_accounts():
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, acc.id)
            item.setSizeHint(QSize(0, 92))
            self.account_list.addItem(item)
            self.account_list.setItemWidget(
                item,
                AccountListRow(acc, self.auth_service.keyring_store.get_token(acc.id) is not None, self.account_list),
            )

        self.current_account = None
        if previous_id is not None:
            for row in range(self.account_list.count()):
                item = self.account_list.item(row)
                if item and item.data(Qt.ItemDataRole.UserRole) == previous_id:
                    self.account_list.setCurrentRow(row)
                    self.select_account(item)
                    return

        if self.account_list.count() == 0:
            self.sidebar_account_chip.setText("No account selected")
            self.acc_details.setHtml(
                "<h3>No account connected</h3>"
                "<p>Add a site to view its publishing endpoints, scopes, and local session status here.</p>"
            )
            self.drafts_view.set_account(None)
            self.compose_view.account = None
            return

    def select_account(self, item):
        if item is None:
            self.current_account = None
            self.sidebar_account_chip.setText("No account selected")
            self.acc_details.setHtml("<p>No account selected.</p>")
            self.drafts_view.set_account(None)
            self.compose_view.account = None
            return

        account_id = item.data(Qt.ItemDataRole.UserRole)
        accounts = {acc.id: acc for acc in self.auth_service.get_accounts()}
        selected = accounts.get(account_id)
        if selected is None:
            self.current_account = None
            self.sidebar_account_chip.setText("No account selected")
            self.acc_details.setHtml("<p>Account not found.</p>")
            return

        self.current_account = selected
        self.drafts_view.set_account(self.current_account)
        self.compose_view.set_account(self.current_account)
        logger.info("Selected account: %s", self.current_account.me_url)
        self._render_current_account()

        try:
            caps = self.post_service.fetch_capabilities(self.current_account)
            self.tech_view.log(f"Capabilities: {caps.raw_config_json}")
            self._render_current_account()
        except Exception as e:
            self.tech_view.log(f"Capabilities failed: {e}")

    def _render_current_account(self) -> None:
        if not self.current_account:
            self.acc_details.setHtml("<p>No account selected.</p>")
            return

        details = f"<h3>{self.current_account.display_name}</h3>"
        details += f"<p><b>Me URL:</b> {self.current_account.me_url}</p>"
        details += f"<p><b>Micropub:</b> {self.current_account.micropub_endpoint}</p>"
        details += f"<p><b>Media:</b> {self.current_account.media_endpoint or 'Not discovered'}</p>"
        details += f"<p><b>Scopes:</b> {self.current_account.scopes_granted or 'None'}</p>"

        has_token = self.auth_service.keyring_store.get_token(self.current_account.id) is not None
        details += f"<p><b>Local token:</b> {'Available' if has_token else 'Sign-in required'}</p>"
        self.sidebar_account_chip.setText(
            f"Account: {self.current_account.display_name}"
        )
        self.acc_details.setHtml(details)

    def _refresh_meta(self):
        if not self.current_account:
            return
        try:
            self.current_account = self.auth_service.refresh_account_metadata(self.current_account)
            self._render_current_account()
            try:
                caps = self.post_service.fetch_capabilities(self.current_account)
                self.tech_view.log(f"Capabilities refreshed: {caps.raw_config_json}")
            except Exception as exc:
                self.tech_view.log(f"Capabilities refresh failed: {exc}")
            QMessageBox.information(self, "Metadata", "Account metadata updated.")
        except Exception as exc:
            QMessageBox.critical(self, "Metadata", f"Refresh failed: {exc}")

    def _revoke_session(self):
        if not self.current_account:
            return
        self.auth_service.keyring_store.delete_token(self.current_account.id)
        self._render_current_account()
        QMessageBox.warning(
            self,
            "Session removed",
            "The local token was removed from this device. Sign in again to continue publishing.",
        )

    def _remove_account(self):
        if not self.current_account:
            return
        rep = QMessageBox.question(
            self,
            "Remove account",
            "Remove this account from PyPub and delete its local drafts?",
        )
        if rep == QMessageBox.StandardButton.Yes:
            account_id = self.current_account.id
            self.auth_service.remove_account(account_id)
            self.current_account = None
            self.acc_details.setHtml("<p>No account selected.</p>")
            self.drafts_view.set_account(None)
            self.compose_view.account = None
            self.refresh_accounts()
            QMessageBox.information(
                self,
                "Account removed",
                "The account and its local drafts were removed from this device.",
            )

    def add_account(self):
        dialog = LoginDialog(self.auth_service, self)
        if dialog.exec():
            self.refresh_accounts()
            if self.account_list.count() > 0:
                self.account_list.setCurrentRow(self.account_list.count() - 1)
                self.select_account(self.account_list.currentItem())

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.settings_manager.settings.confirm_on_exit:
            reply = QMessageBox.question(
                self,
                "Exit PyPub",
                "Close PyPub now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        super().closeEvent(event)

    def _make_label(self, text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        return label

    def _page_intro(self, title: str, subtitle: str) -> QWidget:
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        title_lbl = self._make_label(title, "PageHeroTitle")
        sub_lbl = self._make_label(subtitle, "PageHeroSubtitle")
        sub_lbl.setWordWrap(True)
        lay.addWidget(title_lbl)
        lay.addWidget(sub_lbl)
        return box
