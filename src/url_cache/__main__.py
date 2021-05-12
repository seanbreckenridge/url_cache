"""
CLI interface
"""

import sys
import logging
from orjson import dumps
from pathlib import Path
from typing import List, Optional, Any

import click

from .core import (
    URLCache,
    Summary,
    DEFAULT_SLEEP_TIME,
    DEFAULT_OPTIONS,
    DEFAULT_LOGLEVEL,
)

# cache object for all commands
ucache: Optional[URLCache] = None


def summary_dumps(data: Any) -> str:
    return dumps(data).decode("utf-8")


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
@click.option(
    "--skip-subtitles",
    is_flag=True,
    default=DEFAULT_OPTIONS["skip_subtitles"],
    help="Don't attempt to download subtitles",
)
@click.option(
    "--subtitle-language",
    type=str,
    default=DEFAULT_OPTIONS["subtitle_language"],
    help="Subtitle language for Youtube captions",
)
def main(
    cache_dir: str,
    debug: bool,
    sleep_time: int,
    skip_subtitles: bool,
    subtitle_language: str,
) -> None:
    global ucache
    ucache = URLCache(
        loglevel=logging.DEBUG if debug else DEFAULT_LOGLEVEL,
        sleep_time=sleep_time,
        cache_dir=cache_dir,
        options={
            "subtitle_language": subtitle_language,
            "skip_subtitles": skip_subtitles,
        },
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
        click.echo(summary_dumps(sinfo_list))


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
        click.echo(summary_dumps(values))
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
    click.echo(summary_dumps({"cached": cached}))
    sys.exit(0 if cached else 1)


@main.command()
def export() -> None:
    """Print all cached information as JSON"""
    keyfiles: List[Path] = list_keys(ucache.cache_dir)  # type: ignore[union-attr]
    sinfo_list: List[Summary] = []
    for k in keyfiles:
        sinfo_list.append(ucache.get(k.read_text()))  # type: ignore[union-attr]
    click.echo(summary_dumps(sinfo_list))


@main.command()
def cachedir() -> None:
    """Prints the location of the local cache directory"""
    click.echo(str(ucache.cache_dir))  # type: ignore[union-attr]


if __name__ == "__main__":
    main(prog_name=__package__)
