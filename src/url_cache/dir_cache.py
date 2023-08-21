"""
An hash-based, file system cache
"""

import os
import shutil
from typing import List
from hashlib import md5


class DirCacheMiss(Exception):
    pass


def subdirs(path: str) -> List[str]:
    """
    Returns a list of subdirectores (that exist) for a existing directory
    """
    return [f.path for f in os.scandir(path) if f.is_dir()]


def keyfile_matches_contents(key: str, path: str) -> bool:
    """
    Helper function to check if a file matches the key we're trying to find
    """
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
# the benefit that there is no index, with relatively fast lookup (using MD5)
# Directories can be deleted by the user whenever they'd like without issue.
class DirCache:
    """
    Underlying hash implementation.

    The input/key to the cache is a string, which is typically a URL.
    This stores the key at <target_dir>/key
    """

    def __init__(self, loc: str):
        self.base: str = loc
        os.makedirs(self.base, exist_ok=True)

    def get(self, key: str) -> str:
        """
        Receives some string key as input.
        Returns the directory for that key if it exists, else raises DirCacheMiss
        """
        base: str = self.base_dir_hashed_path(key)
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
        Receives a key to create a cache directory for.
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
        base: str = self.base_dir_hashed_path(key)
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

    def delete(self, key: str) -> bool:
        """
        Deletes the corresponding directory for a key, if it exists
        Returns True if something was deleted, else False
        """
        try:
            kdir = self.get(key)
            shutil.rmtree(kdir)
            return True
        except DirCacheMiss:
            return False

    def base_dir_hashed_path(self, key: str) -> str:
        """
        Receives the key as input. Computes the corresponding base directory for the hash

        >>> d = DirCache('/tmp')
        >>> d.base_dir_hashed_path("something")
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
