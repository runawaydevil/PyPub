import json
from pathlib import Path
from pydantic import BaseModel


_THEMES = {"light", "dark", "system"}
_DEFAULT_THEME = "light"
_DEFAULT_APPEARANCE_PRESET = "office_light"
_APPEARANCE_PRESET_ALIASES = {
    "writer_nook": _DEFAULT_APPEARANCE_PRESET,
}


def normalize_theme(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    return normalized if normalized in _THEMES else _DEFAULT_THEME


def normalize_appearance_preset(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if not normalized:
        return _DEFAULT_APPEARANCE_PRESET
    return _APPEARANCE_PRESET_ALIASES.get(normalized, normalized)


class AppSettings(BaseModel):
    # General
    theme: str = _DEFAULT_THEME  # light, dark, system
    appearance_preset: str = _DEFAULT_APPEARANCE_PRESET
    autosave_interval_ms: int = 2000
    confirm_on_exit: bool = True

    # Editor
    default_mode: str = "rich_text"
    wrap_lines: bool = True
    split_preview: bool = True
    convert_warning: bool = True
    # ~794px ≈ largura A4 a 96 DPI (210 mm); área útil de escrita confortável
    editor_document_max_width_px: int = 794
    editor_body_font_pt: int = 16
    chrome_font_family: str = "Segoe UI"
    editor_serif_font_family: str = "Georgia"
    editor_mono_font_family: str = "Consolas"
    show_floating_toolbar: bool = True
    enable_slash_menu: bool = True
    default_metadata_collapsed: bool = True
    default_inspector_collapsed: bool = True
    default_preview_mode: str = "hidden"  # hidden | bottom | side
    preview_side_panel_width_px: int = 340
    editor_surface: str = "light"  # light | dark (document area prefers light)

    # Publishing
    confirm_before_publish: bool = True
    warn_missing_alt_text: bool = True
    auto_upload_media: bool = True
    default_account_id: int | None = None
    
    # Privacy & Storage
    keep_deleted_in_trash_days: int = 30
    save_recovery_snapshots: bool = True
    
    # Advanced
    log_level: str = "DEBUG"
    show_technical_tab: bool = False
    http_timeout_sec: int = 30
    preview_limit_size_mb: int = 5


class SettingsManager:
    def __init__(self, config_dir: Path):
        self.config_file = config_dir / "settings.json"
        self.settings = self._load()

    def _load(self) -> AppSettings:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        data["theme"] = normalize_theme(data.get("theme"))
                        data["appearance_preset"] = normalize_appearance_preset(data.get("appearance_preset"))
                    return AppSettings(**data)
            except Exception:
                pass
        return AppSettings()

    def save(self):
        self.settings.theme = normalize_theme(self.settings.theme)
        self.settings.appearance_preset = normalize_appearance_preset(self.settings.appearance_preset)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write(self.settings.model_dump_json(indent=2))
