"""Application icon helpers for source and frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon


def app_icon_candidates() -> list[Path]:
    candidates: list[Path] = []
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        frozen_assets = Path(frozen_root) / "pypub" / "assets"
        candidates.extend(
            [
                frozen_assets / "app_icon.svg",
                frozen_assets / "app_icon.ico",
            ]
        )
    source_assets = Path(__file__).resolve().parents[1] / "assets"
    candidates.extend(
        [
            source_assets / "app_icon.svg",
            source_assets / "app_icon.ico",
        ]
    )
    return candidates


def load_app_icon() -> QIcon:
    for candidate in app_icon_candidates():
        if candidate.exists():
            icon = QIcon(str(candidate))
            if not icon.isNull():
                return icon
    return QIcon()
