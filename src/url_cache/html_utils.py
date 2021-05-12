"""
Methods to parse HTML
"""

import readability  # type: ignore[import]

from .exceptions import URLCacheException


def summarize_html(
    html_text: str,
) -> str:
    """
    Uses readability to summarize the HTML response into a summary
    """
    if html_text.strip() == "":
        raise URLCacheException("No html provided to summarize")
    doc: readability.Document = readability.Document(html_text)
    summary: str = doc.summary()
    return summary
