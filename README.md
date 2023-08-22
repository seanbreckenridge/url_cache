[![PyPi version](https://img.shields.io/pypi/v/url_cache.svg)](https://pypi.python.org/pypi/url_cache) [![Python3.7|3.8|3.9](https://img.shields.io/pypi/pyversions/url_cache.svg)](https://pypi.python.org/pypi/url_cache) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

This is currently very alpha and in development, so expect changes to the API/interface. It aims to walk the line between extracting enough text/data for it to be useful, but no so much that it takes enormous amounts of space.

As it stands I'm sort of pessimistic this would ever be a silver bullet, getting useful info out of arbitrary HTML is hard, so you're sort of stuck writing parsers for each website you're interested in. However, I still use this frequently, especially as a cache for API information like described [below](#api-cache-examples)

Current TODOs:

- [ ] Add more sites using the [abstract interface](https://github.com/seanbreckenridge/url_cache/blob/master/src/url_cache/sites/abstract.py), to get more info from sites I use commonly. Ideally, should be able to re-use common scraper/parsers/API interface libraries in python, instead of recreating everything from scratch
- [ ] Create a (separate repo/project) daemon which handles configuring this and slowly requests things in the background as they become available through given sources; allow user to provide generators/inputs define include/exclude lists/regexes. Probably just integrate with [promnesia](https://github.com/karlicoss/promnesia) so avoid duplicating the work of searching for URLs on disk

## Installation

Requires `python3.7+`

To install with pip, run:

    python3 -m pip install url_cache

As this is still in development, for the latest changes install from git: `python3 -m pip install git+https://github.com/seanbreckenridge/url_cache`

## Rationale

A file system cache which saves URL metadata and summarizes content

This is meant to provide more context to any of my tools which use URLs. If I [watched some youtube video](https://github.com/seanbreckenridge/mpv-history-daemon) and I have a URL, I'd like to have the subtitles for it, so I can do a text-search over all the videos I've watched. If I [read an article](https://github.com/seanbreckenridge/browserexport), I want the article text! This requests, parses and abstracts away that data for me locally, so I can do something like:

```python
>>> from url_cache.core import URLCache
>>> u = URLCache()
>>> data = u.get("https://sean.fish/")
>>> data.metadata["images"][-1]
{'src': 'https://raw.githubusercontent.com/seanbreckenridge/glue/master/assets/screenshot.png', 'alt': 'screenshot', 'type': 'body_image', 'width': 600}
>>> data.metadata["description"]
"sean.fish; Sean Breckenridge's Home Page"
```

If I ever request that URL again, the information is grabbed from a local cache instead.

Generally, this uses:

- [`lassie`](https://github.com/michaelhelmick/lassie) to get generic metadata; the title, description, opengraph information, links to images/videos on the page.
- [`readability`](https://github.com/buriy/python-readability) to convert/compress HTML to a summary of the HTML content.

Site-Specific Extractors:

- [Youtube](./docs/url_cache/sites/youtube/subtitles_downloader.md): to get manual/auto-generated captions (converted to a `.srt` file) from Youtube URLs
- Stackoverflow (Just a basic URL preprocessor to reduce the possibility of conflicts/duplicate data)
- MyAnimeList (using [Jikan v4](https://docs.api.jikan.moe/))

This is meant to be extendible -- so its possible for you to write your own extractors/file loaders/dumpers (for new formats (e.g. `srt`)) for sites you use commonly and pass those to `url_cache.core.URLCache` to extract richer data for those sites. Otherwise, it saves the information from `lassie` and the summarized HTML using `readability` for each URL.

To avoid scope creep, this probably won't support:

- Converting the HTML summary to text (use something like the `lynx` command below)
- Minimizing HTML - run something like `find ~/.local/share/url_cache/ -name '*.html' -exec <some tool/script that minimizes in place> \;` instead -- the data is just stored in individual files in the data directory

### Usage:

In Python, this can be configured by using the `url_cache.core.URLCache` class: For example:

```python
import logging
from url_cache.core import URLCache

# make requests every 2 seconds
# debug logs
# save to a folder in my home directory
cache = URLCache(loglevel=logging.DEBUG, sleep_time=2, cache_dir="~/Documents/urldata")
c = cache.get("https://github.com/seanbreckenridge")
# just request information, don't read/save to cache
data = cache.request_data("https://www.wikipedia.org/")
```

For more information, see [the docs](./docs/url_cache/core.md)

The CLI interface provides some utility commands to get/list information from the cache.

```
Usage: url_cache [OPTIONS] COMMAND [ARGS]...

Options:
  --cache-dir PATH                Override default cache directory location
  --debug / --no-debug            Increase log verbosity
  --sleep-time INTEGER            How long to sleep between requests
  --summarize-html / --no-summarize-html
                                  Use readability to summarize html. Otherwise
                                  saves the entire HTML document

  --skip-subtitles / --no-skip-subtitles
                                  Skip downloading Youtube Subtitles
  --subtitle-language TEXT        Subtitle language for Youtube Subtitles
  --help                          Show this message and exit.

Commands:
  cachedir  Prints the location of the local cache directory
  export    Print all cached information as JSON
  get       Get information for one or more URLs Prints results as JSON
  in-cache  Prints if a URL is already cached
  list      List all cached URLs
```

An environment variable `URL_CACHE_DIR` can be set, which changes the default cache directory.

### API Cache Examples

I've also successfully used this to cache responses from API results in some of my projects, by subclassing and overriding the `request_data` function. I just make a request and return a summary, and it transparently caches the rest. See:

- [`albums/discogs_cache`](https://github.com/seanbreckenridge/albums/blob/9d296c4abb8e9e16c8dd410aeae8e5bb760008de/nextalbums/discogs_cache.py)
- [`my_feed/tmdb`](https://github.com/seanbreckenridge/my_feed/blob/master/src/my_feed/sources/trakt/tmdb.py)
- [`dbsentinel/metadata`](https://github.com/seanbreckenridge/dbsentinel/blob/accfc70485644d8966a582204c6c47839d2d874e/mal_id/metadata_cache.py)

### CLI Examples

The `get` command emits `JSON`, so it could with other tools (e.g. [`jq`](https://stedolan.github.io/jq/)) used like:

```shell
$ url_cache get "https://click.palletsprojects.com/en/7.x/arguments/" | \
  jq -r '.[] | .html_summary' | lynx -stdin -dump | head -n 5
Arguments

   Arguments work similarly to [1]options but are positional. They also
   only support a subset of the features of options due to their
   syntactical nature. Click will also not attempt to document arguments
```

```shell
$ url_cache export | jq -r '.[] | .metadata | .title'
seanbreckenridge - Overview
Arguments — Click Documentation (7.x)
```

```shell
url_cache list --location
/home/sean/.local/share/url_cache/data/2/c/7/6284b2f664f381372fab3276449b2/000
/home/sean/.local/share/url_cache/data/7/5/1/70fc230cd88f32e475ff4087f81d9/000
```

```shell
# to make a backup of the cache directory
$ tar -cvzf url_cache.tar.gz "$(url_cache cachedir)"
```

Accessible through the `url_cache` script and `python3 -m url_cache`

### Implementation Notes

This stores all of this information as individual files in a cache directory. In particular, it `MD5` hashes the URL and stores information like:

```
.
└── a
    └── a
        └── e
            └── cf0118bb22340e18fff20f2db8abd
                └── 000
                    ├── data
                    │   └── subtitles.srt
                    ├── key
                    ├── metadata.json
                    └── timestamp.datetime.txt
```

In other words, this is a file system hash table which implements separate chaining.

You're free to delete any of the directories in the cache if you want, this doesn't maintain a strict index, it uses a hash of the URL and then searches for a matching `key` file.

By default this waits 5 seconds between requests. Since all the info is cached, I use this by requesting all the info from one data source (e.g. my bookmarks, or videos I've watched recently) in a loop in the background, which saves all the information to my computer. The next time I do that same loop, it doesn't have to make any requests and it just grabs all the info from local cache.

Originally created for [`HPI`](https://github.com/seanbreckenridge/HPI).

---

### Testing

```
git clone 'https://github.com/seanbreckenridge/url_cache'
cd ./url_cache
pip install '.[testing]'
mypy ./src/url_cache
flake8 ./src/url_cache
pytest
```
