"""
Downloads subtitles from youtube
"""

import json
import html
import urllib.parse
from typing import Dict, Any

import requests

# TODO: use other helper funcs for better error warnings?
from pytube.extract import video_info_url  # type: ignore[import]

from .srt_converter import to_srt


class YoutubeSubtitlesException(Exception):
    pass


def download_subs(video_identifier: str, target_language: str) -> str:
    try:
        video_info: Dict[str, Any] = get_video_info(video_identifier)
        track_urls: Dict[str, Any] = get_sub_track_urls(video_info)
        target_track_url: str = select_target_lang_track_url(
            track_urls, target_language
        )
        subs_data: str = get_subs_data(target_track_url)
        return to_srt(subs_data)
    except (requests.exceptions.RequestException, YoutubeSubtitlesException) as e:
        raise YoutubeSubtitlesException(str(e))


def get_video_info(video_id: str) -> Dict[str, Any]:
    url = video_info_url(video_id, f"https://www.youtube.com/watch?v={video_id}")
    resp: requests.Response = requests.get(url)
    return urllib.parse.parse_qs(resp.text)


def get_sub_track_urls(video_info: Dict[str, Any]) -> Dict[str, Any]:
    try:
        video_response: Dict[str, Any] = json.loads(video_info["player_response"][0])
        captions = video_response["captions"]
        caption_tracks = captions["playerCaptionsTracklistRenderer"]["captionTracks"]
        return {
            caption_track["languageCode"]: caption_track["baseUrl"]
            for caption_track in caption_tracks
        }
    except KeyError:
        raise YoutubeSubtitlesException(
            "Error retrieving metadata. The video may be not have subtitles, or may be licensed"
        )


def select_target_lang_track_url(
    track_urls: Dict[str, Any], target_language: str
) -> str:
    try:
        chosen_lang: str = track_urls[target_language]
        return chosen_lang
    except KeyError:
        raise YoutubeSubtitlesException(
            f"Could not find track for target language {target_language}"
        )


def get_subs_data(subs_url: str) -> str:
    resp: requests.Response = requests.get(subs_url)
    return html.unescape(resp.text)
