# TODO: allow user to configure logging

from .core import URLMetadataCache

# if not customized at all, metadata is a very basic entrypoint
# to this library.
#
# If you want to do anything else, better to import it elsewhere
# and provide flags
default_cache = URLMetadataCache()


def metadata(url):
    return default_cache.get(url)
