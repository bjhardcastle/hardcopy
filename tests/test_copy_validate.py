import pathlib
import tempfile
import random
import timeit
import concurrent.futures

import pytest

import hardcopy

# src_dir = pathlib.Path(tempfile.mkdtemp())
dest_dir = pathlib.Path(tempfile.mkdtemp())
src_dir = pathlib.Path('C:/Users/BEN~1.HAR/AppData/Local/Temp/tmpqbkjv4jq')
dest_dir = pathlib.Path('C:/Users/BEN~1.HAR/AppData/Local/Temp/tmpcr3cju3j')
for _ in dest_dir.iterdir():
    _.unlink()
    
# with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
#     for n in range(20):
#         s = src_dir / f'{n}.txt'
#         s.parent.mkdir(parents=True, exist_ok=True)
#         s.touch(exist_ok=True)
#         pool.submit(s.write_text, random.choice('abcdefghijklmnopqrstuvwxyz') * 100_000_000)
# pool.shutdown(wait=True)

    
# src_file = src_dir / 'test.txt' # create a file
# dest_file = dest_dir / src_file.relative_to(src_dir)

# src_file.parent.mkdir(parents=True, exist_ok=True)
# src_file.write_text(random.choice('abcdefghijklmnopqrstuvwxyz') * 1000)

def test_copy() -> None:
    hardcopy.Robocopy().copy(src_dir, dest_dir)
    # assert src_file.read_bytes() == dest_file.read_bytes()

def test_validate() -> None:
    assert hardcopy.ConcurrentValidater().is_valid_copy(src_dir, dest_dir)


if __name__ == '__main__':
    # test_copy()
    print(timeit.timeit(test_copy, number=1) ,'seconds')
    print(timeit.timeit(test_validate, number=1) ,'seconds')