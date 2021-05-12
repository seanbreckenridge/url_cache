Module url_cache.summary_cache
==============================

Classes
-------

`FileParser(name: str, ext: str, *, load_func: Callable[[pathlib.Path], ~T], dump_func: Callable[[~T, pathlib.Path], NoneType])`
:   Encapsulates some function which parses an underlying file for a field on the metadata

    ### Instance variables

    `filename: str`
    :

    ### Methods

    `dump(self, data: ~T, p: pathlib.Path) ‑> NoneType`
    :

    `load(self, p: pathlib.Path) ‑> ~T`
    :

    `matches(self, p: pathlib.Path) ‑> bool`
    :

`SummaryDirCache(data_dir: pathlib.Path, *, file_parsers: Optional[List[url_cache.summary_cache.FileParser]] = None)`
:   Interface to the underlying DirCache, which serializes/deserializes information
    from the Summary object into each individual file
    
    additional FileParser objects can be provided to parse custom data

    ### Methods

    `get(self, url: str) ‑> Optional[url_cache.model.Summary]`
    :   Get data for the 'url' from cache, or None if it doesn't exist

    `has(self, url: str) ‑> bool`
    :   Returns true/false, signifying whether or not the information
        for this url is already cached
        
        calls the underlying DirCache.exists function

    `has_null_value(self, url: str) ‑> bool`
    :   Currently not Implemented
        
        If the item isn't in cache, raises DirCacheMiss
        If the item is in cache, but it doesn't have any values (i.e. empty
        json file and no srt data), then return True
        else return False (this has data)
        
        meant to be used to 'retry' getting url metadata, incase none was retrieved

    `put(self, url: str, data: url_cache.model.Summary) ‑> str`
    :   Puts/Replaces the information from 'data' into the
        corresponding directory given the url
        
        Overwrites previous files/information if it exists for the URL