Module url_cache.utils
======================

Functions
---------

    
`backoff_warn(details: Dict[str, Any]) ‑> NoneType`
:   

    
`clean_url(urlstr: str) ‑> str`
:   unquotes and removes whitespace from URLs
    https://docs.python.org/3/library/urllib.parse.html#urllib.parse.unquote

    
`fibo_backoff() ‑> Iterator[int]`
:   Fibonacci backoff, with the first 6 elements consumed.
    In other words, this starts at 13, 21, ....

    
`normalize_path(p: Union[str, pathlib.Path]) ‑> pathlib.Path`
: