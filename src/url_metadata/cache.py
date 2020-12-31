import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Union, Any, Tuple
from pathlib import Path
from enum import auto, Enum

from .model import Metadata, Subtitles
from .dir_cache import DirCache

import srt  # type: ignore[import]


class MetadataFieldType(Enum):
    JSON = auto()
    STR = auto()
    DATETIME = auto()
    SUBTITLES = auto()


class MetadataField:
    """
    Represents one possible piece of metadata for a URL
    For example, the JSON info, the HTML summary or the subtitles
    """

    def __init__(self, filename: str, mtype: MetadataFieldType):
        self.filename = filename
        self.mtype = mtype

    def get(self, from_dir: str) -> Union[datetime, str, Dict[str, Any], Subtitles, None]:
        target: str = os.path.join(from_dir, self.filename)
        if not os.path.exists(target):
            return None
        with open(target, "r") as f:
            contents = f.read()
        if self.mtype == MetadataFieldType.JSON:
            data: Dict[str, Any] = json.loads(contents)
            return data
        elif self.mtype == MetadataFieldType.STR:
            return contents
        elif self.mtype == MetadataFieldType.DATETIME:
            return datetime.fromtimestamp(int(contents))
        elif self.mtype == MetadataFieldType.SUBTITLES:
            return list(srt.parse(contents))
        else:
            raise ValueError(f"Unsupported mtype of {self.mtype}")

    def put(self, from_dir: str, data: Any) -> None:
        target: str = os.path.join(from_dir, self.filename)
        with open(target, "w") as f:
            if self.mtype == MetadataFieldType.JSON:
                json.dump(data, f)
            elif self.mtype == MetadataFieldType.STR:
                f.write(data)
            elif self.mtype == MetadataFieldType.DATETIME:
                f.write(str(int(data.timestamp())))
            elif self.mtype == MetadataFieldType.SUBTITLES:
                f.write(srt.compose(data))
            else:
                raise ValueError(f"Unsupported mtype of {self.mtype}")


class MetadataCache:
    """
    Interface to the underlying DirCache, which serializes/deserializes information
    from the Metadata object into each individual file
    """

    def __init__(self, data_dir: Path):
        self.data_dir: Path = data_dir
        self.dir_cache = DirCache(str(self.data_dir))
        self.fields: List[Tuple[str, MetadataField]] = [
            ("info", MetadataField("metadata.json", MetadataFieldType.JSON)),
            ("html_summary", MetadataField("summary.html", MetadataFieldType.STR)),
            ("subtitles", MetadataField("subtitles.srt", MetadataFieldType.SUBTITLES)),
            ("timestamp", MetadataField("timestamp.txt", MetadataFieldType.DATETIME)),
        ]

    def get(self, url: str) -> Optional[Metadata]:
        """
        Get data for the 'url' from cache, or None
        """
        if not self.has(url):
            return None

        tdir: str = self.dir_cache.get(url)
        metadata = Metadata(url=url)

        for (attr, field) in self.fields:
            data = field.get(tdir)
            if data is not None:
                setattr(metadata, attr, data)

        return metadata

    def put(self, url: str, data: Metadata) -> str:
        """
        Replaces/puts the information from 'data' into the
        corresponding directory given the url

        Deletes previous cached information, if it exists for the URL
        """

        # delete if already cached
        if self.has(url):
            self.delete(url)

        tdir: str = self.dir_cache.put(url)

        for (attr, field) in self.fields:
            # get the data from the metadata object
            mdata = getattr(data, attr)
            if mdata is not None:
                field.put(tdir, mdata)

        return tdir

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


