import json
from pathlib import Path
from pydantic import BaseModel

class AppSettings(BaseModel):
    # General
    theme: str = "system" # light, dark, system
    autosave_interval_ms: int = 2000
    confirm_on_exit: bool = True

    # Editor
    default_mode: str = "rich_text"
    wrap_lines: bool = True
    split_preview: bool = True
    convert_warning: bool = True

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
                    return AppSettings(**data)
            except Exception:
                pass
        return AppSettings()

    def save(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write(self.settings.model_dump_json(indent=2))
