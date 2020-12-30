from typing import List, Any
from .youtube import Youtube

# TODO: add more site-specific extractors here
EXTRACTORS: List[Any] = [Youtube]  # type: ignore
