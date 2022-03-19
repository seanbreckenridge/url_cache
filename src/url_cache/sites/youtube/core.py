from typing import Optional, List
from functools import lru_cache
from urllib.parse import urlparse, parse_qs, ParseResult

from .subtitles_downloader import YoutubeSubtitlesException, download_subs
from ...model import Summary
from ...summary_cache import FileParser, _load_file_text, _dump_file_text
from ..abstract import AbstractSite


# From: https://gist.github.com/kmonsoor/2a1afba4ee127cce50a0
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
    """
    Youtube site extractor to get subtitles for videos
    """

    def file_parsers(self) -> List[FileParser]:
        return [
            FileParser(
                name="subtitles",
                ext=".srt",
                load_func=_load_file_text,
                dump_func=_dump_file_text,
            )
        ]

    def matches_site(self, url: str) -> bool:
        return get_yt_video_id(url) is not None

    def extract_info(self, url: str, summary: Summary) -> Summary:
        summary = self._delete_unnecessary_info(summary)
        # if user didn't specify to skip trying to download subtitles
        if not self._uc.options["skip_subtitles"]:
            yt_id: Optional[str] = get_yt_video_id(url)
            # exit early if the URL doesn't match the site, this shouldn't have been called anyways
            if yt_id is None:
                return summary
            # if this matches a youtube url, download subtitles
            try:
                self.logger.debug(f"Downloading subtitles for Youtube ID: {yt_id}")
                summary.data["subtitles"] = download_subs(
                    yt_id, self._uc.options["subtitle_language"]
                )
                self.sleep()
            except YoutubeSubtitlesException as ye:  # this catches both request and track/subtitle exceptions
                self.logger.debug(str(ye))
                # sleep even if it failed to parse, still made the request to youtube
                # won't sleep if url doesn't match youtube
                self.sleep()
        return summary

    def preprocess_url(self, url: str) -> str:
        yt_id: Optional[str] = get_yt_video_id(url)
        if yt_id is None:
            # failed, just return URL as it was
            return url
        else:
            return "https://www.youtube.com/watch?v={}".format(yt_id)

    def _delete_unnecessary_info(self, summary: Summary) -> Summary:
        """
        The extracted data from youtube isn't that useful, its not worth keeping
        """
        summary.html_summary = None
        return summary
