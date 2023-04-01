from __future__ import annotations

import doctest
import os
import pathlib
import subprocess
import sys

from hardcopy.types import PathLike

ON_WINDOWS: bool = 'win' in sys.platform


def assert_cli_tool(executable: str) -> None:
    """Assert that `executable` can be found and used.

    >>> if ON_WINDOWS: assert_cli_tool("robocopy") == None
    True

    >>> assert_cli_tool("not-robocopy")
    Traceback (most recent call last):
    ...
    AssertionError

    """
    try:
        process = subprocess.run(
            [executable, '/?'],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        if not ON_WINDOWS and executable == 'robocopy':
            raise AssertionError(
                f'robocopy is only available on Windows: running on {sys.platform}'
            )
        raise AssertionError(f'{executable!r} could not be found in PATH.')
    else:
        if process.returncode != 16:
            raise AssertionError(
                f'{executable!r} returned exit status {process.returncode}.'
            )


def to_path(*path: PathLike) -> pathlib.Path | tuple[pathlib.Path, ...]:
    """Convert each `path` to a `pathlib.Path`.

    >>> to_path('test')
    WindowsPath('test')
    >>> to_path('test', 'test2')
    (WindowsPath('test'), WindowsPath('test2'))
    """
    if len(path) == 1:
        return pathlib.Path(os.fsdecode(path[0]))
    return tuple(pathlib.Path(os.fsdecode(p)) for p in path)


if __name__ == '__main__':
    doctest.testmod(verbose=True, optionflags=doctest.IGNORE_EXCEPTION_DETAIL)
