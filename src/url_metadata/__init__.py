from .core import URLMetadataCache

# uncustomized, basic entry point to the library
default_cache = None


def metadata(url):
    global default_cache
    if default_cache is None:
        default_cache = URLMetadataCache()
    return default_cache.get(url)
