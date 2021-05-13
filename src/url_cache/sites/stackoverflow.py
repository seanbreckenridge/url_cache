from typing import Optional
from urllib.parse import urlparse
from functools import lru_cache

from requests import get, Response

from .abstract import AbstractSite
from ..model import Summary


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
        elif parsed.path.startswith("/a/"):
            # request this so that we redirect to the question
            # dont use the session so this doesnt overwrite data
            resp = get(url)
            self._uc.sleep()
            if resp.status_code == 200:
                parsed = urlparse(resp.url)
                if parsed.path.startswith("/questions/"):
                    qid = parsed.path.split("/")[2]
        if qid.isdigit():
            return int(qid)
        return None

    def matches_site(self, url: str) -> bool:
        return self.extract_question_id(url) is not None

    def extract_info(self, url: str, summary: Summary) -> Summary:
        # TODO: add some stuff here to responses from stackoverflow question/answers?
        return summary

    def preprocess_url(self, url: str) -> str:
        qid = self.extract_question_id(url)
        if qid is not None:
            return f"https://stackoverflow.com/questions/{qid}"
        else:
            return url
