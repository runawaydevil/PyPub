import logging
from markdown_it import MarkdownIt

logger = logging.getLogger("pypub.conversion")

class ConversionManager:
    def __init__(self):
        self.md = MarkdownIt('commonmark')

    def markdown_to_html(self, md_source: str) -> str:
        """Render raw markdown to HTML."""
        if not md_source:
            return ""
        try:
            return self.md.render(md_source)
        except Exception as e:
            logger.error(f"Failed to convert MD to HTML: {e}")
            return ""

    def validate_conversion(self, from_mode: str, to_mode: str) -> tuple[bool, str]:
        """
        Determines if a conversion requires warnings/snapshots.
        Returns: (is_destructive, warning_message)
        """
        if to_mode == from_mode:
            return False, ""

        if from_mode == "rich_text" and to_mode in ["markdown", "plain"]:
            return True, "Converting from Rich Text to Markdown/Plain will result in formatting loss. Proceed?"
            
        if from_mode == "html" and to_mode in ["markdown", "plain"]:
            return True, "Converting raw HTML to Markdown/Plain will result in structure loss. Proceed?"

        return False, ""
