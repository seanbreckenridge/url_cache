from typing import List, Any
from .youtube import Youtube

# TODO: add more site-specific parsing here
PARSERS: List[Any] = [Youtube]  # type: ignore
