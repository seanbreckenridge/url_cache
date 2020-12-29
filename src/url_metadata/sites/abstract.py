from typing import Optional
from abc import ABC, abstractmethod

from requests import Response

from ..model import Metadata


class AbstractSite(ABC):
    """
    These are always run after the 'core' lassie/summarization information has been done,
    so these have access to the cached response through self._umc
    """

    def __init__(self, umc):  # type: ignore
        from ..core import URLMetadataCache  # to prevent cyclic imports

        assert isinstance(umc, URLMetadataCache)
        # attach so that classes can inspect options
        self._umc = umc

    @abstractmethod
    def matches_site(self, url: str) -> bool:  # type: ignore[misc]
        """
        Return a boolean describing whether or not some URL matches this site
        """
        raise NotImplementedError

    @abstractmethod
    def extract_info(self, url: str, metadata: Metadata) -> Metadata:  # type: ignore[misc]
        """
        Run requests, extract information from the cached response etc...
        """
        raise NotImplementedError

    @property
    def response(self) -> Optional[Response]:
        return self._umc._response
