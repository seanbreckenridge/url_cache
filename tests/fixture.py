import os
import tempfile
import shutil
from typing import Generator

import pytest
from url_cache.core import URLCache


@pytest.fixture()
def ucache() -> Generator[URLCache, None, None]:  # type: ignore[misc]
    d: str = tempfile.mkdtemp()
    yield URLCache(cache_dir=d, sleep_time=0)
    shutil.rmtree(d)


tests_dir = os.path.dirname(os.path.abspath(__file__))
