"""Command-line dispatcher for pytoolset."""

from __future__ import annotations

import sys
from pathlib import Path

_TOOLS = {
    "select": "filter rows in a CSV or TSV file",
    "parallel": "run a command template once per id, concurrently",
}


def _print_help(prog: str) -> None:
    print(f"usage: {prog} <tool> [options]\n")
    print("tools:")
    for name, description in _TOOLS.items():
        print(f"  {name:<9} {description}")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    invoked_as = Path(sys.argv[0]).name
    prog = invoked_as if invoked_as in {"ptst", "pytoolset"} else "pytoolset"
    if not args or args[0] in {"-h", "--help"}:
        _print_help(prog)
        return 0

    tool, *tool_args = args
    if tool == "select":
        from .select import _main

        return _main(tool_args)
    if tool == "parallel":
        from .parallel import _main

        return _main(tool_args)

    print(f"pytoolset: unknown tool {tool!r}", file=sys.stderr)
    _print_help(prog)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
