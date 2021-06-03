Module url_cache.sites.abstract
===============================

Classes
-------

`AbstractSite(uc: URLCache)`
:   These are always run after the 'core' lassie/summarization information has been done,
    so these have access to the cached response through self._uc

    ### Ancestors (in MRO)

    * abc.ABC

    ### Descendants

    * url_cache.sites.stackoverflow.StackOverflow
    * url_cache.sites.youtube.core.Youtube

    ### Instance variables

    `logger: logging.Logger`
    :

    `response: Optional[requests.models.Response]`
    :

    ### Methods

    `extract_info(self, url: str, summary: url_cache.model.Summary) ‑> url_cache.model.Summary`
    :   Run requests, extract information from the cached response etc...

    `file_parsers(self) ‑> List[url_cache.summary_cache.FileParser]`
    :   Lets Sites specify custom file parsers dynamically in each Site
        Each Site's file_parsers are added to the URLCache when its instantiated

    `matches_site(self, url: str) ‑> bool`
    :   Return a boolean describing whether or not some URL matches this site extractor

    `preprocess_url(self, url: str) ‑> str`
    :   Preprocess/Restructure the URL in some way, to avoid duplicate work
        If it doesn't apply for this URL, you can return the url as its given
        
        For example, youtube has lots of different ways of structuring a URL
        for a single video, but they all return the same information