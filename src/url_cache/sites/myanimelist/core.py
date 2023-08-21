import time
from typing import Optional, List, TYPE_CHECKING, Dict

import requests
import backoff  # type: ignore[import]

from ...model import Summary
from ...summary_cache import FileParser, _load_file_json, _dump_file_json
from ...utils import backoff_warn
from ...common import Json
from ..abstract import AbstractSite

from .urls.v4 import Version4, MalParseResult

if TYPE_CHECKING:
    from ...core import URLCache  # to prevent cyclic imports


class MyAnimeList(AbstractSite):
    """
    MyAnimeList site extractor that uses Jikan
    https://jikan.moe/
    """

    def __init__(self, uc: "URLCache"):
        super().__init__(uc)
        self.url_parser = Version4()
        self.jikan_session = requests.Session()
        self.jikan_sleep_time = 1

    def file_parsers(self) -> List[FileParser[Json]]:
        return [
            FileParser(
                name="jikan",
                ext=".json",
                load_func=_load_file_json,
                dump_func=_dump_file_json,
            )
        ]

    def matches_site(self, url: str) -> bool:
        m: Optional[MalParseResult] = self.url_parser.parse_url(url)
        return m is not None

    def sleep(self) -> None:
        time.sleep(self.jikan_sleep_time)

    @backoff.on_exception(
        backoff.fibo, requests.RequestException, max_tries=3, on_backoff=backoff_warn  # type: ignore[arg-type]
    )
    def _jikan_request(self, url: str) -> Json:
        self.logger.debug(f"Jikan Request: {url}")
        resp = self.jikan_session.get(url)
        self.sleep()
        resp.raise_for_status()
        data: Json = resp.json()
        return data

    def extract_info(self, url: str, summary: Summary) -> Summary:
        m: Optional[MalParseResult] = self.url_parser.parse_url(url)
        if m is None:
            return summary
        data: Dict[str, Json] = {}
        for url in m.jikan_urls:
            try:
                data[url] = self._jikan_request(url)
            except requests.RequestException as r:
                self.logger.warning(str(r))

        summary.data["jikan"] = data

        # html summary is useless since we have all this additional info from jikan
        summary.html_summary = None
        return summary

    def preprocess_url(self, url: str) -> str:
        m: Optional[MalParseResult] = self.url_parser.parse_url(url)
        if m is not None:
            return m.cleaned
        return url
