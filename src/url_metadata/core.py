"""
Core functionality for url_metadata, switches on the URLs to request different types of information
saves that to cache. If something has already been requested, returns it from cache.
"""

import os
import logging
from time import sleep
from pathlib import Path
from typing import Optional, Union, Callable, Any, Dict, List

import backoff  # type: ignore[import]
import readability  # type: ignore[import]
from logzero import setup_logger, formatter  # type: ignore[import]
from lassie import Lassie, LassieError  # type: ignore[import]
from appdirs import user_data_dir, user_log_dir  # type: ignore[import]
from requests import Session, Response, PreparedRequest

from .exceptions import URLMetadataException, URLMetadataRequestException
from .cache import MetadataCache
from .model import Metadata
from .utils import normalize_path, fibo_backoff, backoff_warn, clean_url, html_get_text
from .sites import PARSERS
from .sites.abstract import AbstractSite

DEFAULT_LOGLEVEL = logging.WARNING
DEFAULT_SUBTITLE_LANGUAGE = "en"
DEFAULT_SLEEP_TIME = 5


class SaveSession(Session):
    """
    A subclass of requests.Session which runs a callback function
    after each request.

    Allows me to expose the request objects after requests using lassie
    """

    # requests.Session doesn't accept any arguments
    def __init__(self, cb_func: Callable[[Response], None]) -> None:
        """
        cb_func: A callback function which saves the response
        """
        self.cb_func = cb_func
        super().__init__()

    # type annotations for kwargs must specify kwargs for *one* of the kwargs; quite arbitrarily chosen
    # https://stackoverflow.com/a/37032111/9348376
    # https://github.com/psf/requests/blob/4f6c0187150af09d085c03096504934eb91c7a9e/requests/sessions.py#L626
    def send(self, request: PreparedRequest, **kwargs: bool) -> Response:
        """
        Save the latest response for a requests.Session
        """
        resp: Response = super().send(request, **kwargs)  # type: ignore[no-untyped-call]
        self.cb_func(resp)
        return resp


