from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

LassieMetadata = Dict[str, Any]


@dataclass(init=False)
class Metadata:
    info: LassieMetadata
    html_summary: Optional[str]
    markdown_summary: Optional[str]
    # TODO: better representation in memory, for the .srt file?
    subtitles: Optional[str]
    timestamp: datetime

    def __init__(
        self,
        info: Optional[Dict[str, Any]] = None,
        html_summary: Optional[str] = None,
        markdown_summary: Optional[str] = None,
        subtitles: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):

        self.info = info or {}
        self.html_summary = html_summary or None
        self.markdown_summary = markdown_summary or None
        self.subtitles = subtitles or None
        self.timestamp = timestamp or datetime.now()
