import os

from url_cache.core import URLCache
from url_cache.sites.stackoverflow import StackOverflow

import vcr  # type: ignore[import]

tests_dir = os.path.dirname(os.path.abspath(__file__))


@vcr.use_cassette(os.path.join(tests_dir, "vcr/stackoverflow_redirect.yaml"))  # type: ignore
def test_extract_question_ids() -> None:
    s = StackOverflow(uc=URLCache(sleep_time=0))

    # redirect answers to qid
    assert (
        s.preprocess_url("https://stackoverflow.com/a/10856450/438324324923894")
        == "https://stackoverflow.com/questions/3850022"
    )

    # extract qid
    assert (
        s.preprocess_url(
            "https://stackoverflow.com/questions/10161568/import-python-module-not-on-path"
        )
        == "https://stackoverflow.com/questions/10161568"
    )

    # extract qid
    assert (
        s.preprocess_url("https://stackoverflow.com/q/35013075/93842949328492")
        == "https://stackoverflow.com/questions/35013075"
    )
