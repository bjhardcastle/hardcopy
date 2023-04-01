import pathlib
import tempfile
import random

import pytest

import hardcopy

src_dir = pathlib.Path(tempfile.mkdtemp()) / 'test'
dest_dir = pathlib.Path(tempfile.mkdtemp()) / 'test2'
src_file = src_dir / 'test.txt' # create a file
dest_file = dest_dir / src_file.relative_to(src_dir)

src_file.parent.mkdir(parents=True, exist_ok=True)
src_file.write_text(random.choice('abcdefghijklmnopqrstuvwxyz') * 1000)

def test_copy() -> None:
    hardcopy.Robocopy().copy(src_dir, dest_dir)
    assert src_file.read_bytes() == dest_file.read_bytes()

def test_validate() -> None:
    assert hardcopy.ConcurrentValidater().is_valid_copy(src_file, dest_file)
    
test_copy()
test_validate()