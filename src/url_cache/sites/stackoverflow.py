from typing import Optional
from urllib.parse import urlparse
from functools import lru_cache

from .abstract import AbstractSite


# TODO: support other stackexchange sites?
class StackOverflow(AbstractSite):
    """
    StackOverflow extractor to normalize question IDs/extract question/answers
    """

    @lru_cache(maxsize=32)
    def extract_question_id(self, url: str) -> Optional[int]:
        """
        Extract a stackoverflow question ID from a URL
        """
        parsed = urlparse(url)
        if "stackoverflow.com" not in parsed.netloc:
            return None
        qid: str
        if parsed.path.startswith("/q/"):
            qid = parsed.path.split("/")[2]
        elif parsed.path.startswith("/questions/"):
            qid = parsed.path.split("/")[2]
        if qid.isdigit():
            return int(qid)
        return None

    def matches_site(self, url: str) -> bool:
        return self.extract_question_id(url) is not None

    # TODO: add an extract_info here to extract responses from stackoverflow question/answers?

    def preprocess_url(self, url: str) -> str:
        qid = self.extract_question_id(url)
        if qid is not None:
            return f"https://stackoverflow.com/questions/{qid}"
        else:
            return url
