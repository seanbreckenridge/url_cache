import os
import shutil
import tempfile

from url_metadata.cache import DirCache


def test_dir_cache_chaining():
    # create both
    # make sure they exist
    # delete the first
    # see if second exists
    d = tempfile.mkdtemp()
    dd = DirCache(d)
    k = "key1"
    assert not dd.exists(k)
    got_dir = dd.put(k)
    assert dd.exists(k)
    assert got_dir.rstrip("/").endswith("000")
    # move to 001 and try and find it there
    dirname = os.path.dirname(got_dir)
    # move and make sure it moved
    shutil.move(got_dir, os.path.join(dirname, "001"))
    assert os.path.exists(os.path.join(dirname, "001"))
    assert not os.path.exists(os.path.join(dirname, "000"))
    got_dir = dd.get(k)
    assert got_dir.rstrip("/").endswith("001")
    # re-create 000
    os.makedirs(os.path.join(dirname, "000"))
    # mess with keyfile
    with open(os.path.join(dd.get(k), "key"), "a") as break_key:
        break_key.write("dsakfjaksjfksaf")
    # no keyfile matches this anymore
    assert not dd.exists(k)
    # try to create 002, to make sure it works
    got_dir = dd.put(k)
    assert got_dir.rstrip("/").endswith("002")
