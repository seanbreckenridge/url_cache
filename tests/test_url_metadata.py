import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest
import vcr

from url_metadata.core import URLMetadataCache, Metadata
from url_metadata.cache import DirCache
from url_metadata.youtube import get_yt_video_id


@pytest.fixture()
def ucache():
    d: str = tempfile.mkdtemp()
    yield URLMetadataCache(cache_dir=d, sleep_time=0)
    shutil.rmtree(d)


# links to use; requests are cached in ./vcr/
youtube_with_cc = "https://www.youtube.com/watch?v=KXJSjte_OAI"
youtube_without_cc = "https://youtu.be/xvQUiX26RfE"
github_home = "https://github.com"
image_file = "https://i.picsum.photos/id/1000/367/267.jpg?hmac=uO9iQNujyGpqk0Ieytv_xfwbpy3ENW4PhnIZ1gsnldI"


@vcr.use_cassette("tests/vcr/youtube_subs.yaml")
def test_youtube_has_subtitles(ucache):
    # make sure subtitles download to file
    assert not ucache.in_cache(youtube_with_cc)
    meta_resp = ucache.get(youtube_with_cc)
    assert ucache.in_cache(youtube_with_cc)
    assert isinstance(meta_resp, Metadata)
    assert "trade-off between space and time" in meta_resp.subtitles

    # make sure corresponding file exists
    dcache = ucache.metadata_cache.cache
    assert isinstance(dcache, DirCache)
    dir_full_path = dcache.get(youtube_with_cc)
    assert dir_full_path.endswith("data/2/c/7/6284b2f664f381372fab3276449b2/000")

    # make sure _path handler map returns the correct hash/file
    subtitles_file: Path = ucache.metadata_cache.__class__._path(
        dir_full_path, "subtitles"
    )
    assert str(subtitles_file) == os.path.join(dir_full_path, "subtitles.srt")

    # make sure subtitle is in cache dir
    assert "trade-off between space and time" in subtitles_file.read_text()


@vcr.use_cassette("tests/vcr/youtube_no_subs.yaml")
def test_doesnt_have_subtitles(ucache):
    meta_resp = ucache.get(youtube_without_cc)
    # make sure this parsed the youtube id
    assert "xvQUiX26RfE" == get_yt_video_id(youtube_without_cc)
    assert meta_resp.subtitles is None
    dir_full_path = ucache.metadata_cache.cache.get(youtube_without_cc)
    assert not os.path.exists(os.path.join(dir_full_path, "subtitles.srt"))
    assert os.path.exists(os.path.join(dir_full_path, "metadata.json"))
    assert os.path.exists(os.path.join(dir_full_path, "summary.html"))


@vcr.use_cassette("tests/vcr/generic_url.yaml")
def test_generic_url(ucache):
    meta_resp = ucache.get(github_home)
    assert ucache.in_cache(github_home)

    # basic tests for any sort of text-based URL
    assert meta_resp.subtitles is None
    assert meta_resp.text_summary is not None
    assert meta_resp.info["title"].casefold().startswith("github")

    dir_full_path = ucache.metadata_cache.cache.get(github_home)
    # make sure subtitles file doesn't exist for item which doesnt have subtitle
    assert not os.path.exists(os.path.join(dir_full_path, "subtitles.srt"))
    assert os.path.exists(os.path.join(dir_full_path, "metadata.json"))


@vcr.use_cassette("tests/vcr/test_image.yaml")
def test_image(ucache):

    # test text_summary doesnt exist for image file, since it doesnt have any
    meta_resp = ucache.get(image_file)
    assert ucache.in_cache(image_file)

    # assert Metadata values
    assert meta_resp.html_summary is None
    assert meta_resp.text_summary is None
    assert meta_resp.subtitles is None
    imgs: List[Dict[str, Any]] = meta_resp.info["images"]
    assert len(imgs) == 1
    assert imgs[0]["type"] == "body_image"
    assert imgs[0]["src"].startswith("https://i.picsum.photos/id/")

    # make sure expected files exist/dont exist
    dir_full_path = ucache.metadata_cache.cache.get(image_file)
    assert not os.path.exists(os.path.join(dir_full_path, "subtitles.srt"))
    assert not os.path.exists(os.path.join(dir_full_path, "summary.html"))
    assert not os.path.exists(os.path.join(dir_full_path, "summary.txt"))
    assert os.path.exists(os.path.join(dir_full_path, "metadata.json"))
