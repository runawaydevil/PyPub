"""Settings form embedded in the main shell or inside SettingsDialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pypub.domain.settings import SettingsManager


class SettingsPanel(QWidget):
    """Load/save AppSettings via SettingsManager."""

    settingsApplied = Signal()

    def __init__(self, settings_manager: SettingsManager, app_data_dir: Path, parent=None):
        super().__init__(parent)
        self.setObjectName("PageSurface")
        self.settings_manager = settings_manager
        self.app_data_dir = Path(app_data_dir)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(18)
        intro = QWidget()
        intro.setObjectName("SettingsIntro")
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(0, 0, 0, 0)
        intro_layout.setSpacing(4)
        intro_title = QLabel("Adjust application preferences")
        intro_title.setObjectName("PageHeroTitle")
        intro_subtitle = QLabel("Choose the theme, visual preset, and editor defaults for this installation.")
        intro_subtitle.setObjectName("PageHeroSubtitle")
        intro_subtitle.setWordWrap(True)
        intro_layout.addWidget(intro_title)
        intro_layout.addWidget(intro_subtitle)
        root.addWidget(intro)

        tabs = QTabWidget()
        s = settings_manager.settings

        gen_w = QWidget()
        gen_layout = QFormLayout(gen_w)
        self.appearance_combo = QComboBox()
        self.appearance_combo.addItems(["office_light"])
        self.appearance_combo.setCurrentText(s.appearance_preset)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "system"])
        self.theme_combo.setCurrentText(s.theme)
        self.chk_confirm_exit = QCheckBox("Confirm before exit")
        self.chk_confirm_exit.setChecked(s.confirm_on_exit)
        gen_layout.addRow("Visual preset:", self.appearance_combo)
        gen_layout.addRow("Theme:", self.theme_combo)
        gen_layout.addRow(self.chk_confirm_exit)
        tabs.addTab(gen_w, "General")

        ed_w = QWidget()
        ed_layout = QFormLayout(ed_w)
        self.chk_wrap = QCheckBox("Wrap long lines")
        self.chk_wrap.setChecked(s.wrap_lines)
        ed_layout.addRow(self.chk_wrap)

        self.sp_max_width = QSpinBox()
        self.sp_max_width.setRange(480, 1400)
        self.sp_max_width.setSingleStep(20)
        self.sp_max_width.setValue(s.editor_document_max_width_px)
        ed_layout.addRow("Document max width (px):", self.sp_max_width)

        self.sp_body_pt = QSpinBox()
        self.sp_body_pt.setRange(12, 28)
        self.sp_body_pt.setValue(s.editor_body_font_pt)
        ed_layout.addRow("Body font size (pt):", self.sp_body_pt)

        self.ed_chrome_font = QLineEdit(s.chrome_font_family)
        ed_layout.addRow("UI font:", self.ed_chrome_font)

        self.ed_serif_font = QLineEdit(s.editor_serif_font_family)
        ed_layout.addRow("Writing font:", self.ed_serif_font)

        self.ed_mono_font = QLineEdit(s.editor_mono_font_family)
        ed_layout.addRow("Monospace font:", self.ed_mono_font)

        self.chk_floating_tb = QCheckBox("Floating toolbar on text selection")
        self.chk_floating_tb.setChecked(s.show_floating_toolbar)
        ed_layout.addRow(self.chk_floating_tb)

        self.chk_slash = QCheckBox("Slash (/) command menu")
        self.chk_slash.setChecked(s.enable_slash_menu)
        ed_layout.addRow(self.chk_slash)

        self.chk_meta_collapsed = QCheckBox("Start with right drawer collapsed")
        self.chk_meta_collapsed.setChecked(s.default_metadata_collapsed)
        ed_layout.addRow(self.chk_meta_collapsed)

        self.chk_insp_collapsed = QCheckBox("Start with inspector tab hidden")
        self.chk_insp_collapsed.setChecked(s.default_inspector_collapsed)
        ed_layout.addRow(self.chk_insp_collapsed)

        self.preview_mode_combo = QComboBox()
        self.preview_mode_combo.addItems(["hidden", "bottom", "side"])
        self.preview_mode_combo.setCurrentText(s.default_preview_mode)
        ed_layout.addRow("Default preview:", self.preview_mode_combo)

        self.sp_preview_side_w = QSpinBox()
        self.sp_preview_side_w.setRange(240, 560)
        self.sp_preview_side_w.setSingleStep(20)
        self.sp_preview_side_w.setValue(s.preview_side_panel_width_px)
        ed_layout.addRow("Side preview width (px):", self.sp_preview_side_w)

        self.editor_surface_combo = QComboBox()
        self.editor_surface_combo.addItems(["light", "dark"])
        self.editor_surface_combo.setCurrentText(s.editor_surface)
        ed_layout.addRow("Editor surface:", self.editor_surface_combo)

        tabs.addTab(ed_w, "Editor")

        pub_w = QWidget()
        pub_layout = QFormLayout(pub_w)
        self.chk_confirm_pub = QCheckBox("Confirm before publishing")
        self.chk_confirm_pub.setChecked(s.confirm_before_publish)
        pub_layout.addRow(self.chk_confirm_pub)
        tabs.addTab(pub_w, "Publishing")

        priv_w = QWidget()
        priv_layout = QVBoxLayout(priv_w)
        btn_open_data = QPushButton("Open data folder (SQLite / cache)")
        btn_open_data.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.app_data_dir)))
        )
        priv_layout.addWidget(btn_open_data)
        priv_layout.addStretch()
        tabs.addTab(priv_w, "Privacy & Storage")

        adv_w = QWidget()
        adv_layout = QFormLayout(adv_w)
        self.chk_tech = QCheckBox("Show Technical in sidebar")
        self.chk_tech.setChecked(s.show_technical_tab)
        adv_layout.addRow(self.chk_tech)
        tabs.addTab(adv_w, "Advanced")

        root.addWidget(tabs, 1)

        row = QHBoxLayout()
        row.addStretch()
        btn_save = QPushButton("Save preferences")
        btn_save.clicked.connect(self._on_save)
        row.addWidget(btn_save)
        root.addLayout(row)

    def _on_save(self) -> None:
        self.apply_to_manager()
        self.settingsApplied.emit()

    def apply_to_manager(self) -> None:
        s = self.settings_manager.settings
        s.appearance_preset = self.appearance_combo.currentText()
        s.theme = self.theme_combo.currentText()
        s.confirm_on_exit = self.chk_confirm_exit.isChecked()
        s.wrap_lines = self.chk_wrap.isChecked()
        s.confirm_before_publish = self.chk_confirm_pub.isChecked()
        s.show_technical_tab = self.chk_tech.isChecked()
        s.editor_document_max_width_px = self.sp_max_width.value()
        s.editor_body_font_pt = self.sp_body_pt.value()
        s.chrome_font_family = self.ed_chrome_font.text().strip() or "Segoe UI"
        s.editor_serif_font_family = self.ed_serif_font.text().strip() or "Georgia"
        s.editor_mono_font_family = self.ed_mono_font.text().strip() or "Consolas"
        s.show_floating_toolbar = self.chk_floating_tb.isChecked()
        s.enable_slash_menu = self.chk_slash.isChecked()
        s.default_metadata_collapsed = self.chk_meta_collapsed.isChecked()
        s.default_inspector_collapsed = self.chk_insp_collapsed.isChecked()
        s.default_preview_mode = self.preview_mode_combo.currentText()
        s.preview_side_panel_width_px = self.sp_preview_side_w.value()
        s.editor_surface = self.editor_surface_combo.currentText()
        self.settings_manager.save()

    def reload_from_manager(self) -> None:
        s = self.settings_manager.settings
        self.appearance_combo.setCurrentText(s.appearance_preset)
        self.theme_combo.setCurrentText(s.theme)
        self.chk_confirm_exit.setChecked(s.confirm_on_exit)
        self.chk_wrap.setChecked(s.wrap_lines)
        self.chk_confirm_pub.setChecked(s.confirm_before_publish)
        self.chk_tech.setChecked(s.show_technical_tab)
        self.sp_max_width.setValue(s.editor_document_max_width_px)
        self.sp_body_pt.setValue(s.editor_body_font_pt)
        self.ed_chrome_font.setText(s.chrome_font_family)
        self.ed_serif_font.setText(s.editor_serif_font_family)
        self.ed_mono_font.setText(s.editor_mono_font_family)
        self.chk_floating_tb.setChecked(s.show_floating_toolbar)
        self.chk_slash.setChecked(s.enable_slash_menu)
        self.chk_meta_collapsed.setChecked(s.default_metadata_collapsed)
        self.chk_insp_collapsed.setChecked(s.default_inspector_collapsed)
        self.preview_mode_combo.setCurrentText(s.default_preview_mode)
        self.sp_preview_side_w.setValue(s.preview_side_panel_width_px)
        self.editor_surface_combo.setCurrentText(s.editor_surface)
