"""
Core functionality for url_metadata, switches on the URLs to request different types of information
saves that to cache. If something has already been requested, returns it from cache.
"""

import os
import logging
from time import sleep
from pathlib import Path
from typing import Optional, Union, Callable, Any, Dict

import backoff  # type: ignore
import readability  # type: ignore
from logzero import setup_logger, formatter  # type: ignore
from lassie import Lassie, LassieError  # type: ignore
from appdirs import user_data_dir, user_log_dir  # type: ignore
from requests import Session, Response

from .exceptions import URLMetadataException, URLMetadataRequestException
from .cache import MetadataCache
from .model import Metadata
from .utils import normalize_path, fibo_backoff, backoff_warn, clean_url, html_get_text
from .youtube import download_subtitles, get_yt_video_id, YoutubeException

DEFAULT_LOGLEVEL = logging.WARNING
DEFAULT_SUBTITLE_LANGUAGE = "en"
DEFAULT_SLEEP_TIME = 5


class SaveSession(Session):
    """
    A subclass of requests.Session which runs a callback function
    after each request.

    Allows me to expose the request objects after requests using lassie
    """

    def __init__(self, cb_func: Callable[[Response], None], *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """
        cb_func: A callback function which saves the response
        """
        self.cb_func = cb_func
        super().__init__(*args, **kwargs)  # type: ignore[call-arg]

    def send(self, *args, **kwargs) -> Response:  # type: ignore[no-untyped-def]
        """
        Save the latest response for a requests.Session
        """
        resp: Response = super().send(*args, **kwargs)  # type: ignore[no-untyped-call]
        self.cb_func(resp)
        return resp


class URLMetadataCache:
    def __init__(
        self,
        loglevel: int = DEFAULT_LOGLEVEL,
        subtitle_language: str = DEFAULT_SUBTITLE_LANGUAGE,
        sleep_time: int = DEFAULT_SLEEP_TIME,
        cache_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Main interface to the library

        Supply 'cache_dir' to overwrite the default location.
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

        self.subtitle_language: str = subtitle_language
        self.sleep_time: int = sleep_time

        ll: Lassie = Lassie()
        # hackery with a requests.Session to save the most recent request object
        ll.client = SaveSession(cb_func=self._save_http_response)
        self.lassie: Lassie = ll

        # default 'last response received' to None
        self._response: Optional[Response] = None

    def get(self, url: str) -> Metadata:
        """
        Gets metadata/summary for a URL.
        Save the parsed information in a local data directory
        If the URL already has cached data locally, returns that instead.
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

    def request_data(self, url: str) -> Metadata:
        """
        Given a URL:

        If this is a youtube URL, this requests youtube subtitles
        Uses lassie to grab metadata
        Parses the HTML text with readablity
        uses bs4 to parse that text into a plaintext summary

        returns all the requested/parsed info as a models.Metdata object
        """
        uurl: str = clean_url(url)
        metadata = Metadata(url=uurl)
        # if this matches a youtube url, download subtitles
        try:
            yt_video_id: str = get_yt_video_id(uurl)  # can raise URLMetadataException
            # I think this is dangerous to do, might cause URL mismatches
            # on the other hand, it causes duplicate downloads if GET info
            # present in the query
            # url = "https://www.youtube.com/watch?v={}".format(yt_video_id)
            try:
                self.logger.debug(
                    "Downloading subtitles for Youtube ID: {}".format(yt_video_id)
                )
                metadata.subtitles = download_subtitles(
                    yt_video_id, self.subtitle_language
                )
            except YoutubeException as ye:
                self.logger.debug(str(ye))
            # sleep even if it failed to parse, still made the request to youtube
            # won't sleep if url doesn't match youtube
            sleep(self.sleep_time)
        except URLMetadataException:
            # don't log here, very common failure for the URL
            # to not be parsable as a Youtube URL
            pass

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
