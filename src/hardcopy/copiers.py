import abc
import doctest
import os
import pathlib
import subprocess

import hardcopy.utils as utils


class Copier(abc.ABC):
    @abc.abstractmethod
    def copy(self, src: pathlib.Path, dest: pathlib.Path, *args, **kwargs) -> None:
        """Copy `src` to `dest`."""
        raise NotImplementedError


class Robocopy(Copier):
    """Wrapper for robocopy. Windows-only.

    Launches in a subprocess, so we can't generate checksums
    while transferring data - we can just validate on either side.
    """

    @classmethod
    def copy(cls, src: pathlib.Path, dest: pathlib.Path, *args, **kwargs) -> None:
        """Copy `src` to `dest` using robocopy."""
        # TODO parse args, kwargs
        cls.run(os.fsdecode(src), os.fsdecode(dest), *args, **kwargs)

    @staticmethod
    def run(*args: str) -> None:
        """Run robocopy with the given string arguments.
            
        https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy
        cmd.append("/e") # incl subdirectories (including empty ones)
        cmd.append("/xn") # excl newer src files
        # cmd.append("/xo") # excl older src files
        # /xc = excl src with same timestamp, different size
        cmd.append("/j") # unbuffered i/o (for large files)
        cmd.extend(("/r:3", "/w:10")) # retry count, wait between retries (s)
        # cmd.append("/mt:24") # multi-threaded: n threads
        
        >>> Robocopy.run('/?') is None
        True
        """
        utils.assert_cli_tool('robocopy')
        if not all(isinstance(arg, str) for arg in args):
            raise TypeError(
                f'robocopy() only accepts string arguments. Got: {args}'
            )
        subprocess.run(['robocopy', '/mt:8', *args], check=False)


if __name__ == '__main__':
    doctest.testmod(verbose=True)
