from __future__ import annotations

import abc
import concurrent.futures
import contextlib
import doctest
import pathlib
import sys
from typing import Any, Callable, ClassVar

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum

import crc32c
from loguru import logger

CHUNK_SIZE_BYTES = 4096


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

    def get_checksum(self, path: pathlib.Path) -> str | int:
        """Return a checksum of the data at `path`."""
        return NotImplemented

    def is_valid_copy(self, src: pathlib.Path, *copy: pathlib.Path) -> bool:
        """Every `copy` has identical data to `src`."""
        return NotImplemented

    def is_valid_copytree(
        self, src_dir: pathlib.Path, copy_dir: pathlib.Path
    ) -> bool:
        """Every file in `src_dir` has identical data at same relative path in
        `copy_dir`.
        """
        return NotImplemented


class SerialValidater(DataValidater):

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
        checksum_fn: Callable[[bytes, Any], Any], path: pathlib.Path
    ) -> str | int:
        """Return a checksum of the data at `path`, breaking into chunks if
        necessary."""
        c = 0
        with path.open('rb') as f:
            while True:
                data = f.read(CHUNK_SIZE_BYTES)
                if not data:
                    break
                c = checksum_fn(data, c)
        return c

    @staticmethod
    def get_checksum(path: pathlib.Path) -> str | int:
        """Return a checksum of the data at `path`.

        >>> import tempfile
        >>> tmpfile = tempfile.NamedTemporaryFile(delete=False).name
        >>> tmpfile = pathlib.Path(tmpfile)
        >>> bool(SerialValidater().get_checksum(tmpfile))
        False
        >>> _ = pathlib.Path(tmpfile).write_text('test')
        >>> SerialValidater().get_checksum(tmpfile)
        2258662080
        """
        return __class__.checksum_in_chunks(  # type: ignore
            crc32c.crc32c, path
        )

    def is_valid_copy(self, src: pathlib.Path, *copy: pathlib.Path) -> bool:
        """Every `copy` has identical data to `src`.

        >>> import tempfile
        >>> tmpfile = pathlib.Path(tempfile.NamedTemporaryFile(delete=False).name)
        >>> SerialValidater().is_valid_copy(tmpfile, tmpfile, tmpfile)
        True
        >>> tmpfile2 = tmpfile.with_suffix('.2')
        >>> _ = tmpfile2.write_text('test')
        >>> SerialValidater().is_valid_copy(tmpfile, tmpfile, tmpfile2)
        False
        """
        if src.is_dir():
            return self.is_valid_copytree(src, *copy)
        src_checksum = self.get_checksum(src)
        return all(self.get_checksum(c) == src_checksum for c in copy)

    def is_valid_copytree(
        self, src_dir: pathlib.Path, copy_dir: pathlib.Path
    ) -> bool:
        """`copy_dir` has identical data to `src_dir`.

        Only checks contents of `src_dir`: extra files in `copy_dir` are
        ignored.

        >>> import tempfile
        >>> tmpdir = pathlib.Path(tempfile.mkdtemp())
        >>> tmpfile = pathlib.Path(tempfile.NamedTemporaryFile(delete=False).name)
        >>> SerialValidater().is_valid_copytree(tmpdir, tmpdir)
        True
        >>> SerialValidater().is_valid_copytree(tmpfile.parent, tmpdir)
        False
        """
        if not copy_dir.exists():
            logger.debug(f'{copy_dir} does not exist')
            return False
        for src_path in src_dir.glob('*'):
            copy_path = copy_dir / src_path.relative_to(src_dir)
            if not copy_path.exists():
                logger.debug(f'{copy_path} does not exist')
                return False
            # dirs only checked for existence
            if not self.is_valid_copy(src_path, copy_path):
                logger.debug(f'{copy_path} is not a valid copy')
                return False
        return True


if __name__ == '__main__':
    doctest.testmod(verbose=True)
