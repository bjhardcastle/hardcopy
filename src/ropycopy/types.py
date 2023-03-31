import os
import pathlib
from typing import Union

PathLike = Union[str, bytes, os.PathLike, pathlib.Path]
# https://peps.python.org/pep-0519/#provide-specific-type-hinting-support
# PathLike inputs are converted to pathlib.Path objects for os-agnostic filesystem operations.
# os.fsdecode(path: PathLike) is used where only a string is required.
