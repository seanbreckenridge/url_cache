from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

import srt  # type: ignore[import]

Subtitles = List[srt.Subtitle]


@dataclass(init=False)
class Metadata:
    """
    Represents all possible data for a URL

    URL
    Info (description, images, page metadata)
    HTML Summary
    Subtitles (from youtube)
    Timestamp (when this information was scraped)
    """

    url: str
    info: Dict[str, Any]
    html_summary: Optional[str]
    subtitles: Optional[Subtitles]
    timestamp: Optional[datetime]

    def __init__(
        self,
        url: str,
        info: Optional[Dict[str, Any]] = None,
        html_summary: Optional[str] = None,
        subtitles: Optional[Subtitles] = None,
        timestamp: Optional[datetime] = None,
    ):

        self.info = info or {}
        self.url = url
        self.html_summary = html_summary or None
        self.subtitles = subtitles
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "info": self.info,
            "html_summary": self.html_summary,
            "subtitles": srt.compose(self.subtitles) if self.subtitles else None,
            "timestamp": int(self.timestamp.timestamp()) if self.timestamp else None,
        }
