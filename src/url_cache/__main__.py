"""
CLI interface
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional, Callable, Dict

import click

from .core import (
    URLCache,
    Summary,
    DEFAULT_SLEEP_TIME,
    DEFAULT_OPTIONS,
    DEFAULT_LOGLEVEL,
)
from .model import dumps

# cache object for all commands
ucache: Optional[URLCache] = None

OPTIONS_HELP: Dict[str, str] = {
    "subtitle_language": "Subtitle language for Youtube Subtitles",
    "skip_subtitles": "Skip downloading Youtube Subtitles",
    "summarize_html": "Use readability to summarize html. Otherwise saves the entire HTML document",
    "expiry_duration": "Rerequest if this amount of time has elapsed since the summary was saved (e.g. 5d, 10m)",
}


def _apply_option_flags(func: Callable[..., None]) -> Callable[..., None]:
    """
    dynamically create click flags for each item in DEFAULT_OPTIONS
    """
    for key, val in DEFAULT_OPTIONS.items():
        flag_content = key.casefold().replace("_", "-")
        is_flag = type(val) == bool
        # create boolean flag if this is a on-off switch
        if is_flag:
            flag = f"--{flag_content}/--no-{flag_content}"
        else:
            flag = f"--{flag_content}"
        # supply key to the click option to specify target function
        # that string is then extracted below from the kwargs of main
        click_func = click.option(
            flag,
            key,
            is_flag=is_flag,
            default=val,
            required=False,
            help=OPTIONS_HELP[key] + f" [default: {val}]",
        )
        func = click_func(func)  # apply decorator
    return func


@click.group()
@click.option(
    "--cache-dir", type=click.Path(), help="Override default cache directory location"
)
@click.option(
    "--debug/--no-debug", is_flag=True, default=False, help="Increase log verbosity"
)
@click.option(
    "--sleep-time",
    type=int,
    default=DEFAULT_SLEEP_TIME,
    help="How long to sleep between requests",
)
@_apply_option_flags
def main(cache_dir: str, debug: bool, sleep_time: int, **kwargs: bool) -> None:
    global ucache
    # dynamically grab these from kwargs -- are created by _apply_option_flags
    options = {key: kwargs[key] for key in DEFAULT_OPTIONS.keys()}
    ucache = URLCache(
        loglevel=logging.DEBUG if debug else DEFAULT_LOGLEVEL,
        sleep_time=sleep_time,
        cache_dir=cache_dir,
        options=options,
    )


@main.command()
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    default=False,
    help="Don't print output, just cache URL",
)
@click.argument("url", nargs=-1, required=True)
def get(quiet: bool, url: str) -> None:
    """
    Get information for one or more URLs

    Prints results as JSON
    """
    sinfo_list: List[Summary] = []
    for u in url:
        sinfo_list.append(ucache.get(u))  # type: ignore[union-attr]
    if not quiet:
        click.echo(dumps(sinfo_list))


def list_keys(cache_dir: Path) -> List[Path]:
    """
    Helper function which returns the absolute path of all matched keyfiles
    """
    return [p.absolute() for p in cache_dir.rglob("*/key")]


@main.command()
@click.option("--json", is_flag=True, default=False, help="Print results as JSON")
@click.option(
    "--location",
    is_flag=True,
    default=False,
    help="Print directory location instead of URL",
)
def list(location: str, json: bool) -> None:
    """List all cached URLs"""
    keyfiles = list_keys(ucache.cache_dir)  # type: ignore[union-attr]
    values = []
    if location:
        for p in keyfiles:
            values.append(str(p.parent))
    else:
        for p in keyfiles:
            values.append(p.read_text().strip())
    if json:
        click.echo(dumps(values))
    else:
        for v in values:
            click.echo(v)


@main.command()
@click.argument("url", required=True)
def in_cache(url: str) -> None:
    """
    Prints if a URL is already cached
    """
    cached = ucache.in_cache(url)  # type: ignore[union-attr]
    click.echo(dumps({"cached": cached}))
    sys.exit(0 if cached else 1)


@main.command()
def export() -> None:
    """Print all cached information as JSON"""
    keyfiles: List[Path] = list_keys(ucache.cache_dir)  # type: ignore[union-attr]
    sinfo_list: List[Summary] = []
    for k in keyfiles:
        sinfo_list.append(ucache.get(k.read_text()))  # type: ignore[union-attr]
    click.echo(dumps(sinfo_list))


@main.command()
def cachedir() -> None:
    """Prints the location of the local cache directory"""
    click.echo(str(ucache.cache_dir))  # type: ignore[union-attr]


if __name__ == "__main__":
    main(prog_name=__package__)
