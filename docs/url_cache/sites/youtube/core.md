Module url_cache.sites.youtube.core
===================================

Functions
---------

    
`get_yt_video_id(url: str) ‑> Optional[str]`
:   Returns Video_ID extracting from the given url of Youtube
    Returns None if youtube ID could not be extracted
    
    Examples of URLs:
      Valid:
        'http://youtu.be/_lOT2p_FCvA',
        'www.youtube.com/watch?v=_lOT2p_FCvA&feature=feedu',
        'http://www.youtube.com/embed/_lOT2p_FCvA',
        'http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US',
        'https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6',
        'youtube.com/watch?v=_lOT2p_FCvA',
      Invalid:
        'youtu.be/watch?v=_lOT2p_FCvA',

Classes
-------

`Youtube(uc: URLCache)`
:   Youtube site extractor to get subtitles for videos

    ### Ancestors (in MRO)

    * url_cache.sites.abstract.AbstractSite
    * abc.ABC