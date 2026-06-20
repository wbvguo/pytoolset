from __future__ import annotations

import pytest

from pytoolset import select_rows
from pytoolset.select import _main


ROWS = [
    {"id": "1", "sample": "A"},
    {"id": "2", "sample": "B"},
    {"id": "3", "sample": "C"},
]


def test_select_rows_includes_values():
    assert list(select_rows(ROWS, "id", include=["1", "3"])) == [ROWS[0], ROWS[2]]


def test_select_rows_excludes_values():
    assert list(select_rows(ROWS, "id", exclude=["2"])) == [ROWS[0], ROWS[2]]


def test_select_rows_rejects_two_filters():
    with pytest.raises(ValueError, match="mutually exclusive"):
        list(select_rows(ROWS, "id", include=["1"], exclude=["2"]))


def test_select_rows_rejects_missing_column():
    with pytest.raises(KeyError, match="missing"):
        list(select_rows(ROWS, "missing", include=["1"]))


def test_cli_filters_csv(tmp_path, capsys):
    source = tmp_path / "samples.csv"
    source.write_text("id,sample\n1,A\n2,B\n3,C\n")

    assert _main([str(source), "--column", "id", "--include", "1,3"]) == 0
    assert capsys.readouterr().out == "id,sample\n1,A\n3,C\n"


def test_cli_filters_tsv(tmp_path, capsys):
    source = tmp_path / "samples.tsv"
    source.write_text("id\tsample\n1\tA\n2\tB\n3\tC\n")

    assert _main([str(source), "-c", "sample", "--exclude", "B"]) == 0
    assert capsys.readouterr().out == "id\tsample\n1\tA\n3\tC\n"


def test_cli_reads_include_values_from_file(tmp_path, capsys):
    source = tmp_path / "samples.csv"
    source.write_text("id,sample\n1,A\n2,B\n3,C\n")
    ids = tmp_path / "include.txt"
    ids.write_text("1\n\n3\n")

    assert _main([str(source), "-c", "id", "-i", str(ids)]) == 0
    assert capsys.readouterr().out == "id,sample\n1,A\n3,C\n"


def test_cli_reads_exclude_values_from_file(tmp_path, capsys):
    source = tmp_path / "samples.tsv"
    source.write_text("id\tsample\n1\tA\n2\tB\n3\tC\n")
    ids = tmp_path / "exclude.txt"
    ids.write_text("2\n")

    assert _main([str(source), "-c", "id", "-e", str(ids)]) == 0
    assert capsys.readouterr().out == "id\tsample\n1\tA\n3\tC\n"


def test_cli_requires_one_filter(tmp_path):
    source = tmp_path / "samples.csv"
    source.write_text("id,sample\n1,A\n")

    with pytest.raises(SystemExit):
        _main([str(source), "--column", "id"])
