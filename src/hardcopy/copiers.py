import abc
import doctest
import os
import subprocess

import hardcopy.utils as utils
from hardcopy.types import PathLike


class Copier(abc.ABC):
    @abc.abstractmethod
    def copy(self, src: PathLike, dest: PathLike, *args, **kwargs) -> None:
        """Copy `src` to `dest`."""
        raise NotImplementedError


class Robocopy(Copier):
    """Wrapper for robocopy. Windows-only.

    Launches in a subprocess, so we can't generate checksums
    while transferring data - we can just validate on either side.
    """

    @classmethod
    def copy(cls, src: PathLike, dest: PathLike, *args, **kwargs) -> None:
        """Copy `src` to `dest` using robocopy."""
        # TODO parse args, kwargs
        cls.run(os.fsdecode(src), os.fsdecode(dest), *args, **kwargs)

    @staticmethod
    def run(*args: str) -> None:
        """Run robocopy with the given string arguments.

        >>> Robocopy.run('/?') is None
        True
        """
        utils.assert_cli_tool('robocopy')
        if not all(isinstance(arg, str) for arg in args):
            raise TypeError(
                f'robocopy() only accepts string arguments. Got: {args}'
            )
        subprocess.run(['robocopy', *args], check=False)


if __name__ == '__main__':
    doctest.testmod(verbose=True)
