from __future__ import annotations

import os
from pathlib import Path


def mkdir(path: str | os.PathLike[str]) -> Path:
    """Create a directory and its parents; print a message if it already exists."""
    path = Path(path).resolve()
    if path.exists():
        print(f"{path} exists! Skip creating...")
    else:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_absolute_path(path: str | os.PathLike[str]) -> Path:
    """Return the absolute, resolved form of a path."""
    return Path(path).resolve()


def find_project_root(
    anchor: str | os.PathLike[str] = ".",
    marker: str = "pyproject.toml",
) -> Path:
    """Walk upward from anchor until a project marker file is found."""
    resolved = Path(anchor).resolve()
    start = resolved if resolved.is_dir() else resolved.parent

    for path in (start, *start.parents):
        if (path / marker).exists():
            return path

    raise FileNotFoundError(f"Could not find {marker!r} above {start}")
