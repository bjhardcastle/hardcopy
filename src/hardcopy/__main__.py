import os
import pathlib

from hardcopy.copiers import Robocopy
from hardcopy.types import PathLike
from hardcopy.validaters import ConcurrentValidater


def validate(src: PathLike, dest: PathLike) -> bool:
    return ConcurrentValidater().is_valid_copy(src, dest)

def copy(src: PathLike, dest: PathLike) -> None:
    attempts = 0
    while (
            (
            not pathlib.Path(os.fsdecode(dest)).exists()
            or not validate(src, dest)
            )
        and attempts < 3
    ):
        Robocopy.copy(src, dest)
        attempts += 1

