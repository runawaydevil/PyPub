from typing import Literal

EditorMode = Literal["plain", "markdown", "html", "rich_text"]

VALID_EDITOR_MODES: tuple[EditorMode, ...] = ("plain", "markdown", "html", "rich_text")
DEFAULT_EDITOR_MODE: EditorMode = "rich_text"


def normalize_editor_mode(mode: str | None) -> EditorMode:
    if mode in VALID_EDITOR_MODES:
        return mode
    return DEFAULT_EDITOR_MODE


class ContentState:
    """Helper to track state during editor mode swaps."""

    def __init__(self):
        self.current_mode: EditorMode = DEFAULT_EDITOR_MODE
        self.source_text: str = ""
        self.rich_html: str = ""
        self.plain_text: str = ""
