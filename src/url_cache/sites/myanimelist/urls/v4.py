"""
Converts MyAnimeList URLs to Jikan API URLs
This uses v4 of the API

This makes no requests, it just parses URLs
and creates the corresponding URLs to request for Jikan
"""

import re
from typing import Optional, List, NamedTuple
from functools import lru_cache

from urllib.parse import urlparse, parse_qs, ParseResult

JIKAN_BASE = "https://api.jikan.moe/v4"

REST_MATCH = r"/(anime|manga|character|people|clubs)/(\d+)"
PHP_MATCH = r"/(anime|manga|character|people|clubs)\.php"
USER_PROFILE_MATCH = r"/profile/([^\/]+)\/?"

REST_MATCH_RE = re.compile(REST_MATCH)
PHP_MATCH_RE = re.compile(PHP_MATCH)
USER_PROFILE_MATCH_RE = re.compile(USER_PROFILE_MATCH)

# is probably better to just use the data directly from the anime/manga
# instead of trying to cache dynamic/paginated results
IGNORED = {
    "ownlist",
    "mymessages.php",
    "recommendations",
    "users.php",
    "topanime.php",
    "topmanga.php",
    "ajaxtb.php",
    "about.php",
    "animelist",
    "mangalist",
    "shared.php",
    "myfriends.php",
    "myrecommendations.php",
    "panel.php",
    "login.php",
    "includes",
    "info.php",
    "myblog.php",
    "history",
}

# dont cache animelist/mangalists here, use https://github.com/seanbreckenridge/malexport/ to keep track of them


# if no jikan_urls, shouldn't request this, its a dynamic URL and saving
# it in cache wouldn't be that useful
class MalParseResult(NamedTuple):
    cleaned: str
    jikan_urls: List[str]


class Version4:
    """
    Converts MyAnimeList URLs to their corresponding Jikan counterparts.

    Only supports a subset of the URLs -- this doesnt support user lists
    or pages that change very often (searches, seasonal listings, history pages)
    as it wouldn't be as useful to cache those
    """

    def __init__(self, base_url: str = JIKAN_BASE):
        self.base = base_url.rstrip("/")

    def _extract_dispatch(self, endpoint: str, mal_id: int) -> Optional[MalParseResult]:
        if endpoint == "anime":
            return self._extract_anime(mal_id)
        elif endpoint == "manga":
            return self._extract_manga(mal_id)
        elif endpoint == "character":
            return self._extract_characters(mal_id)
        elif endpoint == "people":
            return self._extract_person(mal_id)
        elif endpoint == "clubs":
            return self._extract_club(mal_id)
        else:
            return None

    def _extract_anime(self, mal_id: int) -> MalParseResult:
        return MalParseResult(
            cleaned=f"https://myanimelist.net/anime/{mal_id}",
            jikan_urls=[
                f"{self.base}/anime/{mal_id}",
                f"{self.base}/anime/{mal_id}/characters",
                f"{self.base}/anime/{mal_id}/staff",
                f"{self.base}/anime/{mal_id}/pictures",
                f"{self.base}/anime/{mal_id}/statistics",
                f"{self.base}/anime/{mal_id}/relations",
                f"{self.base}/anime/{mal_id}/themes",
                f"{self.base}/anime/{mal_id}/moreinfo",
                f"{self.base}/anime/{mal_id}/recommendations",
            ],
        )

    def _extract_manga(self, mal_id: int) -> MalParseResult:
        return MalParseResult(
            cleaned=f"https://myanimelist.net/manga/{mal_id}",
            jikan_urls=[
                f"{self.base}/manga/{mal_id}",
                f"{self.base}/manga/{mal_id}/characters",
                f"{self.base}/manga/{mal_id}/relations",
                f"{self.base}/manga/{mal_id}/moreinfo",
                f"{self.base}/manga/{mal_id}/recommendations",
                f"{self.base}/manga/{mal_id}/pictures",
                f"{self.base}/manga/{mal_id}/statistics",
            ],
        )

    def _extract_characters(self, mal_id: int) -> MalParseResult:
        return MalParseResult(
            cleaned=f"https://myanimelist.net/character/{mal_id}",
            jikan_urls=[
                f"{self.base}/characters/{mal_id}",
                f"{self.base}/characters/{mal_id}/voices",
                f"{self.base}/characters/{mal_id}/pictures",
            ],
        )

    def _extract_person(self, mal_id: int) -> MalParseResult:
        return MalParseResult(
            cleaned=f"https://myanimelist.net/people/{mal_id}",
            jikan_urls=[
                f"{self.base}/people/{mal_id}",
                f"{self.base}/people/{mal_id}/anime",
                f"{self.base}/people/{mal_id}/manga",
                f"{self.base}/people/{mal_id}/voices",
                f"{self.base}/people/{mal_id}/pictures",
            ],
        )

    def _extract_club(self, mal_id: int) -> MalParseResult:
        return MalParseResult(
            cleaned=f"https://myanimelist.net/clubs.php?cid={mal_id}",
            jikan_urls=[
                f"{self.base}/clubs/{mal_id}",
            ],
        )

    def _extract_user(self, username: str) -> MalParseResult:
        return MalParseResult(
            cleaned=f"https://myanimelist.net/profile/{username}",
            jikan_urls=[
                f"{self.base}/users/{username}",
                f"{self.base}/users/{username}/statistics",
                f"{self.base}/users/{username}/favorites",
                f"{self.base}/users/{username}/about",
            ],
        )

    @lru_cache(maxsize=2048)
    def parse_url(self, url: str) -> Optional[MalParseResult]:
        """
        Given a URL, if extra information can be extracted by requesting info from Jikan
        this cleans the URL to reduce duplicates and returns the Jikan URLs to request
        """

        res: ParseResult = urlparse(url)
        if res.netloc != "myanimelist.net":
            return None
        # homepage
        if res.path.strip("/") == "":
            return None

        # match pages like /anime/4394
        match: Optional[re.Match[str]] = None
        match = re.match(REST_MATCH_RE, res.path)
        if match is not None:
            return self._extract_dispatch(match.group(1), int(match.group(2)))

        # match pages like anime.php?id=4394
        match = re.match(PHP_MATCH_RE, res.path)
        if match is not None:
            # parse the query params into a dict
            query_res = parse_qs(res.query)
            # get the id= or cid= (for clubs)
            ids = query_res.get("id") or query_res.get("cid")
            if ids and len(ids) > 0:
                return self._extract_dispatch(match.group(1), int(ids[0]))

        # stuff like /profile/username...
        match = re.match(USER_PROFILE_MATCH_RE, res.path)
        if match is not None:
            return self._extract_user(match.group(1))

        # explicit ignores
        fst = res.path.strip("/").split("/")[0]
        if fst in IGNORED:
            return None

        # TODO: parse forums posts?

        return None
