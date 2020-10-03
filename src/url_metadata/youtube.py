from typing import Optional
from urllib.parse import urlparse, parse_qs, ParseResult

from .exceptions import URLMetadataException

from .yt_subs.subtitles_downloader import TrackNotFoundException, VideoParsingException, download_subs # type: ignore


class YoutubeException(Exception):
    pass


def download_subtitles(youtube_id: str, lang: str = "en") -> str:
    """
    youtube_id: e.g. for the url 'https://www.youtube.com/watch?v=YoMUQXgcH94', pass 'YoMUQXgcH94'
    lang: language to download subtitles for

    returns a string which has the .srt file contents

    Raises YoutubeException on errors
    """
    try:
        return download_subs(youtube_id, lang)
    except (TrackNotFoundException, VideoParsingException) as e:
        raise YoutubeException(str(e))


# https://gist.github.com/kmonsoor/2a1afba4ee127cce50a0
def get_yt_video_id(url: str):
    """Returns Video_ID extracting from the given url of Youtube

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
        raise URLMetadataException("Could not parse video id from {}".format(url))
    if query.hostname is None or query.path is None:
        raise URLMetadataException("Parsed query info from url {} is None".format(url))
    elif "youtube" in query.hostname:
        if query.path == "/watch":
            return parse_qs(query.query)["v"][0]
        elif query.path.startswith(("/embed/", "/v/")):
            return query.path.split("/")[2]
    elif "youtu.be" in query.hostname:
        return query.path[1:]
    else:
        raise URLMetadataException("Could not parse video id from {}".format(url))
