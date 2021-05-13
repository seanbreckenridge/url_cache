Module url_cache.sites.stackoverflow
====================================

Classes
-------

`StackOverflow(uc: URLCache)`
:   StackOverflow extractor to normalize question IDs/extract question/answers

    ### Ancestors (in MRO)

    * url_cache.sites.abstract.AbstractSite
    * abc.ABC

    ### Methods

    `extract_question_id(self, url: str) ‑> Optional[int]`
    :   Extract a stackoverflow question ID from a URL