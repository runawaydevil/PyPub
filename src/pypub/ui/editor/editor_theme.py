"""Central visual tokens and QSS for PyPub."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication

from pypub.domain.settings import AppSettings


def _effective_dark(settings: AppSettings) -> bool:
    if settings.theme == "dark":
        return True
    if settings.theme == "light":
        return False
    try:
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return False


def _tokens(settings: AppSettings) -> dict[str, str]:
    if _effective_dark(settings):
        tokens = {
            "window": "#16191f",
            "panel": "#1d222a",
            "panel_soft": "#232a33",
            "surface": "#2a313c",
            "surface_2": "#313949",
            "paper": "#20252d",
            "border": "#46505f",
            "border_soft": "#3a4452",
            "text": "#eef2f7",
            "text_soft": "#c5ceda",
            "text_faint": "#96a3b6",
            "accent": "#5b9df0",
            "accent_soft": "#233a5a",
            "accent_deep": "#7ab0f3",
            "success": "#4fa06e",
            "danger": "#d97a7a",
            "selection": "#244770",
            "preview_bg": "#1d222a",
            "preview_text": "#eef2f7",
            "on_accent": "#ffffff",
        }
    else:
        tokens = {
            "window": "#f3f4f6",
            "panel": "#eceff3",
            "panel_soft": "#f7f8fa",
            "surface": "#ffffff",
            "surface_2": "#f4f7fb",
            "paper": "#ffffff",
            "border": "#d3d9e2",
            "border_soft": "#e3e8ef",
            "text": "#1f2937",
            "text_soft": "#5b6575",
            "text_faint": "#7c8798",
            "accent": "#2b78d6",
            "accent_soft": "#e9f2fd",
            "accent_deep": "#1f5fae",
            "success": "#2f7d57",
            "danger": "#b74a4a",
            "selection": "#d7e8fd",
            "preview_bg": "#fbfcfe",
            "preview_text": "#1f2937",
            "on_accent": "#ffffff",
        }

    if settings.editor_surface == "dark":
        tokens["paper"] = "#1f252d"
        tokens["preview_bg"] = "#1f252d"
        tokens["preview_text"] = "#eef2f7"
        tokens["text_editor"] = "#eef2f7"
        tokens["summary_bg"] = "#252c36"
    else:
        tokens["text_editor"] = tokens["text"]
        tokens["summary_bg"] = tokens["surface_2"]

    return tokens


def _compose_document_qss(settings: AppSettings, t: dict[str, str]) -> str:
    pt = settings.editor_body_font_pt
    serif = settings.editor_serif_font_family
    mono = settings.editor_mono_font_family
    return f"""
    QWidget#ComposeWorkspace {{
        background: transparent;
    }}
    QWidget#ComposeHeader {{
        background: {t["surface"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 10px;
        margin: 12px 18px 0 18px;
    }}
    QLabel#ComposeKicker {{
        color: {t["accent"]};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }}
    QLabel#ComposeHeaderAccount {{
        color: {t["text"]};
        font-size: 18px;
        font-weight: 600;
    }}
    QLabel#ComposeHeaderMode, QLabel#ComposeHeaderStatus, QLabel#ComposeHeaderHint {{
        color: {t["text_soft"]};
        font-size: 12px;
    }}
    QPushButton#ComposePublishButton {{
        background: {t["accent"]};
        color: {t["on_accent"]};
        border-color: {t["accent"]};
        font-weight: 700;
    }}
    QPushButton#ComposePublishButton:hover {{
        background: {t["accent_deep"]};
        border-color: {t["accent_deep"]};
    }}
    QWidget#FormatToolbar {{
        background: {t["panel_soft"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 10px;
        margin: 10px 18px 10px 18px;
    }}
    QLabel#ToolbarGroupLabel {{
        color: {t["text_faint"]};
        font-size: 11px;
        font-weight: 700;
        padding: 0 4px;
    }}
    QToolButton#FormatChip {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 6px 10px;
        color: {t["text_soft"]};
    }}
    QToolButton#FormatChip:hover {{
        background: {t["surface_2"]};
        border-color: {t["border"]};
        color: {t["text"]};
    }}
    QWidget#FloatingFormatBar {{
        background: {t["text"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 8px;
    }}
    QToolButton#FloatingFormatButton {{
        color: {t["surface"]};
        border: none;
        padding: 6px 10px;
        font-weight: 600;
        border-radius: 6px;
    }}
    QToolButton#FloatingFormatButton:hover {{
        background: rgba(255, 255, 255, 0.16);
    }}
    QWidget#DocumentCard {{
        background-color: {t["paper"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 12px;
    }}
    QLineEdit#DocTitle {{
        font-family: "{serif}";
        font-size: 30px;
        font-weight: 600;
        border: none;
        border-bottom: 1px solid {t["border_soft"]};
        padding: 12px 4px 14px 4px;
        background: {t["paper"]};
        color: {t["text_editor"]};
    }}
    QLineEdit#DocTitle[articleTitle="true"] {{
        font-size: 34px;
        font-weight: 700;
    }}
    QPlainTextEdit#DocSummary {{
        font-family: "{serif}";
        font-size: 15px;
        color: {t["text_soft"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 8px;
        padding: 10px 12px;
        background: {t["summary_bg"]};
    }}
    QTextEdit#DocumentEditor {{
        background-color: {t["paper"]};
        color: {t["text_editor"]};
        font-family: "{serif}";
        font-size: {pt}px;
        selection-background-color: {t["selection"]};
        border: none;
        padding: 24px 32px 52px 32px;
    }}
    QLabel#PresetChip {{
        color: {t["accent"]};
        font-size: 11px;
        font-weight: 700;
        padding: 4px 10px;
        background: {t["accent_soft"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 999px;
    }}
    QLabel#ContextStatus {{
        color: {t["text_faint"]};
        font-size: 12px;
    }}
    QFrame#PresetUrlBlock, QFrame#PhotoPresetStrip {{
        background: {t["panel_soft"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 10px;
    }}
    QLabel#PresetHint {{
        color: {t["text_soft"]};
        font-size: 12px;
    }}
    QWidget#DrawerPanel {{
        background-color: {t["panel_soft"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 12px;
        margin: 0 18px 18px 8px;
    }}
    QLabel#DrawerTitle {{
        color: {t["text"]};
        font-size: 15px;
        font-weight: 600;
    }}
    QLabel#DrawerSubtitle {{
        color: {t["text_soft"]};
        font-size: 12px;
    }}
    QToolButton#DrawerToggle {{
        border: 1px solid {t["border"]};
        border-radius: 8px;
        padding: 6px 12px;
        background: {t["surface"]};
        color: {t["text"]};
    }}
    QToolButton#DrawerToggle:hover {{
        background: {t["surface_2"]};
        border-color: {t["accent"]};
    }}
    QFrame#BottomPanel {{
        background-color: {t["panel_soft"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 12px;
        margin: 0 18px 18px 18px;
    }}
    QTextBrowser#PreviewReading {{
        background-color: {t["preview_bg"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 10px;
        padding: 18px;
        font-family: "{serif}";
        font-size: 15px;
        color: {t["preview_text"]};
    }}
    QTextEdit#InspectorLog {{
        background-color: {t["surface"]};
        color: {t["text_soft"]};
        font-family: "{mono}";
        font-size: 11px;
        border: 1px solid {t["border_soft"]};
        border-radius: 8px;
    }}
    """


def _chrome_shell_qss(settings: AppSettings, t: dict[str, str]) -> str:
    return f"""
    QMainWindow, QWidget#ShellCentral {{
        background-color: {t["window"]};
    }}
    QWidget#SidebarFrame {{
        background: {t["panel"]};
        border-right: 1px solid {t["border_soft"]};
    }}
    QWidget#SidebarHero {{
        background: {t["surface"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 10px;
    }}
    QLabel#SidebarEyebrow {{
        color: {t["accent"]};
        font-size: 11px;
        font-weight: 700;
    }}
    QLabel#SidebarTitle {{
        color: {t["text"]};
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel#SidebarSubtitle, QLabel#SidebarAccountChip {{
        color: {t["text_soft"]};
        font-size: 12px;
    }}
    QLabel#SidebarAccountChip {{
        background: {t["panel_soft"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 999px;
        padding: 7px 10px;
    }}
    QListWidget#AppNav {{
        background-color: transparent;
        border: none;
        padding: 8px 0;
        font-size: 13px;
        outline: none;
        color: {t["text"]};
    }}
    QListWidget#AppNav::item {{
        padding: 12px 14px;
        margin: 3px 0;
        border-radius: 8px;
        color: {t["text_soft"]};
    }}
    QListWidget#AppNav::item:selected {{
        background-color: {t["accent_soft"]};
        color: {t["accent"]};
        border: 1px solid {t["accent"]};
        font-weight: 700;
    }}
    QListWidget#AppNav::item:hover:!selected {{
        background-color: {t["surface_2"]};
        color: {t["text"]};
    }}
    QWidget#PageSurface {{
        background: {t["panel_soft"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 14px;
        margin: 16px 18px 18px 0;
    }}
    QWidget#PageCard, QWidget#DetailCard, QWidget#EmptyCard {{
        background: {t["surface"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 10px;
    }}
    QLabel#PageHeroTitle {{
        color: {t["text"]};
        font-size: 26px;
        font-weight: 700;
    }}
    QLabel#PageHeroSubtitle {{
        color: {t["text_soft"]};
        font-size: 13px;
    }}
    QLabel#SectionTitle {{
        color: {t["text"]};
        font-size: 16px;
        font-weight: 600;
    }}
    QLabel#SectionHint, QLabel#EmptyBody, QLabel#CardMeta, QLabel#AccountMeta {{
        color: {t["text_soft"]};
        font-size: 12px;
    }}
    QLabel#EmptyTitle {{
        color: {t["text"]};
        font-size: 18px;
        font-weight: 600;
    }}
    QLabel#AccountName, QLabel#DraftTitle {{
        color: {t["text"]};
        font-size: 15px;
        font-weight: 600;
    }}
    QLabel#DraftMeta, QLabel#DraftStatus, QLabel#MediaMeta, QLabel#MediaWarning, QLabel#AccountMeta {{
        color: {t["text_soft"]};
        font-size: 12px;
    }}
    QLabel#DraftStatus {{
        color: {t["accent"]};
        font-weight: 700;
    }}
    QLabel#MediaWarning {{
        color: {t["danger"]};
        font-weight: 700;
    }}
    QFrame#MediaCard {{
        background: {t["surface"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 10px;
    }}
    QLabel#MediaThumb {{
        background: {t["panel_soft"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 8px;
        color: {t["text_faint"]};
        font-weight: 700;
    }}
    QLabel#MediaEmbedBadge {{
        color: {t["accent"]};
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        background: {t["accent_soft"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 999px;
    }}
    QTextBrowser#AccountDetailsBrowser, QTextEdit#TechnicalLog {{
        background: {t["surface"]};
        color: {t["text"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 10px;
        padding: 14px;
    }}
    """


def _global_control_qss(settings: AppSettings, t: dict[str, str]) -> str:
    chrome = settings.chrome_font_family
    return f"""
    QWidget {{
        color: {t["text"]};
    }}
    QLabel {{
        color: {t["text"]};
    }}
    QPushButton {{
        background-color: {t["surface"]};
        color: {t["text"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        padding: 8px 14px;
        min-height: 18px;
    }}
    QPushButton:hover {{
        background-color: {t["surface_2"]};
        border-color: {t["accent"]};
    }}
    QPushButton:pressed {{
        background-color: {t["accent_soft"]};
    }}
    QPushButton:disabled {{
        color: {t["text_faint"]};
        background-color: {t["panel_soft"]};
        border-color: {t["border_soft"]};
    }}
    QPushButton#PrimaryAction {{
        background-color: {t["accent"]};
        color: {t["on_accent"]};
        border-color: {t["accent"]};
        font-weight: 700;
    }}
    QPushButton#PrimaryAction:hover {{
        background-color: {t["accent_deep"]};
        border-color: {t["accent_deep"]};
    }}
    QPushButton#DangerAction {{
        color: {t["danger"]};
        border-color: {t["border"]};
    }}
    QPushButton#DangerAction:hover {{
        border-color: {t["danger"]};
        background-color: {t["surface_2"]};
    }}
    QToolButton {{
        color: {t["text"]};
        background-color: transparent;
        padding: 5px 10px;
        border-radius: 8px;
    }}
    QToolButton:hover {{
        background-color: {t["surface_2"]};
    }}
    QComboBox, QLineEdit, QSpinBox, QTextEdit, QPlainTextEdit, QTextBrowser {{
        background-color: {t["surface"]};
        color: {t["text"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        padding: 7px 10px;
        selection-background-color: {t["selection"]};
    }}
    QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus, QTextBrowser:focus {{
        border-color: {t["accent"]};
    }}
    QComboBox QAbstractItemView {{
        background-color: {t["surface"]};
        color: {t["text"]};
        selection-background-color: {t["selection"]};
        border: 1px solid {t["border_soft"]};
    }}
    QListWidget, QListView {{
        background-color: {t["surface"]};
        color: {t["text"]};
        border: 1px solid {t["border_soft"]};
        border-radius: 10px;
        padding: 8px;
    }}
    QListWidget::item:selected, QListView::item:selected {{
        background-color: transparent;
        color: {t["text"]};
    }}
    QCheckBox {{
        color: {t["text"]};
        spacing: 8px;
    }}
    QTabWidget::pane {{
        border: 1px solid {t["border_soft"]};
        background-color: {t["panel_soft"]};
        border-radius: 10px;
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {t["text_soft"]};
        padding: 10px 16px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    QTabBar::tab:selected {{
        background: {t["surface"]};
        color: {t["text"]};
        border: 1px solid {t["border_soft"]};
        border-bottom: 0;
        font-weight: 700;
    }}
    QTabBar::tab:hover:!selected {{
        background: {t["surface_2"]};
    }}
    QSplitter::handle {{
        background-color: {t["window"]};
        width: 8px;
        height: 8px;
    }}
    QMenu {{
        background: {t["surface"]};
        border: 1px solid {t["border_soft"]};
        padding: 6px;
    }}
    QMenu::item {{
        padding: 6px 18px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background: {t["accent_soft"]};
        color: {t["accent"]};
    }}
    QToolTip {{
        background: {t["surface"]};
        color: {t["text"]};
        border: 1px solid {t["border_soft"]};
        padding: 6px 8px;
    }}
    * {{
        font-family: "{chrome}";
    }}
    """


def _apply_palette(app: QApplication, t: dict[str, str]) -> None:
    pal = QPalette(app.palette())
    pal.setColor(QPalette.ColorRole.Window, QColor(t["window"]))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
    pal.setColor(QPalette.ColorRole.Base, QColor(t["surface"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(t["panel_soft"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
    pal.setColor(QPalette.ColorRole.Button, QColor(t["surface"]))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(t["text"]))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(t["selection"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(t["text"]))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(t["text_faint"]))
    app.setPalette(pal)


def apply_app_theme(app: QApplication, settings: AppSettings) -> None:
    t = _tokens(settings)
    _apply_palette(app, t)
    app.setStyleSheet(
        _chrome_shell_qss(settings, t)
        + "\n"
        + _global_control_qss(settings, t)
        + "\n"
        + _compose_document_qss(settings, t)
    )
    font = QFont(settings.chrome_font_family or "Segoe UI", 10)
    app.setFont(font)


def apply_shell_sidebar_style(sidebar) -> None:
    sidebar.setObjectName("AppNav")


def app_chrome_stylesheet(settings: AppSettings) -> str:
    t = _tokens(settings)
    return _chrome_shell_qss(settings, t) + "\n" + _global_control_qss(settings, t)
