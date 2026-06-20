from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path


def mkdir(path: str | os.PathLike[str]) -> Path:
    """Create a directory and its parents, skipping if it already exists.

    Args:
        path: The directory to create.

    Returns:
        The absolute, resolved path of the directory.
    """
    path = Path(path).resolve()
    if path.exists():
        print(f"{path} exists! Skip creating...")
    else:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_absolute_path(path: str | os.PathLike[str]) -> Path:
    """Return the absolute, resolved form of a path.

    Args:
        path: The path to resolve.

    Returns:
        The absolute, resolved path.
    """
    return Path(path).resolve()


def find_project_root(
    anchor: str | os.PathLike[str] = ".",
    marker: str = "pyproject.toml",
) -> Path:
    """Walk upward from an anchor until a project marker file is found.

    Args:
        anchor: The path to start searching from. Defaults to the current
            working directory (``"."``).
        marker: The marker file that identifies the project root. Defaults to
            ``"pyproject.toml"``.

    Returns:
        The first ancestor directory (including the anchor) that contains
        ``marker``.

    Raises:
        FileNotFoundError: If no ancestor directory contains ``marker``.
    """
    resolved = Path(anchor).resolve()
    start = resolved if resolved.is_dir() else resolved.parent

    for path in (start, *start.parents):
        if (path / marker).exists():
            return path

    raise FileNotFoundError(f"Could not find {marker!r} above {start}")


def find_file(
    name: str,
    path: str | os.PathLike[str] = ".",
    exclude_dir: Iterable[str] | None = None,
    hidden: bool = False,
) -> list[Path]:
    """Recursively search a directory tree for files matching a given name.

    Args:
        name: The file name to search for (matched against each entry's base name).
        path: The directory to start the search from. Defaults to the current
            working directory (``"."``).
        exclude_dir: Directory base names to skip during the search. Defaults to
            ``None``.
        hidden: Whether to descend into hidden folders (those whose name starts
            with a dot). Defaults to ``False``, i.e. hidden folders are skipped.

    Returns:
        A list of paths (relative to ``path``) for every match found. Returns an
        empty list if no match is found.

    Raises:
        NotADirectoryError: If ``path`` does not exist or is not a directory.
    """
    root = Path(path)
    if not root.is_dir():
        raise NotADirectoryError(f"Directory does not exist: {root}")

    excluded = set(exclude_dir) if exclude_dir is not None else set()
    matches: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune directories in place so os.walk does not descend into them.
        dirnames[:] = [
            d
            for d in dirnames
            if d not in excluded and (hidden or not d.startswith("."))
        ]
        if name in filenames:
            matches.append(Path(dirpath, name).relative_to(root))

    return matches
