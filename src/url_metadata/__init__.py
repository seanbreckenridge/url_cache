from typing import Optional

from .core import URLMetadataCache, Metadata

# uncustomized, basic entry point to the library
default_cache: Optional[URLMetadataCache] = None


def metadata(url: str) -> Metadata:
    global default_cache
    if default_cache is None:
        default_cache = URLMetadataCache()
    return default_cache.get(url)
