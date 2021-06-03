Module url_cache.sites.youtube.subtitles_downloader
===================================================
Downloads subtitles from youtube

Functions
---------

    
`download_subs(video_identifier: str, target_language: str) ‑> str`
:   

    
`get_sub_track_urls(video_info: Dict[str, Any]) ‑> Dict[str, Any]`
:   

    
`get_subs_data(subs_url: str) ‑> str`
:   

    
`get_video_info(video_id: str) ‑> Dict[str, Any]`
:   

    
`select_target_lang_track_url(track_urls: Dict[str, Any], target_language: str) ‑> str`
:   

Classes
-------

`YoutubeSubtitlesException(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException