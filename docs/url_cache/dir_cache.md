Module url_cache.dir_cache
==========================
An hash-based, file system cache

Functions
---------

    
`keyfile_matches_contents(key: str, path: str) ‑> bool`
:   Helper function to check if a file matches the key we're trying to find

    
`subdirs(path: str) ‑> List[str]`
:   Returns a list of subdirectores (that exist) for a existing directory

Classes
-------

`DirCache(loc: str)`
:   Underlying hash implementation.
    
    The input/key to the cache is a string, which is typically a URL.
    This stores the key at <target_dir>/key

    ### Static methods

    `hash_key(key: str) ‑> str`
    :   >>> DirCache.hash_key("something")
        '437b930db84b8079c2dd804a71936b5f'

    ### Methods

    `base_dir_hashed_path(self, key: str) ‑> str`
    :   Receives the key as input. Computes the corresponding base directory for the hash
        
        >>> d = DirCache('/tmp')
        >>> d.base_dir_hashed_path("something")
        '/tmp/4/3/7/b930db84b8079c2dd804a71936b5f'

    `delete(self, key: str) ‑> bool`
    :   Deletes the corresponding directory for a key, if it exists
        Returns True if something was deleted, else False

    `exists(self, key: str) ‑> bool`
    :   try/catch wrapper around self.get, to return whether or not a key already exists
        in the database

    `get(self, key: str) ‑> str`
    :   Receives some string key as input.
        Returns the directory for that key if it exists, else raises DirCacheMiss

    `put(self, key: str) ‑> str`
    :   Receives a key to create a cache directory for.
        Creates a directory by calculating the MD5 hash, returns the path to the corresponding
        directory. Expects the directory to only be used to store files, not directories.
        
        e.g.:
        
        First Directory
        For key 'something'
        hashlib.md5(b'something').hexdigest()
        '437b930db84b8079c2dd804a71936b5f'
        corresponding directory would be
        4/3/7/b930db84b8079c2dd804a71936b5f/000/
        and the key would be stored at
        4/3/7/b930db84b8079c2dd804a71936b5f/000/key
        
        If a hash collision occurs (a different key already exists there), this creates
        a new directory, starting with 001, 002, 003

`DirCacheMiss(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException