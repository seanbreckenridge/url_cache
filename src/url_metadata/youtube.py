from .yt_subs.subtitles_downloader import (
    TrackNotFoundException,
    VideoParsingException,
    download_subs,
)


class YoutubeException(Exception):
    pass


def download_subtitles(youtube_id: str, lang: str = "en") -> str:
    """
    youtube_id: for url 'https://www.youtube.com/watch?v=YoMUQXgcH94', pass 'YoMUQXgcH94'
    lang: language to download subtitles for

    Raises YoutubeException on errors
    """
    try:
        return download_subs(youtube_id, lang)
    except (TrackNotFoundException, VideoParsingException) as e:
        return YoutubeException(str(e))
