import json
from datetime import datetime
from typing import (
    Optional,
    Generic,
    List,
    Dict,
    Any,
    Tuple,
    Callable,
    TypeVar,
    Set,
)
from pathlib import Path

from .exceptions import URLCacheException
from .common import Json
from .model import Summary
from .dir_cache import DirCache


T = TypeVar("T")


class FileParser(Generic[T]):
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


def _load_file_datetime(p: Path) -> datetime:
    return datetime.fromtimestamp(int(p.read_text()))


def _dump_file_json(data: Json, p: Path) -> None:
    if data == {}:
        return
    p.write_text(json.dumps(data))


def _dump_file_text(data: str, p: Path) -> None:
    p.write_text(data)


def _dump_file_datetime(data: datetime, p: Path) -> None:
    p.write_text(str(int(data.timestamp())))


DEFAULT_FILE_PARSERS: List[FileParser[Any]] = [
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
]


SUMMARY_ATTRS: Set[str] = set(Summary.__annotations__.keys())
# url is already stored as the 'key' file, don't need store again
SUMMARY_ATTRS.remove("url")
IGNORE_FILES: Set[str] = set(["key", "url.txt"])


class SummaryDirCache:
    """
    Interface to the underlying DirCache, which serializes/deserializes information
    from the Summary object into each individual file

    additional FileParser objects can be provided to parse custom data
    """

    def __init__(
        self, data_dir: Path, *, file_parsers: Optional[List[FileParser[Any]]] = None
    ):
        self.data_dir: Path = data_dir
        self.dir_cache = DirCache(str(self.data_dir))
        self.file_parsers: List[FileParser[Any]] = DEFAULT_FILE_PARSERS
        if file_parsers is not None:
            self.file_parsers.extend(file_parsers)
        # map name of attribute to the parsers
        self.attr_file_parsers: Dict[str, FileParser[Any]] = {
            parser.name: parser for parser in self.file_parsers
        }

    def parse_file(self, p: Path) -> Tuple[str, Any]:
        """
        Takes a path and tries to parse it with each self.file_parsers
        """
        for parser in self.file_parsers:
            if parser.matches(p):
                return parser.name, parser.load(p)
        # hmm - warning instead?
        raise URLCacheException(f"No way to parse {str(p)}")

    def scan_directory(self, keydir: Path) -> Dict[str, Any]:
        """
        Given the target directory, recursively scans for files
        and applies the 'file_parsers' against each file
        """
        res = {}
        for target in keydir.rglob("*"):
            if not target.is_file():
                continue
            # ignore the key file, used to handle hashing/storing the URL
            if target.name in IGNORE_FILES:
                continue
            name, data = self.parse_file(target)
            res[name] = data
        return res

    def get(self, url: str) -> Optional[Summary]:
        """
        Get data for the 'url' from cache, or None if it doesn't exist
        """
        if not self.has(url):
            return None

        key: Path = Path(self.dir_cache.get(url))

        # store info for this in a dict and splat onto dataclass at end
        sdict: Dict[str, Any] = {"url": url}

        for attr_name, data in self.scan_directory(key).items():
            # top level attr on Summary dataclass
            if attr_name in SUMMARY_ATTRS:
                sdict[attr_name] = data
            else:
                # some additional data (e.g. subtitles), attach to 'data' field
                if "data" not in sdict:
                    sdict["data"] = {attr_name: data}
                else:
                    sdict["data"][attr_name] = data

        return Summary(**sdict)  # type: ignore[call-arg]

    def put(self, url: str, data: Summary) -> str:
        """
        Puts/Replaces the information from 'data' into the
        corresponding directory given the url

        Overwrites previous files/information if it exists for the URL
        """

        skey: str = self.dir_cache.put(url)
        key: Path = Path(skey)

        for attr in SUMMARY_ATTRS:
            # get the value from the Summary dataclass
            val: Optional[Any] = getattr(data, attr, None)
            if val is None:
                continue

            base = key

            if attr == "data":
                # put any additional data into a subdirectory in the dircache
                assert isinstance(val, dict)
                base /= "data"
                if val.keys():
                    base.mkdir(parents=True, exist_ok=True)
                for data_key, data_val in val.items():
                    psr = self.attr_file_parsers[data_key]
                    psr.dump(data_val, base / psr.filename)
            else:
                psr = self.attr_file_parsers[attr]
                psr.dump(val, base / psr.filename)

        return skey

    def has_null_value(self, url: str) -> bool:
        """
        Currently not Implemented

        If the item isn't in cache, raises DirCacheMiss
        If the item is in cache, but it doesn't have any values (i.e. empty
        json file and no srt data), then return True
        else return False (this has data)

        meant to be used to 'retry' getting url metadata, incase none was retrieved
        """
        # TODO: implement? may not be needed
        raise NotImplementedError

    def has(self, url: str) -> bool:
        """
        Returns true/false, signifying whether or not the information
        for this url is already cached

        calls the underlying DirCache.exists function
        """
        return self.dir_cache.exists(url)
