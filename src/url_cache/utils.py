import re
import warnings
from datetime import timedelta
from urllib.parse import unquote
from pathlib import Path
from typing import Union, Generator, Dict, Any

import backoff  # type: ignore[import]


def normalize_path(p: Union[str, Path]) -> Path:
    pth: Path
    if isinstance(p, Path):
        pth = p
    elif isinstance(p, str):
        pth = Path(p)
    else:
        raise TypeError("Expected 'str' or 'pathlib.Path', received {}".format(type(p)))
    return pth.expanduser().absolute()


def fibo_backoff() -> Generator[float, None, None]:
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


def clean_url(urlstr: str) -> str:
    """
    unquotes and removes whitespace from URLs
    https://docs.python.org/3/library/urllib.parse.html#urllib.parse.unquote
    """
    return unquote(urlstr).strip()


timedelta_regex = re.compile(
    r"^((?P<weeks>[\.\d]+?)w)?((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$"
)


# https://stackoverflow.com/a/51916936
def parse_timedelta_string(timedelta_str: str) -> timedelta:
    """
    This uses a syntax similar to the 'GNU sleep' command
    e.g.: 1w5d5h10m50s means '1 week, 5 days, 5 hours, 10 minutes, 50 seconds'
    """
    parts = timedelta_regex.match(timedelta_str)
    if parts is None:
        raise ValueError(
            f"Could not parse expiry time from {timedelta_str}.\nValid examples: '8h', '1w2d8h5m20s', '2m4s'"
        )
    time_params = {
        name: float(param) for name, param in parts.groupdict().items() if param
    }
    return timedelta(**time_params)  # type: ignore[arg-type]
