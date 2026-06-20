"""Filter CSV and TSV rows by the value of one column."""

from __future__ import annotations

import argparse
import csv
import sys
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path


def select_rows(
    rows: Iterable[Mapping[str, str]],
    column: str,
    *,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
) -> Iterator[Mapping[str, str]]:
    """Yield rows whose ``column`` value passes the requested filter."""
    if include is not None and exclude is not None:
        raise ValueError("include and exclude are mutually exclusive")

    wanted = set(include if include is not None else exclude or ())
    keep_matches = include is not None
    for row in rows:
        if column not in row:
            raise KeyError(f"column {column!r} not found")
        if (row[column] in wanted) == keep_matches:
            yield row


def _delimiter(path: Path, value: str | None) -> str:
    if value is not None:
        return "\t" if value == r"\t" else value
    return "," if path.suffix.lower() == ".csv" else "\t"


def _values(item: str) -> set[str]:
    """Read comma-separated values or a file containing one value per line."""
    path = Path(item)
    if path.is_file():
        values = {line.strip() for line in path.read_text().splitlines()}
    else:
        values = {value.strip() for value in item.split(",")}
    values.discard("")
    return values


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Filter rows in a CSV or TSV file.")
    parser.add_argument("file", type=Path, help="input .csv or .tsv file")
    parser.add_argument("-c", "--column", required=True, help="column to filter")
    filters = parser.add_mutually_exclusive_group(required=True)
    filters.add_argument(
        "-i", "--include", metavar="VALUES_OR_FILE",
        help="keep comma-separated values or values from a file (one ID per line)",
    )
    filters.add_argument(
        "-e", "--exclude", metavar="VALUES_OR_FILE",
        help="drop comma-separated values or values from a file (one ID per line)",
    )
    parser.add_argument(
        "-d", "--delimiter", help=r"delimiter override (for example ',' or '\t')"
    )
    args = parser.parse_args(argv)

    delimiter = _delimiter(args.file, args.delimiter)
    with args.file.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames or args.column not in reader.fieldnames:
            parser.error(f"column {args.column!r} not found in {args.file}")

        writer = csv.DictWriter(
            sys.stdout, fieldnames=reader.fieldnames, delimiter=delimiter,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            select_rows(
                reader,
                args.column,
                include=_values(args.include) if args.include else None,
                exclude=_values(args.exclude) if args.exclude else None,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
