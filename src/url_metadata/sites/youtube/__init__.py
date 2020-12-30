from time import sleep
from typing import Optional
from functools import lru_cache
from urllib.parse import urlparse, parse_qs, ParseResult

from .yt_subs import YoutubeSubtitlesException, download_subs  # type: ignore
from ...model import Metadata
from ..abstract import AbstractSite

# https://gist.github.com/kmonsoor/2a1afba4ee127cce50a0
@lru_cache(maxsize=None)
def get_yt_video_id(url: str) -> Optional[str]:
    """
    Returns Video_ID extracting from the given url of Youtube
    Returns None if youtube ID could not be extracted

    Examples of URLs:
      Valid:
        'http://youtu.be/_lOT2p_FCvA',
        'www.youtube.com/watch?v=_lOT2p_FCvA&feature=feedu',
        'http://www.youtube.com/embed/_lOT2p_FCvA',
        'http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US',
        'https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6',
        'youtube.com/watch?v=_lOT2p_FCvA',
      Invalid:
        'youtu.be/watch?v=_lOT2p_FCvA',
    """

    if url.startswith(("youtu", "www")):
        url = "http://" + url

    query: Optional[ParseResult] = urlparse(url)

    if query is None:
        return None
    if query.hostname is None or query.path is None:
        return None
    elif "youtube" in query.hostname:
        if query.path == "/watch":
            return parse_qs(query.query)["v"][0]
        elif query.path.startswith(("/embed/", "/v/")):
            return query.path.split("/")[2]
    elif "youtu.be" in query.hostname:
        return query.path[1:]
    return None


class Youtube(AbstractSite):
    def matches_site(self, url: str) -> bool:
        return get_yt_video_id(url) is not None

    def extract_info(self, url: str, metadata: Metadata) -> Metadata:  # type: ignore[misc]
        metadata = self._delete_unnecessary_info(metadata)
        # if user didn't specify to skip trying to download subtitles
        if not self._umc.skip_subtitles:
            yt_id: Optional[str] = get_yt_video_id(url)
            # exit early if the URL doesn't match the site, this shouldn't have been called anyways
            if yt_id is None:
                return metadata
            # if this matches a youtube url, download subtitles
            # I think changing the URL is dangerous to do, might cause URL mismatches (the same URL wont be returned by cache)
            # on the other hand, it causes duplicate downloads if GET info
            # present in the query
            # url = "https://www.youtube.com/watch?v={}".format(yt_id)
            # for now, while this doesnt have some URL preprocessor to handle that (add a hook to
            # abstract?), leave it as the user provided
            try:
                self._umc.logger.debug(f"Downloading subtitles for Youtube ID: {yt_id}")
                metadata.subtitles = download_subs(yt_id, self._umc.subtitle_language)
            except YoutubeSubtitlesException as ye:  # this catches both request and track/subtitle exceptions
                self._umc.logger.debug(str(ye))
                # sleep even if it failed to parse, still made the request to youtube
                # won't sleep if url doesn't match youtube
                sleep(self._umc.sleep_time)
        return metadata

    def _delete_unnecessary_info(self, metadata: Metadata) -> Metadata:
        """
        The extracted data from youtube isn't that useful, its not worth keeping
        """
        # TODO: add as flag, to prevent this info from being deleted. I think this is fine though
        metadata.html_summary = None
        metadata.text_summary = None
        return metadata
