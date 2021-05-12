"""
Handles converting the Youtube subtitles to an SRT file
"""

import re
import html

from typing import List, Tuple, Optional, Union


# Conversion code from
# http://code.activestate.com/recipes/577459-convert-a-youtube-transcript-in-srt-subtitle/
pat = re.compile(r'<?text start="(\d+\.\d+)" dur="(\d+\.\d+)">(.*)</text>?')


def format_srt_time(sec_time: Union[str, float]) -> str:
    """Convert a time in seconds (google's transcript) to srt time format."""
    sec, micro = str(sec_time).split(".")
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return "{:02}:{:02}:{:02},{}".format(h, m, s, micro)


def format_srt_line(i: int, elms: Tuple[str, str, str]) -> str:
    """Print a subtitle in srt format."""
    return "{}\n{} --> {}\n{}\n\n".format(
        i,
        format_srt_time(elms[0]),
        format_srt_time(float(elms[0]) + float(elms[1])),
        convert_html(elms[2]),
    )


def convert_html(text: str) -> str:
    return html.unescape(text)


def to_srt(buf: str) -> str:
    out_srt: List[str] = []
    srt_data: List[str] = "".join(buf.replace("\n", " ")).split("><")
    i: int = 0
    for text in srt_data:
        parsed: Optional[Tuple[str, str, str]] = parse_line(text)
        if parsed is not None:
            i += 1
            out_srt.append(format_srt_line(i, parsed))
    out_srt_string = "".join(out_srt)
    return out_srt_string


def parse_line(text: str) -> Optional[Tuple[str, str, str]]:
    """Parse a subtitle."""
    m = re.match(pat, text)
    if m:
        return m.group(1), m.group(2), m.group(3)
    else:
        return None
