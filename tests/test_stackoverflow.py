from url_cache.core import URLCache
from url_cache.sites.stackoverflow import StackOverflow

from .fixture import ucache, tests_dir


def test_extract_question_ids(ucache: URLCache) -> None:
    s = StackOverflow(uc=ucache)

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
