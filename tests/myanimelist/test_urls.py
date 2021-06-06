from url_cache.sites.myanimelist.urls.v4 import Version4, MalParseResult, JIKAN_BASE


def test_succeeds() -> None:
    v4 = Version4()
    assert v4.parse_url("https://myanimelist.net/") is None
    mal_id = 1
    bebop = MalParseResult(
        cleaned="https://myanimelist.net/anime/1",
        jikan_urls=[
            f"{JIKAN_BASE}/anime/{mal_id}",
            f"{JIKAN_BASE}/anime/{mal_id}/characters",
            f"{JIKAN_BASE}/anime/{mal_id}/staff",
            f"{JIKAN_BASE}/anime/{mal_id}/relations",
            f"{JIKAN_BASE}/anime/{mal_id}/themes",
            f"{JIKAN_BASE}/anime/{mal_id}/moreinfo",
            f"{JIKAN_BASE}/anime/{mal_id}/recommendations",
        ],
    )
    assert v4.parse_url("https://myanimelist.net/anime/1") == bebop
    assert v4.parse_url("https://myanimelist.net/anime/1/Cowboy_Bebop") == bebop
    assert v4.parse_url("https://myanimelist.net/anime/1/Something") == bebop

    m = v4.parse_url("https://myanimelist.net/manga/1/Monster")
    assert m is not None
    assert f"{JIKAN_BASE}/manga/1" in m.jikan_urls

    m = v4.parse_url("https://myanimelist.net/manga.php?id=1")
    assert m is not None
    assert f"{JIKAN_BASE}/manga/1" in m.jikan_urls

    c = v4.parse_url("https://myanimelist.net/clubs.php?cid=57607")
    assert c is not None
    assert f"{JIKAN_BASE}/clubs/57607" in c.jikan_urls

    c = v4.parse_url("https://myanimelist.net/clubs.php?cid=57607")
    assert c is not None
    assert f"{JIKAN_BASE}/clubs/57607" in c.jikan_urls

    u = v4.parse_url("https://myanimelist.net/profile/Xinil")
    assert u is not None
    assert f"{JIKAN_BASE}/users/Xinil" in u.jikan_urls

    ch = v4.parse_url("https://myanimelist.net/character/1")
    assert ch is not None
    assert f"{JIKAN_BASE}/characters/1" in ch.jikan_urls

    p = v4.parse_url("https://myanimelist.net/people.php?id=1")
    assert p is not None
    assert f"{JIKAN_BASE}/people/1" in p.jikan_urls
