Module url_cache.sites.youtube.subtitles_downloader
===================================================

Functions
---------

    
`download_subs(video_identifier: str, target_language: str) ‑> str`
:   

    
`get_sub_track_urls(video_info: Dict[str, Any]) ‑> Dict[str, Any]`
:   

    
`get_subs_data(subs_url: str) ‑> str`
:   

    
`get_video_info(video_id: str) ‑> Dict[str, Any]`
:   Get video info. Scraping code inspired by:
    https://github.com/syzer/youtube-captions-scraper/blob/master/src/index.js

    
`select_target_lang_track_url(track_urls: Dict[str, Any], target_language: str) ‑> str`
:   

Classes
-------

`YoutubeSubtitlesException(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException