import doctest
import subprocess
import sys

ON_WINDOWS: bool = 'win' in sys.platform


def assert_cli_tool(executable: str) -> None:
    """Assert that `executable` can be found and used.

    >>> if ON_WINDOWS: assert_cli_tool("robocopy") == None
    True

    >>> assert_cli_tool("not-robocopy")
    Traceback (most recent call last):
    ...
    AssertionError: 'not-robocopy' could not be found in PATH.

    """
    try:
        completed_process = subprocess.run(
            [executable, '/?'],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        if not ON_WINDOWS and executable == 'robocopy':
            raise AssertionError(
                f'robocopy is only available on Windows. You are running on: {sys.platform}'
            )
        raise AssertionError(f'{executable!r} could not be found in PATH.')
    else:
        if completed_process.returncode != 16:
            raise AssertionError(
                f'{executable!r} cannot be used: returned exit status {completed_process.returncode}.'
            )


if __name__ == '__main__':
    doctest.testmod(verbose=True)
