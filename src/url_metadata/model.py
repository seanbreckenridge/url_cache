from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass(init=False)
class Metadata:
    info: Dict[str, Any]
    url: str
    html_summary: Optional[str]
    text_summary: Optional[str]
    # TODO: better representation in memory, for the .srt file?
    subtitles: Optional[str]
    timestamp: datetime

    def __init__(
        self,
        url: str,
        info: Optional[Dict[str, Any]] = None,
        html_summary: Optional[str] = None,
        text_summary: Optional[str] = None,
        subtitles: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):

        self.info = info or {}
        self.url = url
        self.html_summary = html_summary or None
        self.text_summary = text_summary or None
        self.subtitles = subtitles or None
        self.timestamp = timestamp or datetime.now()
