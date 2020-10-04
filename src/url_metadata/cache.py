"""
An hash-based, file system cache
"""

import os
import shutil
import json
from datetime import datetime, timezone
from hashlib import md5
from typing import Optional, List, Dict
from pathlib import Path
from functools import lru_cache

from .model import Metadata


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

    @lru_cache(32)
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


class MetadataCache:
    """
    Interface to the underlying DirCache, which serializes/deserializes information
    from the Metadata object into each individual file
    """

    _metadata_fp = "metadata.json"
    _subtitles_fp = "subtitles.srt"
    _html_fp = "summary.html"
    _summary_fp = "summary.txt"
    _timestamp_fp = "epoch_timestamp.txt"

    _handler_map = None

    def __init__(self, data_dir: Path):
        self.data_dir: Path = data_dir
        self.cache = DirCache(str(self.data_dir))

    @classmethod
    def _handler(cls) -> Dict[str, str]:
        if cls._handler_map is None:
            cls._handler_map = {
                "metadata": cls._metadata_fp,
                "subtitles": cls._subtitles_fp,
                "html": cls._html_fp,
                "text": cls._summary_fp,
                "timestamp": cls._timestamp_fp,
            }
        return cls._handler_map

    # helper to get a metadata file
    @classmethod
    def _path(cls, base: str, metadata_filename: str) -> Path:
        """
        >>> str(MetadataCache._path("/tmp/something", "html"))
        '/tmp/something/summary.html'
        """
        # raises keyerror on incorrect usage
        part: str = cls._handler()[metadata_filename]
        return Path(base) / part

    def get(self, url: str) -> Optional[Metadata]:
        """
        Get data for the 'url' from cache, or None
        """
        if not self.has(url):
            return None

        tdir: str = self.cache.get(url)
        metadata = Metadata(url=url)

        cl = self.__class__

        mpath: Path = cl._path(tdir, "metadata")
        if mpath.exists():
            metadata.info = json.loads(mpath.read_text())

        htmlpath: Path = cl._path(tdir, "html")
        if htmlpath.exists():
            metadata.html_summary = htmlpath.read_text()

        tpath: Path = cl._path(tdir, "text")
        if tpath.exists():
            metadata.text_summary = tpath.read_text()

        subpath: Path = cl._path(tdir, "subtitles")
        if subpath.exists():
            metadata.subtitles = subpath.read_text()

        tspath: Path = cl._path(tdir, "timestamp")
        if tspath.exists():
            metadata.timestamp = datetime.fromtimestamp(
                int(tspath.read_text().strip()), tz=timezone.utc
            )

        return metadata

    def put(self, url: str, data: Metadata) -> str:
        """
        Replaces/puts the information from 'data' into the
        corresponding directory given the url

        Deletes previous cached information, if it exists for the URL
        """

        # delete
        if self.has(url):
            self.delete(url)

        tdir: str = self.cache.put(url)

        cl = self.__class__

        # if metadata was parsed
        if data.info:
            with cl._path(tdir, "metadata").open("w") as meta_f:
                json.dump(data.info, meta_f)

        # if this has the html summary from readability
        if data.html_summary is not None:
            with cl._path(tdir, "html").open("w") as content_f:
                content_f.write(data.html_summary)

        if data.text_summary is not None:
            with cl._path(tdir, "text").open("w") as text_f:
                text_f.write(data.text_summary)

        # if this has subtitles
        if data.subtitles is not None:
            with cl._path(tdir, "subtitles").open("w") as sub_f:
                sub_f.write(data.subtitles)

        with cl._path(tdir, "timestamp").open("w") as tstamp_f:
            tstamp_f.write(str(int(data.timestamp.timestamp())))

        return tdir

    def has(self, url: str) -> bool:
        """
        Returns true/false, signifying whether or not the information
        for this url is already cached
        """
        return self.cache.exists(url)

    # not used but here as a library function, incase
    def delete(self, url: str) -> bool:
        """
        Returns true if item was deleted, false if it didn't exist
        """
        return self.cache.delete(url)

    def has_null_value(self, url: str) -> bool:
        """
        If the item isn't in cache, raises DirCacheMiss
        If the item is in cache, but it doesn't have any values (i.e. empty
        json file and no srt data), then return True
        else return False (this has data)

        meant to be used to 'retry' getting url metadata, incase none was retrieved
        """
        # TODO: implement? may not be needed
        pass
