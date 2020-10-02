from typing import Dict, Any, Optional
from dataclasses import dataclass

LassieMetadata = Dict[str, Any]


@dataclass
class Metadata:
    info: LassieMetadata = {}
    subtitles: Optional[str] = None
