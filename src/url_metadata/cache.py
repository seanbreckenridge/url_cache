"""
An hash-based, file system cache
"""

import os
from hashlib import md5
from typing import Optional
from pathlib import Path
from typing import List

from .model import Metadata


class DirCacheMiss(Exception):
    pass


def subdirs(path: str) -> List[str]:
    return [f.path for f in os.scandir(path) if f.is_dir()]


def keyfile_matches_contents(key: str, path: str) -> bool:
    with open(path, "r") as f:
        contents = f.read()
    return contents == key


# this means that there is no 'master' index/database file, which could
# possibly cause issues, if we were using autoindexed IDs to decide
# where to put a cached request. This way, its only dependent on the URL.
# If you want to delete a cached response, you merely have to delete
# the folder.
# It stores the corresponding URL as a 'key' file when inserted,
# so it can do chaining of sorts if there are hash collisions
# By no means is this an 'optimal' caching strategy, but it provides
# the benifit that there is no index, with relatively fast lookup (using MD5)
# Directories can be deleted by the user whenever they'd like without issue.
class DirCache:
    """
    Underlying hash implementation.

    The input/key to the cache is a string, which is typically a URL.
    This stores the key at <target_dir>/key

    """

    def __init__(self, loc: Path):
        self.base = str(loc)
        os.makedirs(self.base, exist_ok=True)

    def get(self, key: str) -> str:
        """
        Recieves some string key as input.
        Returns the directory for that key if it exists, else raises DirCacheMiss
        """
        base: str = self.base_dir(key)
        if not os.path.exists(base):
            raise DirCacheMiss("Base dir for hash doesn't exist: {}".format(base))
        # check if keyfile matches any of the existing directories
        for s in subdirs(base):
            target_key = os.path.join(s, "key")
            if os.path.exists(target_key) and keyfile_matches_contents(key, target_key):
                return s
        raise DirCacheMiss("No matching keyfile found!")

    def put(self, key: str) -> str:
        """
        Recieves a key to create a cache directory for.
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
        """
        base: str = self.base_dir(key)
        os.makedirs(base, exist_ok=True)
        # check if keyfile matches any of the existing directories
        for s in subdirs(base):
            target_key = os.path.join(s, "key")
            if os.path.exists(target_key) and keyfile_matches_contents(key, target_key):
                return s
        # if keyfile didnt match an existing one, put it in the first 'open' directory
        # in this folder. Most of the time, this will be unique and just return
        # ../000/
        i = 0
        while True:
            possible_dir = os.path.join(base, str(i).zfill(3))
            if not os.path.exists(possible_dir):
                # create keyfile, and return directory
                os.makedirs(possible_dir)
                with open(os.path.join(possible_dir, "key"), "w") as kf:
                    kf.write(key)
                return possible_dir
            i += 1

    def exists(self, key: str) -> bool:
        """
        try/catch wrapper around self.get, to return whether or not a key already exists
        in the database
        """
        try:
            self.get(key)
            return True
        except DirCacheMiss:
            return False

    def base_dir(self, key: str) -> str:
        """
        Recieves the key as input. Computes the corresponding base directory for the hash

        >>> d = DirCache('/tmp')
        >>> d.base_dir("something")
        '/tmp/4/3/7/b930db84b8079c2dd804a71936b5f'
        """
        md5_hash: str = self.__class__.hash_key(key)
        parts: List[str] = [self.base]
        for i in range(3):
            parts.append(md5_hash[i])
        parts.append(md5_hash[3:])
        return os.path.join(*parts)

    @staticmethod
    def hash_key(key: str) -> str:
        """
        >>> DirCache.hash_key("something")
        '437b930db84b8079c2dd804a71936b5f'
        """
        return md5(key.encode()).hexdigest()


class Index:
    def __init__(self, data_dir: Path):
        self.data_dir: Path = data_dir

    @staticmethod
    def has_null_value(url: str) -> bool:
        """
        If the item isn't in cache, returns True
        If the item is in cache, but it doesn't have any values (i.e. empty
        json file and no srt data), then return True
        else return False (this has data)
        """
        pass

    def get(self, url: str) -> Optional[Metadata]:
        """
        Get data for the 'url' from cache, or None
        """
        pass

    def exists(self, url: str) -> bool:
        """
        Returns true/false, signifying whether or not the information
        for this url is already cached
        """
        return False

    def put(self, url: str) -> None:
        pass

    # not used but here as a library function, incase
    def delete(self, url: str) -> bool:
        """
        Returns true if item was deleted, false if it didn't exist
        """
        pass
