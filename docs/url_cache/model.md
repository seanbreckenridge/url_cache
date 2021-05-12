Module url_cache.model
======================

Functions
---------

    
`dumps(data: Any) ‑> str`
:   Dump a Summary object to JSON

Classes
-------

`Summary(url: str, data: Dict[str, Any] = <factory>, metadata: Dict[str, Any] = <factory>, html_summary: Optional[str] = None, timestamp: Optional[datetime.datetime] = None)`
:   Represents all possible data for a URL
    
    URL
    Metadata (description, images, page metadata) - from Lassie
    HTML Summary (parsed with readability)
    Timestamp (when this information was scraped)
    Data (any other data extracted from this site)

    ### Class variables

    `data: Dict[str, Any]`
    :

    `html_summary: Optional[str]`
    :

    `metadata: Dict[str, Any]`
    :

    `timestamp: Optional[datetime.datetime]`
    :

    `url: str`
    :