"""``python -m pytoolset``: list the tools you can run with ``-m``."""

from __future__ import annotations

_TOOLS = {
    "select": "produce a list of ids (metadata column, range, or list) to stdout",
    "parallel": "run a command template once per id, concurrently",
    "youtube": "download a YouTube video or playlist via yt-dlp",
    "session": "print Python/platform details and loaded-package versions",
}


def main() -> int:
    print("pytoolset — run a tool with: python -m pytoolset.<tool>\n")
    for name, description in _TOOLS.items():
        print(f"  python -m pytoolset.{name:<9} {description}")
    return 0


raise SystemExit(main())
