from pathlib import Path


def mkdir(dir):
    """Create a directory and its parents; print a message if it already exists."""
    dir = Path(dir)
    if dir.exists():
        print(f"{dir} exists! Skip creating...")
    else:
        dir.mkdir(parents=True, exist_ok=True)
    return dir


def find_project_root(anchor=".", marker="pyproject.toml"):
    """Walk upward from anchor until a project marker file is found."""
    anchor = Path(anchor).resolve()
    start = anchor if anchor.is_dir() else anchor.parent

    for path in (start, *start.parents):
        if (path / marker).exists():
            return path

    raise FileNotFoundError(f"Could not find {marker!r} above {start}")
