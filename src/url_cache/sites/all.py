from typing import List, Type
from .abstract import AbstractSite
from .youtube.core import Youtube

# TODO: add more site-specific extractors here
EXTRACTORS: List[Type[AbstractSite]] = [Youtube]
