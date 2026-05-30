from pathlib import Path


def find_project_root(anchor=".", marker="pyproject.toml"):
    """Walk upward from anchor until a project marker file is found."""
    anchor = Path(anchor).resolve()
    start = anchor if anchor.is_dir() else anchor.parent

    for path in (start, *start.parents):
        if (path / marker).exists():
            return path

    raise FileNotFoundError(f"Could not find {marker!r} above {start}")
