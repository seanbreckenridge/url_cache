import logging
from time import sleep
from pathlib import Path
from typing import Optional, Union

from lassie import Lassie
from appdirs import user_data_dir
from requests import Session, Response

from .log import setup
from .exceptions import URLMetadataException
from .model import Metadata
from .youtube import download_subtitles, get_yt_video_id, YoutubeException

DEFAULT_SUBTITLE_LANGUAGE = "en"
DEFAULT_SLEEP_TIME = 5


def _normalize(p: Union[str, Path]) -> Path:
    if isinstance(p, Path):
        return p
    elif isinstance(p, str):
        return Path(p).expanduser().absolute()
    else:
        raise TypeError("Expected 'str' or 'pathlib.Path', recieved {}".format(type(p)))


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
        print("Saving " + str(resp))
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

        self.database_path: Path = self._base_cache_dir / "index.sqlite"

        self.subtitle_language: str = subtitle_language
        self.logger: logging.Logger = setup(loglevel)
        self.sleep_time: int = sleep_time

        ll: Lassie = Lassie()
        # hackery with a requests.Session to save the most recent request object
        ll.client = SaveSession(cb_func=self.save_http_response)
        self.lassie: Lassie = ll

    def save_http_response(self, resp: Response) -> None:
        """
        callback function to save the most recent request that lassie made
        """
        # do I need to save multiple? lassie makes a HEAD
        # request to get the content type, and then another
        # to get the content, so this should access the
        # response with the content
        self._response = resp

    def get(self, url: str, skip_cache=False) -> Metadata:
        if skip_cache or not self.in_cache(url):
            # user specified to skip using cache, or item doesn't exist in cache
            # make HTTP request, depending on the URL
            data = self.handle_url(url)
            # TODO: save response
            return data
        else:
            # TODO: read info from cache
            return True

    def in_cache(self, url: str) -> bool:
        # TODO: implement; check if in cache
        return False

    def handle_url(self, url: str) -> Metadata:
        metadata = Metadata(info={}, subtitles=None)
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
            # dont log here, very common failure
            pass
        self.logger.debug("Fetching metadata for {}".format(url))
        # TODO: need to handle errors?
        metadata.info = self.lassie.fetch(url, handle_file_content=True)
        sleep(self.sleep_time)
        # TODO: use readability lib to parse self._response.text
        return metadata