class URLMetadataCache:
    def __init__(
        self,
        loglevel: int = DEFAULT_LOGLEVEL,
        sleep_time: int = DEFAULT_SLEEP_TIME,
        cache_dir: Optional[Union[str, Path]] = None,
        additional_site_parsers: Optional[List[Any]] = None,
        subtitle_language: str = DEFAULT_SUBTITLE_LANGUAGE,
        skip_subtitles: bool = False,
    ) -> None:
        """
        Main interface to the library

        subtitle_language: for youtube subtitle requests
        skip_subtitles: don't attempt to download youtube subtitles
        sleep_time: time to wait between HTTP requests
        cache_dir: location the store cached data
                   uses default user cache directory if not provided
        """

        # handle cache dir
        cdir: Optional[Path] = None
        if cache_dir is not None:
            cdir = normalize_path(cache_dir)
        else:
            cdir = Path(user_data_dir("url_metadata"))

        if cdir.exists() and not cdir.is_dir():
            raise RuntimeError(
                "'cache_dir' '{}' already exists but is not a directory".format(
                    str(cdir)
                )
            )
        if not cdir.exists():
            cdir.mkdir()
        self._base_cache_dir: Path = cdir

        self.cache_dir: Path = self._base_cache_dir / "data"
        if not self.cache_dir.exists():
            self.cache_dir.mkdir()
        self.metadata_cache = MetadataCache(self.cache_dir)

        # setup logging
        self.logger = setup_logger(
            name="url_metadata",
            level=loglevel,
            logfile=self.logpath,
            maxBytes=1e7,
            formatter=formatter(
                "{start}[%(levelname)-7s %(asctime)s %(name)s %(filename)s:%(lineno)d]{end} %(message)s"
            ),
        )

        self.skip_subtitles: bool = skip_subtitles
        self.subtitle_language: str = subtitle_language
        self.sleep_time: int = sleep_time

        ll: Lassie = Lassie()
        # hackery with a requests.Session to save the most recent request object
        ll.client = SaveSession(cb_func=self._save_http_response)
        self.lassie: Lassie = ll

        # default 'last response received' to None
        self._response: Optional[Response] = None

        # initialize site-specific parsers
        self.parser_classes = PARSERS
        if additional_site_parsers is not None:
            for parser in additional_site_parsers:
                if not issubclass(parser, AbstractSite):
                    self.logger.warning(f"{parser} is not a subclass of AbstractSite")
                self.parser_classes.append(parser)

        self.parsers: List[AbstractSite] = [
            asite(umc=self) for asite in self.parser_classes
        ]

    def request_data(self, url: str) -> Metadata:
        """
        Given a URL:

        Uses lassie to grab metadata
        Parses the HTML text with readablity
        uses bs4 to parse that text into a plaintext summary

        Calls each enabled 'site' module, to extract additional information if a site matches the URL
        e.g. If this is a youtube URL, this requests youtube subtitles

        returns all the requested/parsed info as a models.Metdata object
        """
        uurl: str = clean_url(url)
        metadata = Metadata(url=uurl)

        # set self._response, to make sure we're not using stale request information when parsing with readability
        self._response = None

        # try to fetch metadata data with lassie, requests.Session saves the response object using a callback
        # to self._response
        try:
            metadata.info = self._fetch_lassie(uurl)
        except URLMetadataRequestException:
            # failed after waiting 13, 21, 34 seconds successively
            pass

        sleep(self.sleep_time)

        # use readability lib to parse self._response.text
        # if we're at this point, that should always be the latest
        # response, see https://github.com/michaelhelmick/lassie/blob/dd525e6243a989f083534921a1a1206931e608ec/lassie/core.py#L244-L266
        if (
            bool(metadata.info)
            and self._response is not None
            and len(self._response.text) > 0  # type: ignore[unreachable]
        ):
            if self._response.status_code < 400:  # type: ignore[unreachable]
                doc = readability.Document(self._response.text)
                metadata.html_summary = doc.summary()
            else:
                self.logger.warning(
                    f"Response code for {uurl} is {self._response.status_code}, skipping HTML extraction..."
                )

        if metadata.html_summary is not None:
            metadata.text_summary = html_get_text(metadata.html_summary)

        # call hooks for other parsers, if the URL matches
        for parser in self.parsers:
            if parser.matches_site(uurl):
                metadata = parser.extract_info(uurl, metadata)
        return metadata

    @backoff.on_exception(
        fibo_backoff, URLMetadataRequestException, max_tries=3, on_backoff=backoff_warn
    )
    def _fetch_lassie(self, url: str) -> Optional[Dict[str, Any]]:
        self.logger.debug("Fetching metadata for {}".format(url))
        try:
            meta: Dict[str, Any] = self.lassie.fetch(
                url, handle_file_content=True, all_images=True
            )
            return meta
        except LassieError as le:
            self.logger.warning("Could not retrieve metadata from lassie: " + str(le))
        if self._response is not None and self._response.status_code == 429:
            raise URLMetadataRequestException(
                "Received 429 for URL {}, waiting to retry...".format(url)
            )
        return None

    @property
    def logpath(self) -> str:
        """Returns the path to the url_metadata logfile"""
        f = os.path.join(user_log_dir("url_metadata"), "request.log")
        os.makedirs(os.path.dirname(f), exist_ok=True)
        return f

    def _save_http_response(self, resp: Response) -> None:
        """
        callback function to save the most recent request that lassie made
        """
        # do I need to save multiple? lassie makes a HEAD
        # request to get the content type, and then another
        # to get the content, so this should access the
        # response I want; with the main page content
        self._response = resp

    def get(self, url: str) -> Metadata:
        """
        Gets metadata/summary for a URL
        Save the parsed information in a local data directory
        If the URL already has cached data locally, returns that instead
        """
        uurl: str = clean_url(url)
        if not self.in_cache(uurl):
            data: Metadata = self.request_data(uurl)
            self.metadata_cache.put(uurl, data)
            return data
        # returns None if not present
        fdata: Optional[Metadata] = self.metadata_cache.get(uurl)
        if fdata is None:
            raise URLMetadataException(
                f"Failure retrieving information from cache for {url}"
            )
        else:
            return fdata

    def in_cache(self, url: str) -> bool:
        """Returns True if the URL already has cached information"""
        uurl: str = clean_url(url)
        return self.metadata_cache.has(uurl)

    def get_cache_dir(self, url: str) -> Optional[str]:
        """
        If this URL is in cache, returns the location of the cache directory
        Returns None if it couldn't find a matching directory
        """
        uurl: str = clean_url(url)
        try:
            return self.metadata_cache.cache.get(uurl)
        except:
            return None
