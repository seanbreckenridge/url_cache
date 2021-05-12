# sanity check to make sure the CLI is documented

from url_cache.__main__ import DEFAULT_OPTIONS, OPTIONS_HELP


def test_flags_help() -> None:
    assert set(DEFAULT_OPTIONS.keys()) == set(OPTIONS_HELP.keys())
