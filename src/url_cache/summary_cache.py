import os
import json
import warnings
from datetime import datetime
from typing import (
    Optional,
    List,
    Dict,
    Union,
    Any,
    Tuple,
    Callable,
    TypeVar,
    Type,
    Set,
    cast,
)
from pathlib import Path

from .exceptions import URLCacheException
from .common import Json
from .model import Summary
from .dir_cache import DirCache

import srt  # type: ignore[import]


T = TypeVar("T")


class FileParser:
    """
    Encapsulates some function which parses an underlying file for a field on the metadata
    """

    def __init__(
        self,
        name: str,
        ext: str,
        *,
        load_func: Callable[[Path], T],
        dump_func: Callable[[T, Path], None],
    ):
        # basename of a file, not a full path, just what
        # this is meant to match against
        self.name = name
        self.ext = ext
        self.load_func = load_func
        self.dump_func = dump_func

    @property
    def filename(self) -> str:
        return self.name + self.ext

    def matches(self, p: Path) -> bool:
        # instead of checking the extension directly, this just
        # checks if it starts/ends with what was provided
        # that way, you can have filenames like
        # epoch.datetime.txt to specify the loaded
        # type of some data
        return p.name.startswith(self.name) and p.name.endswith(self.ext)

    def load(self, p: Path) -> T:
        return self.load_func(p)

    def dump(self, data: T, p: Path) -> None:
        self.dump_func(data, p)


# functions to load/dump the supported types from files


def _load_file_json(p: Path) -> Json:
    loaded: Json = json.loads(p.read_text())
    return loaded


def _load_file_text(p: Path) -> str:
    return p.read_text()


def _load_file_subtitles(p: Path) -> List[srt.Subtitle]:
    return list(srt.parse(p.read_text()))


def _load_file_datetime(p: Path) -> datetime:
    return datetime.fromtimestamp(int(p.read_text()))


def _dump_file_json(data: Json, p: Path) -> None:
    if data == {}:
        return
    p.write_text(json.dumps(data))


def _dump_file_text(data: str, p: Path) -> None:
    p.write_text(data)


def _dump_file_subtitles(data: List[srt.Subtitle], p: Path) -> None:
    p.write_text(srt.compose(data))


def _dump_file_datetime(data: datetime, p: Path) -> None:
    p.write_text(str(int(data.timestamp())))


DEFAULT_FILE_PARSERS: List[FileParser] = [
    FileParser(
        name="url",
        ext=".txt",
        load_func=_load_file_text,
        dump_func=_dump_file_text,
    ),
    FileParser(
        name="metadata",
        ext=".json",
        load_func=_load_file_json,
        dump_func=_dump_file_json,
    ),
    FileParser(
        name="timestamp",
        ext=".datetime.txt",
        load_func=_load_file_datetime,
        dump_func=_dump_file_datetime,
    ),
    FileParser(
        name="html_summary",
        ext=".html",
        load_func=_load_file_text,
        dump_func=_dump_file_text,
    ),
    FileParser(
        name="subtitles",
        ext=".srt",
        load_func=_load_file_subtitles,
        dump_func=_dump_file_subtitles,
    ),
]


SUMMARY_ATTRS: Set[str] = set(Summary.__annotations__.keys())


class SummaryDirCache:
    """
    Interface to the underlying DirCache, which serializes/deserializes information
    from the Summary object into each individual file

    additional FileParser objects can be provided to parse custom data
    """

    def __init__(
        self, data_dir: Path, *, file_parsers: Optional[List[FileParser]] = None
    ):
        self.data_dir: Path = data_dir
        self.dir_cache = DirCache(str(self.data_dir))
        self.file_parsers: List[FileParser] = DEFAULT_FILE_PARSERS
        if file_parsers is not None:
            self.file_parsers.extend(file_parsers)
        # map name of attribute to the parsers
        self.attr_file_parsers: Dict[str, FileParser] = {
            parser.name: parser for parser in self.file_parsers
        }

    @staticmethod
    def _toplevel_attr(attr: str) -> bool:
        return attr in SUMMARY_ATTRS

    def _parse_file(self, p: Path) -> Tuple[str, Any]:
        for parser in self.file_parsers:
            if parser.matches(p):
                return parser.name, parser.load(p)
        # hmm - warning instead?
        raise URLCacheException(f"No way to parse {str(p)}")

    def _scan_directory(self, keydir: Path) -> Dict[str, Any]:
        """
        Given the target directory, recursively scans for files
        and applies the 'file_parsers' against each file
        """
        res = {}
        for target in keydir.rglob("*"):
            if not target.is_file():
                continue
            # ignore the key file, used to handle hashing/storing the URL
            if target.name == "key":
                continue
            name, data = self._parse_file(target)
            res[name] = data
        return res

    def get(self, url: str) -> Optional[Summary]:
        """
        Get data for the 'url' from cache, or None
        """
        if not self.has(url):
            return None

        key: Path = Path(self.dir_cache.get(url))

        # store info for this in a dict and splat onto dataclass at end
        sdict: Dict[str, Any] = {"url": url}

        for name, data in self._scan_directory(key).items():
            # top level attr on Summary dataclass
            if self.__class__._toplevel_attr(name):
                sdict[name] = data
            else:
                if "data" not in sdict:
                    sdict["data"] = {name: data}
                else:
                    sdict["data"][name] = data

        return Summary(**sdict)  # type: ignore[call-arg]

    def _put_helper(data: Any, target: Path, parser: FileParser) -> None:
        pass

    def put(self, url: str, data: Summary) -> str:
        """
        Replaces/puts the information from 'data' into the
        corresponding directory given the url

        Deletes previous cached information, if it exists for the URL
        """

        # delete if already cached
        #
        # TODO: dont delete info if data has None for that value?
        # i.e. if some website removed information, dont lose previously
        # cached info
        if self.has(url):
            self.delete(url)

        key: Path = Path(self.dir_cache.put(url))

        for attr in SUMMARY_ATTRS:
            val: Optional[Any] = getattr(data, attr, None)
            if val is None:
                continue

            base = key

            if attr == "data":
                # put any additional data into a subdirectory in the dircache
                assert isinstance(val, dict)
                base /= "data"
                base.mkdir(parents=True, exist_ok=True)
                for data_key, data_val in val.items():
                    psr = self.attr_file_parsers[data_key]
                    psr.dump(data_val, base / psr.filename)
            else:
                psr = self.attr_file_parsers[attr]
                psr.dump(val, base / psr.filename)

        return str(key)

    def has_null_value(self, url: str) -> bool:
        """
        If the item isn't in cache, raises DirCacheMiss
        If the item is in cache, but it doesn't have any values (i.e. empty
        json file and no srt data), then return True
        else return False (this has data)

        meant to be used to 'retry' getting url metadata, incase none was retrieved
        """
        # TODO: implement? may not be needed
        raise NotImplementedError

    # call underlying dircache functions

    def has(self, url: str) -> bool:
        """
        Returns true/false, signifying whether or not the information
        for this url is already cached
        """
        return self.dir_cache.exists(url)

    # not used but here as a library function, incase
    def delete(self, url: str) -> bool:
        """
        Returns true if item was deleted, false if it didn't exist
        """
        return self.dir_cache.delete(url)
