from __future__ import annotations

import abc
import asyncio
import concurrent.futures
import contextlib
import doctest
import logging
import os
import pathlib
import sys
import tempfile
from typing import Callable, ClassVar, Optional

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum
    
import crc32c
from loguru import logger

from hardcopy.types import PathLike


class Algorithms(StrEnum):
    """Checksum algorithms for validating data integrity."""

    CRC32 = 'crc32'
    CRC32C = 'crc32c'
    MD5 = 'md5'
    SHA1 = 'sha1'
    SHA256 = 'sha256'
    SHA512 = 'sha512'


class DataValidater(abc.ABC):
    """Abstract base class for validating data integrity."""

    algorithm: str

    def get_checksum(self, path: PathLike) -> str | int:
        """Return a checksum of the data at `path`."""
        return NotImplemented

    def is_valid_copy(self, src: PathLike, *copy: PathLike) -> bool:
        """Every `copy` has identical data to `src`."""
        return NotImplemented

    def is_valid_copytree(self, src_dir: PathLike, copy_dir: PathLike) -> bool:
        """Every file in `src_dir` has identical data at same relative path in
        `copy_dir`.
        """
        return NotImplemented


class ConcurrentValidater(DataValidater):

    algorithm: str = Algorithms.CRC32C

    _threadpool: ClassVar[concurrent.futures.ThreadPoolExecutor]
    _processpool: ClassVar[concurrent.futures.ProcessPoolExecutor]

    @property
    def threadpool(self) -> concurrent.futures.ThreadPoolExecutor:
        with contextlib.suppress(AttributeError):
            return self._threadpool
        self.__class__._threadpool = concurrent.futures.ThreadPoolExecutor()
        return self.threadpool

    @property
    def processpool(self) -> concurrent.futures.ProcessPoolExecutor:
        with contextlib.suppress(AttributeError):
            return self._processpool
        self.__class__._processpool = concurrent.futures.ProcessPoolExecutor()
        return self.processpool

    @staticmethod
    def checksum_in_chunks(
        fn: Callable[[bytes], str | int], path: pathlib.Path
    ) -> str | int:
        """Return a checksum of the data at `path`, breaking into chunks if necessary."""
        return fn(path.read_bytes())

    @staticmethod
    def get_checksum(path: pathlib.Path) -> str | int:
        """Return a checksum of the data at `path`.

        >>> tmpfile = tempfile.NamedTemporaryFile(delete=False).name
        >>> bool(ConcurrentValidater().get_checksum(tmpfile))
        False
        >>> _ = pathlib.Path(tmpfile).write_text('test')
        >>> bool(ConcurrentValidater().get_checksum(tmpfile))
        True
        """
        return __class__.checksum_in_chunks(crc32c.crc32c, path)


    def is_valid_copy(self, src: pathlib.Path, *copy: pathlib.Path) -> bool:
        """Every `copy` has identical data to `src`.

        >>> tmpfile = tempfile.NamedTemporaryFile(delete=False).name
        >>> ConcurrentValidater().is_valid_copy(tmpfile, tmpfile, tmpfile)
        True
        >>> tmpfile2 = pathlib.Path(tmpfile).with_suffix('.2')
        >>> _ = tmpfile2.write_text('test')
        >>> ConcurrentValidater().is_valid_copy(tmpfile, tmpfile, tmpfile2)
        False
        """
        if src.is_dir():
            return self.is_valid_copytree(src, *copy)
        path_to_future = {
            path: self.threadpool.submit(self.get_checksum, path) for path in (src, *copy)
        }
        # checksums = self.processpool.map(
        #         self.get_checksum, (src, *copy)
        #     )
        return all(path_to_future[src].result() == path_to_future[c].result() for c in copy)

    def is_valid_copytree(self, src_dir: PathLike, copy_dir: PathLike) -> bool:
        """`copy_dir` has identical data to `src_dir`.

        Only checks contents of `src_dir`: extra files in `copy_dir` are
        ignored.

        >>> tmpdir = tempfile.TemporaryDirectory(suffix='test').name
        >>> tmpfile = tempfile.NamedTemporaryFile(delete=False).name
        >>> ConcurrentValidater().is_valid_copytree(tmpdir, tmpdir)
        True
        >>> ConcurrentValidater().is_valid_copytree(pathlib.Path(tmpfile).parent, tmpdir)
        False
        """
        src_dir = pathlib.Path(os.fsdecode(src_dir))
        copy_dir = pathlib.Path(os.fsdecode(copy_dir))
        future_to_path: dict[concurrent.futures.Future, pathlib.Path] = {}
        for src_path in src_dir.glob('*'):
            copy_path = copy_dir / src_path.relative_to(src_dir)
            if not copy_path.exists():
                bad_path = copy_path
                break
            # dirs only checked for existence
            future_to_path.update(
                {
                    self.threadpool.submit(
                        self.is_valid_copy, src_path, copy_path
                    ): src_path
                }
            )
        else:
            for future in concurrent.futures.as_completed(f for f in future_to_path):
                if future.result() == False:
                    bad_path = future_to_path[future]
                    break
            else:
                return True

        for future in future_to_path:
            future.cancel()

        if bad_path.exists():
            logger.debug(f'{bad_path} is not a valid copy')
        else:
            logger.debug(f'{bad_path} does not exist')

        return False


if __name__ == '__main__':
    doctest.testmod(verbose=True)
