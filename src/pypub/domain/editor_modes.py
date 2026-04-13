from typing import Literal

EditorMode = Literal["plain", "markdown", "html", "rich_text"]

class ContentState:
    """Helper to track state during editor mode swaps."""
    def __init__(self):
        self.current_mode: EditorMode = "plain"
        self.source_text: str = ""
        self.rich_html: str = ""
        self.plain_text: str = ""
