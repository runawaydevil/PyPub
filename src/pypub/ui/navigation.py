"""Stable shell navigation indices — stack order must match these values."""

from __future__ import annotations

from enum import IntEnum


class ShellPage(IntEnum):
    ACCOUNTS = 0
    DRAFTS = 1
    COMPOSE = 2
    SETTINGS = 3
    TECHNICAL = 4
    ABOUT = 5
