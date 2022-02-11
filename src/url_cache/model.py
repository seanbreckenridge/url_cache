from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

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


def dumps(data: Any) -> str:
    """
    Dump a Summary object to JSON
    """
    return simplejson.dumps(data, namedtuple_as_object=True)
