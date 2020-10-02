import sqlite
from typing import Optional
from pathlib import Path

from .model import Metadata

# maintain an sqlite database which handles mapping
# URLs to IDs. The IDs correspond to the file location


class Index:
    def __init__(self, loc: Path):
        pass

    @staticmethod
    def has_null_value(self, url: str) -> bool:
        """
        If the item isn't in cache, returns True
        If the item is in cache, but it doesn't have any values (i.e. empty
        json file and no srt data), then return True
        else return False (this has data)
        """
        pass

    def get(self, url: str) -> Optional[Metadata]:
        """
        Get data for the 'url' from cache, or None
        """
        pass

    def exists(self, url: str) -> bool:
        """
        Returns true/false, signifying whether or not the information
        for this url is already cached
        """
        return False

    def put(self, url: str) -> None:
        pass

    # not used but here as a library function, incase
    def delete(self, url: str) -> bool:
        """
        Returns true if item was deleted, false if it didn't exist
        """
        pass
