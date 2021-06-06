from typing import List, Type
from .abstract import AbstractSite
from .youtube.core import Youtube
from .stackoverflow import StackOverflow
from .myanimelist.core import MyAnimeList

# As this is a namespace package, you're free to add additional files
# to this package in a separate directory, and then append them (or override this file, by
# placing your namespace package before this on your PYTHONPATH),
# to this list, and they'd be added to the global list in the rest of the library
#
# for more information, see:
# https://www.python.org/dev/peps/pep-0420/#dynamic-path-computation
# https://packaging.python.org/guides/creating-and-discovering-plugins/#using-namespace-packages
# https://packaging.python.org/guides/packaging-namespace-packages/
# https://github.com/seanbreckenridge/reorder_editable

# TODO: add more site-specific extractors here
EXTRACTORS: List[Type[AbstractSite]] = [Youtube, StackOverflow, MyAnimeList]
