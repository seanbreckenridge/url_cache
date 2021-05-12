import logging
from typing import Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

from requests import Response

from ..model import Summary


if TYPE_CHECKING:
    from ..core import URLCache  # to prevent cyclic imports


class AbstractSite(ABC):
    """
    These are always run after the 'core' lassie/summarization information has been done,
    so these have access to the cached response through self._uc
    """

    def __init__(self, uc: "URLCache"):
        self._uc = uc

    @abstractmethod
    def matches_site(self, url: str) -> bool:  # type: ignore[misc]
        """
        Return a boolean describing whether or not some URL matches this site extractor
        """
        raise NotImplementedError

    @abstractmethod
    def extract_info(self, url: str, summary: Summary) -> Summary:  # type: ignore[misc]
        """
        Run requests, extract information from the cached response etc...
        """
        raise NotImplementedError

    @abstractmethod
    def preprocess_url(self, url: str) -> str:
        """
        Preprocess/Restructure the URL in some way, to avoid duplicate work
        If it doesn't apply for this URL, you can return the url as its given

        For example, youtube has lots of different ways of structuring a URL
        for a single video, but they all return the same information
        """
        raise NotImplementedError

    @property
    def response(self) -> Optional[Response]:
        return self._uc._response

    @property
    def logger(self) -> logging.Logger:
        return self._uc.logger
