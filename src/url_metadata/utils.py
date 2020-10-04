import warnings
from urllib.parse import unquote
from pathlib import Path
from typing import Union, Iterator, Dict, Any

import backoff  # type: ignore[import]
from bs4 import BeautifulSoup  # type: ignore[import]


def normalize_path(p: Union[str, Path]) -> Path:
    if isinstance(p, Path):
        return p
    elif isinstance(p, str):
        return Path(p).expanduser().absolute()
    else:
        raise TypeError("Expected 'str' or 'pathlib.Path', received {}".format(type(p)))


def fibo_backoff() -> Iterator[int]:
    """
    Fibonacci backoff, with the first 6 elements consumed.
    In other words, this starts at 13, 21, ....
    """
    fib = backoff.fibo()
    for _ in range(6):
        next(fib)
    yield from fib


def backoff_warn(details: Dict[str, Any]) -> None:
    warning_msg: str = "Backing off {wait:0.1f} seconds afters {tries} tries with {args} {kwargs}".format(
        **details
    )
    warnings.warn(warning_msg)


def clean_url(url: str) -> str:
    """
    unquotes and removes whitespace from URLs
    https://docs.python.org/3/library/urllib.parse.html#urllib.parse.unquote
    """
    return unquote(url).strip()


def html_get_text(html_text: str) -> str:
    """
    Extracts text content from HTML text
    """
    # modified from https://stackoverflow.com/a/24618186/9348376
    soup = BeautifulSoup(html_text, features="html.parser")
    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()  # rip it out
    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in soup.get_text().splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    return "\n".join(chunk for chunk in chunks if chunk)
