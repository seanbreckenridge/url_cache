import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import pytest
import vcr  # type: ignore[import]

from url_cache.core import URLCache, Summary
from url_cache.summary_cache import DirCache
from url_cache.sites.youtube.core import get_yt_video_id

from .fixture import ucache, tests_dir


# links to use; requests are cached in ./vcr/
youtube_with_cc = "https://www.youtube.com/watch?v=KXJSjte_OAI"
youtube_with_cc_skip_subs = "https://www.youtube.com/watch?v=1n3NJdqzLNg"
youtube_without_cc = "https://youtu.be/xvQUiX26RfE"
github_home = "https://github.com"
image_file = "https://i.picsum.photos/id/1000/367/267.jpg?hmac=uO9iQNujyGpqk0Ieytv_xfwbpy3ENW4PhnIZ1gsnldI"


@pytest.mark.skip(reason="pytube subtitles is broken, waiting on fix")
@vcr.use_cassette(os.path.join(tests_dir, "vcr/youtube_subs.yaml"))  # type: ignore
def test_youtube_has_subtitles(ucache: URLCache) -> None:

    # make sure subtitles download to file
    assert not ucache.in_cache(youtube_with_cc)
    summ_resp: Summary = ucache.get(youtube_with_cc)
    assert ucache.in_cache(youtube_with_cc)
    assert isinstance(summ_resp, Summary)
    assert summ_resp is not None
    assert summ_resp.data is not None and "subtitles" in summ_resp.data
    assert "trade-off between space" in summ_resp.data["subtitles"]

    # make sure corresponding file exists
    dcache = ucache.summary_cache.dir_cache
    assert isinstance(dcache, DirCache)
    dir_full_path = dcache.get(ucache.preprocess_url(youtube_with_cc))
    assert dir_full_path.endswith("data/2/c/7/6284b2f664f381372fab3276449b2/000")

    subtitles_file = Path(os.path.join(dir_full_path, "data", "subtitles.srt"))
    assert subtitles_file.exists()

    # make sure subtitle is in cache dir
    assert "trade-off between space" in subtitles_file.read_text()


def test_youtube_preprocessor(ucache: URLCache) -> None:
    assert youtube_without_cc != "https://www.youtube.com/watch?v=xvQUiX26RfE"
    assert (
        ucache.preprocess_url(youtube_without_cc)
        == "https://www.youtube.com/watch?v=xvQUiX26RfE"
    )


@vcr.use_cassette(os.path.join(tests_dir, "vcr/youtube_no_subs.yaml"))  # type: ignore
def test_doesnt_have_subtitles(ucache: URLCache) -> None:
    summ_resp = ucache.get(youtube_without_cc)
    # shouldnt match, is the 'corrected' preprocessed URL
    assert summ_resp.url != youtube_without_cc
    # make sure this parsed the youtube id
    assert "xvQUiX26RfE" == get_yt_video_id(youtube_without_cc)
    assert summ_resp.data is not None
    # deleted for youtube by the site-specific extractor
    assert summ_resp.html_summary is None
    assert "subtitles" not in summ_resp.data
    dir_full_path = ucache.summary_cache.dir_cache.get(
        ucache.preprocess_url(youtube_without_cc)
    )
    assert not os.path.exists(os.path.join(dir_full_path, "data", "subtitles.srt"))
    assert os.path.exists(os.path.join(dir_full_path, "metadata.json"))
    # this deletes the summary files on purpose, since theyre somewhat useless
    assert not os.path.exists(os.path.join(dir_full_path, "html_summary.html"))


skip_dl_fp = os.path.join(tests_dir, "vcr/skip_downloading_youtube_subtitles.yaml")


@pytest.mark.skip(reason="pytube subtitles is broken, waiting on fix")
@vcr.use_cassette(skip_dl_fp)  # type: ignore
def test_skip_downloading_youtube_subtitles(ucache: URLCache) -> None:

    # see if this URL would succeed usually, download subtitles
    assert not ucache.in_cache(youtube_with_cc_skip_subs)
    summ_resp = ucache.get(youtube_with_cc_skip_subs)
    assert summ_resp is not None
    assert ucache.in_cache(youtube_with_cc_skip_subs)
    assert summ_resp is not None
    assert summ_resp.data is not None
    assert "subtitles" in summ_resp.data
    assert "coda radio" in summ_resp.data["subtitles"].casefold()
    dir_full_path = ucache.summary_cache.dir_cache.get(youtube_with_cc_skip_subs)

    # delete, and check its deleted
    shutil.rmtree(dir_full_path)
    assert not ucache.in_cache(youtube_with_cc_skip_subs)

    ucache.options["skip_subtitles"] = True

    # make sure we didnt get any subtitles
    summ_resp = ucache.get(youtube_with_cc_skip_subs)
    assert "subtitles" not in summ_resp.data


@vcr.use_cassette(os.path.join(tests_dir, "vcr/generic_url.yaml"))  # type: ignore
def test_generic_url(ucache: URLCache) -> None:
    summ_resp = ucache.get(github_home)  # type: ignore[union-attr]
    assert ucache.in_cache(github_home)

    # basic tests for any sort of text-based URL
    assert summ_resp.html_summary is not None
    assert isinstance(summ_resp.timestamp, datetime)
    assert "subtitles" not in summ_resp.data
    assert summ_resp.metadata is not None
    assert summ_resp.metadata["title"].casefold().startswith("github")

    dir_full_path = ucache.summary_cache.dir_cache.get(github_home)
    # make sure subtitles file doesn't exist for item which doesnt have subtitle
    assert not os.path.exists(os.path.join(dir_full_path, "data", "subtitles.srt"))
    assert os.path.exists(os.path.join(dir_full_path, "metadata.json"))
    assert os.path.exists(os.path.join(dir_full_path, "html_summary.html"))
    assert os.path.exists(os.path.join(dir_full_path, "timestamp.datetime.txt"))
    # url file shouldnt exist, that is stored in key
    assert not os.path.exists(os.path.join(dir_full_path, "url.txt"))
    assert os.path.exists(os.path.join(dir_full_path, "key"))


@vcr.use_cassette(os.path.join(tests_dir, "vcr/test_image.yaml"))  # type: ignore
def test_image(ucache: URLCache) -> None:

    summ_resp = ucache.get(image_file)
    assert ucache.in_cache(image_file)

    # assert Summary values
    assert summ_resp.html_summary is None  # shouldnt have any HTML
    assert "subtitles" not in summ_resp.data  # no subtitles, obviously
    imgs: List[Dict[str, Any]] = summ_resp.metadata["images"]
    assert len(imgs) == 1
    assert imgs[0]["type"] == "body_image"
    assert imgs[0]["src"].startswith("https://i.picsum.photos/id/")

    # make sure expected files exist/dont exist
    dir_full_path = ucache.summary_cache.dir_cache.get(image_file)
    assert not os.path.exists(os.path.join(dir_full_path, "summary_html.html"))
    assert os.path.exists(os.path.join(dir_full_path, "metadata.json"))


@vcr.use_cassette(os.path.join(tests_dir, "vcr/generic_url.yaml"))  # type: ignore
def test_read_from_cache(ucache: URLCache) -> None:
    ucache.get(github_home)
    assert ucache.in_cache(github_home)

    # this should load from file instead
    ucache.get(github_home)
