"""
Core funcitonality for url_metadata, switches on the URLs to request different types of information
saves that to cache. If something has already been requested, returns it from cache.
"""

import logging
from time import sleep
from pathlib import Path
from typing import Optional, Union

import backoff
import readability
from lassie import Lassie, LassieError
from appdirs import user_data_dir
from requests import Session, Response

from .log import setup
from .exceptions import URLMetadataException, URLMetadataRequestException
from .cache import MetadataCache
from .model import Metadata
from .utils import _normalize, fibo_backoff, backoff_warn, clean_url
from .youtube import download_subtitles, get_yt_video_id, YoutubeException

DEFAULT_SUBTITLE_LANGUAGE = "en"
DEFAULT_SLEEP_TIME = 5


class SaveSession(Session):
    def __init__(self, **kwargs):
        """
        cb_func: A callback function which saves the response
        """
        self.cb_func = kwargs.pop("cb_func")
        super().__init__(**kwargs)

    def send(self, *args, **kwargs):
        """
        Save the latest response for a requests.Session
        """
        resp = super().send(*args, **kwargs)
        self.cb_func(resp)
        return resp


class URLMetadataCache:
    def __init__(
        self,
        loglevel: int = logging.WARNING,
        subtitle_language: str = DEFAULT_SUBTITLE_LANGUAGE,
        sleep_time: int = DEFAULT_SLEEP_TIME,
        cache_dir: Optional[Union[str, Path]] = None,
    ):

        # handle cache dir
        cdir: Optional[Path] = None
        if cache_dir is not None:
            cdir = _normalize(cache_dir)
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

        # TODO: setup rotating logfile in user_cache_dir
        self.logger: logging.Logger = setup(loglevel)

        self.subtitle_language: str = subtitle_language
        self.sleep_time: int = sleep_time

        ll: Lassie = Lassie()
        # hackery with a requests.Session to save the most recent request object
        ll.client = SaveSession(cb_func=self.save_http_response)
        self.lassie: Lassie = ll

        # default 'last response received' to None
        self._response = None

    def save_http_response(self, resp: Response) -> None:
        """
        callback function to save the most recent request that lassie made
        """
        # do I need to save multiple? lassie makes a HEAD
        # request to get the content type, and then another
        # to get the content, so this should access the
        # response with the content
        self._response = resp

    def get(self, url: str) -> Metadata:
        uurl: str = clean_url(url)
        if not self.in_cache(uurl):
            data: Metadata = self.request_data(uurl)
            self.metadata_cache.put(uurl, data)
            return data
        # returns None if not present
        return self.metadata_cache.get(uurl)

    def in_cache(self, url: str) -> bool:
        uurl: str = clean_url(url)
        return self.metadata_cache.has(uurl)

    def request_data(self, url: str) -> Metadata:
        metadata = Metadata()
        # if this matches a youtube url, download subtitles
        try:
            yt_video_id: str = get_yt_video_id(url)
            try:
                self.logger.debug(
                    "Downloading subtitles for Youtube ID: {}".format(yt_video_id)
                )
                metadata.subtitles = download_subtitles(
                    yt_video_id, self.subtitle_language
                )
                sleep(self.sleep_time)
            except YoutubeException as ye:
                self.logger.debug(str(ye))
        except URLMetadataException:
            # don't log here, very common failure for the URL
            # to not be parsable as a Youtube URL
            pass

        # set self._response, to make sure we're not using stale request information when parsing with readability
        self._response = None

        # try to fetch metadata data with lassie, requests.Session saves the response object using a callback
        # to self._response
        try:
            metadata.info = self._fetch_lassie(url)
        except URLMetadataRequestException:
            # failed after waiting 13, 21, 34 seconds successively
            pass

        sleep(self.sleep_time)
        # use readability lib to parse self._response.text
        # if we're at this point, that should always be the latest
        # response, see https://github.com/michaelhelmick/lassie/blob/dd525e6243a989f083534921a1a1206931e608ec/lassie/core.py#L244-L266
        if self._response is not None:
            if self._response.status_code < 400:
                doc = readability.Document(self._response.text)
                metadata.html_title = doc.title()
                metadata.html_summary = doc.summary()
            else:
                self.logger.warning(
                    f"Response code for {url} is {self._response.status_code}, skipping HTML extraction..."
                )

        if metadata.html_summary is not None:
            # TODO: parse with pandoc
            pass
        return metadata

    @backoff.on_exception(
        fibo_backoff, URLMetadataRequestException, max_tries=3, on_backoff=backoff_warn
    )
    def _fetch_lassie(self, url):
        self.logger.debug("Fetching metadata for {}".format(url))
        try:
            return self.lassie.fetch(url, handle_file_content=True, all_images=True)
        except LassieError as le:
            self.logger.warning("Could not retrieve metadata from lassie: " + str(le))
        if self._response.status_code == 429:
            raise URLMetadataRequestException(
                "Received 429 for URL {}, waiting to retry...".format(url)
            )
        return None
