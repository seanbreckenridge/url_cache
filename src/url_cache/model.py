from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass, field, is_dataclass, asdict

from .common import Json

import simplejson


@dataclass
class Summary:
    """
    Represents all possible data for a URL

    URL
    Metadata (description, images, page metadata) - from Lassie
    HTML Summary (parsed with readability)
    Timestamp (when this information was scraped)
    Data (any other data extracted from this site)
    """

    url: str
    # each key in the Json object corresponds to a file
    # in the ./data subdirectory
    data: Json = field(default_factory=dict)
    metadata: Json = field(default_factory=dict)
    html_summary: Optional[str] = None
    timestamp: Optional[datetime] = None


def _default(o: Any) -> Any:
    if is_dataclass(o):
        return asdict(o)
    elif isinstance(o, datetime):
        return str(o)
    raise TypeError(f"no way to serialize {o} {type(o)}")


def dumps(data: Any) -> str:
    """
    Dump a Summary object to JSON
    """
    return simplejson.dumps(data, default=_default, namedtuple_as_object=True)
