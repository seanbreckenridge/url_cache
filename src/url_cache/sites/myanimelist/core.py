from typing import Optional, List
from functools import lru_cache

from ...model import Summary
from ...summary_cache import FileParser, _load_file_json, _dump_file_json
from ..abstract import AbstractSite


class MyAnimeList(AbstractSite):
    """
    MyAnimeList site extractor that uses Jikan
    https://jikan.moe/
    """

    def file_parsers(self) -> List[FileParser]:
        return [
            FileParser(
                name="jikan",
                ext=".json",
                load_func=_load_file_json,
                dump_func=_dump_file_json,
            )
        ]

    def matches_site(self, url: str) -> bool:
        pass

    def extract_info(self, url: str, summary: Summary) -> Summary:  # type: ignore[misc]
        pass

    def preprocess_url(self, url: str) -> str:
        pass
