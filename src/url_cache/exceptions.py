class URLCacheException(Exception):
    pass


class URLCacheRequestException(URLCacheException):
    """Encountered a request error while requesting a URL"""

    pass
