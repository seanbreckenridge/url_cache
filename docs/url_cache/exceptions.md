Module url_cache.exceptions
===========================

Classes
-------

`URLCacheException(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException

    ### Descendants

    * url_cache.exceptions.URLCacheRequestException

`URLCacheRequestException(*args, **kwargs)`
:   Encountered a request error while requesting a URL

    ### Ancestors (in MRO)

    * url_cache.exceptions.URLCacheException
    * builtins.Exception
    * builtins.BaseException