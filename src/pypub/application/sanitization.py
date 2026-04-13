import nh3

# Default allowlist tailored for basic blog posting safely
ALLOWED_TAGS = {
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'em', 'i', 'li', 'ol',
    'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'hr', 'img', 'figure', 'figcaption',
    'div', 'span', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
}

ALLOWED_ATTRIBUTES = {
    'a': {'href', 'title', 'target'},
    'img': {'src', 'alt', 'title', 'width', 'height', 'loading'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan'},
}

def sanitize_html(html_content: str) -> str:
    """
    Sanitizes HTML strictly for local preview inside PySide6/QTextEdit and before remote submission if desired.
    """
    if not html_content:
        return ""
    
    return nh3.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip_comments=True
    )
