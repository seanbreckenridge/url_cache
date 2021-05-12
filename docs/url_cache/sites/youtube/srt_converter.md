Module url_cache.sites.youtube.srt_converter
============================================
Handles converting the Youtube subtitles to an SRT file

Functions
---------

    
`convert_html(text: str) ‑> str`
:   

    
`format_srt_line(i: int, elms: Tuple[str, str, str]) ‑> str`
:   Print a subtitle in srt format.

    
`format_srt_time(sec_time: Union[str, float]) ‑> str`
:   Convert a time in seconds (google's transcript) to srt time format.

    
`parse_line(text: str) ‑> Optional[Tuple[str, str, str]]`
:   Parse a subtitle.

    
`to_srt(buf: str) ‑> str`
: