from __future__ import annotations

import abc
import asyncio
import concurrent.futures
import doctest
import os
import pathlib
import sys
import tempfile

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum

import crc32c
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

    algorithm: str = Algorithms.CRC32C

    @staticmethod
    @abc.abstractmethod
    def get_checksum(path: PathLike) -> str | int:
        """Return a checksum of the data at `path`.

        >>> tmpfile = tempfile.NamedTemporaryFile(delete=False).name
        >>> bool(DataValidater.get_checksum(tmpfile))
        False
        >>> _ = pathlib.Path(tmpfile).write_text('test')
        >>> bool(DataValidater.get_checksum(tmpfile))
        True
        """
        return crc32c.crc32c(pathlib.Path(os.fsdecode(path)).read_bytes())

    @classmethod
    def is_valid_copy(cls, src: PathLike, *copy: PathLike) -> bool:
        """Every `copy` has identical data to `src`.

        >>> tmpfile = tempfile.NamedTemporaryFile(delete=False).name
        >>> DataValidater.is_valid_copy(tmpfile, tmpfile, tmpfile)
        True
        >>> tmpfile2 = pathlib.Path(tmpfile).with_suffix('.2')
        >>> _ = tmpfile2.write_text('test')
        >>> DataValidater.is_valid_copy(tmpfile, tmpfile, tmpfile2)
        False
        """
        src = pathlib.Path(os.fsdecode(src))
        if src.is_dir():
            return cls.is_valid_copytree(src, *copy)
        target = cls.get_checksum(src)
        return all(cls.get_checksum(path) == target for path in copy)

    @classmethod
    def is_valid_copytree(cls, src_dir: PathLike, copy_dir: PathLike) -> bool:
        """`copy_dir` has identical data to `src_dir`.

        Only checks contents of `src_dir`: extra files in `copy_dir` are
        ignored.

        >>> tmpdir = tempfile.TemporaryDirectory(suffix='test').name
        >>> tmpfile = tempfile.NamedTemporaryFile(delete=False).name
        >>> DataValidater.is_valid_copytree(tmpdir, tmpdir)
        True
        >>> DataValidater.is_valid_copytree(pathlib.Path(tmpfile).parent, tmpdir)
        False
        """
        src_dir = pathlib.Path(os.fsdecode(src_dir))
        copy_dir = pathlib.Path(os.fsdecode(copy_dir))
        futures = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for src_path in src_dir.rglob('*'):
                copy_path = copy_dir / src_path.relative_to(src_dir)
                futures.append(
                    executor.submit(copy_path.exists)
                )   # dirs only checked for existence
                futures.append(
                    executor.submit(cls.is_valid_copy, src_path, copy_path)
                )
                if any(
                    future.result() == False
                    for future in concurrent.futures.as_completed(futures)
                ):
                    return False
        return True


if __name__ == '__main__':
    doctest.testmod(verbose=True)
