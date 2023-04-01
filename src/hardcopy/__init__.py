"""
Copy tool with validation for Windows, wrapping Robocopy.

>>> from hardcopy import hardcopy

>>> import tempfile, pathlib
>>> tmpdir = pathlib.Path(tempfile.mkdtemp())

>>> hardcopy(tmpdir, tmpdir.with_name('hardcopy'))
"""
from __future__ import annotations

import doctest

from loguru import logger

import hardcopy.utils as utils
from hardcopy.copiers import Robocopy as Copier
from hardcopy.types import PathLike
from hardcopy.validaters import SerialValidater as Validater


def hardcopy(src: PathLike, dest: PathLike) -> None:
    """Copy `src` to `copy` using Robocopy then validate."""
    src, dest = utils.to_path(src, dest)
    attempts = 0
    while attempts < 3 and not dest.exists():
        copy(src, dest)
        try:
            validate(src, dest)
        except AssertionError:
            logger.warning(f'Validation failed: {src} <- {dest}')
            attempts += 1
        else:
            return None
    validate(src, dest)   # raises AssertionError if validation fails


def validate(src: PathLike, copy: PathLike) -> None:
    """Validate that `copy` contains identical data to `src` or raise
    AssertionError.

    Extra files in `copy` are ignored.

    >>> import tempfile, pathlib
    >>> tmpdir = pathlib.Path(tempfile.mkdtemp())
    
    >>> validate(tmpdir, tmpdir.with_name('clone'))
    
    >>> validate(tmpdir, tmpdir / 'fugazi')
    Traceback (most recent call last):
    ...
    AssertionError
    """
    src, copy = utils.to_path(src, copy)
    if not Validater().is_valid_copy(src, copy):
        raise AssertionError(f'{copy} is not a valid copy of {src}')
    logger.debug(f'Validated: {src} <- {copy}')


def copy(src: PathLike, dest: PathLike) -> None:
    """Copy `src` to `dest` using Robocopy.

    >>> import tempfile, pathlib
    >>> tmpdir = pathlib.Path(tempfile.mkdtemp())
    
    >>> copy(tmpdir, tmpdir.with_name('clone'))
    """
    src, dest = utils.to_path(src, dest)
    Copier.copy(src, dest)
    logger.debug(f'Copied: {src} -> {dest}')


if __name__ == '__main__':
    doctest.testmod(verbose=True, optionflags=doctest.IGNORE_EXCEPTION_DETAIL)
