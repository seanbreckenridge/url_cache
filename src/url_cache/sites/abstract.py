import logging
from typing import Optional, TYPE_CHECKING, List
from abc import ABC, abstractmethod

from requests import Response

from ..model import Summary
from ..summary_cache import FileParser


if TYPE_CHECKING:
    from ..core import URLCache  # to prevent cyclic imports


class AbstractSite(ABC):
    """
    These are always run after the 'core' lassie/summarization information has been done,
    so these have access to the cached response through self._uc
    """

    def __init__(self, uc: "URLCache"):
        self._uc = uc

    def file_parsers(self) -> List[FileParser]:
        """
        Lets Sites specify custom file parsers dynamically in each Site
        Each Site's file_parsers are added to the URLCache when its instantiated
        """
        return []

    @abstractmethod
    def matches_site(self, url: str) -> bool:  # type: ignore[misc]
        """
        Return a boolean describing whether or not some URL matches this site extractor
        """
        raise NotImplementedError

    def extract_info(self, url: str, summary: Summary) -> Summary:
        """
        Run requests, extract information from the cached response etc...
        """
        return summary

    def preprocess_url(self, url: str) -> str:
        """
        Preprocess/Restructure the URL in some way, to avoid duplicate work
        If it doesn't apply for this URL, you can return the url as its given

        For example, youtube has lots of different ways of structuring a URL
        for a single video, but they all return the same information
        """
        return url

    @property
    def response(self) -> Optional[Response]:
        return self._uc._response

    @property
    def logger(self) -> logging.Logger:
        return self._uc.logger

    def sleep(self) -> None:
        self._uc.sleep()
