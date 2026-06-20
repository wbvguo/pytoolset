from __future__ import annotations

import io
import sys

from pytoolset import CommandRunner
from pytoolset.parallel import _main

TAB = "\t"


# --- CommandRunner: row delivery ---


def test_row_as_argument_placeholder(tmp_path):
    # '{}' present -> row delivered as a single argv element (argv[1] under -c).
    cmd = f'{sys.executable} -c "import sys; sys.stdout.write(sys.argv[1])" {{}}'
    results = CommandRunner(cmd, log_dir=tmp_path).run(["s1\tA"])
    assert results[0].ok
    assert (tmp_path / "jobs_1.log").read_text() == "s1\tA"


def test_row_piped_to_stdin(tmp_path):
    # No '{}' -> row written to the command's stdin.
    cmd = f'{sys.executable} -c "import sys; sys.stdout.write(sys.stdin.read())"'
    results = CommandRunner(cmd, log_dir=tmp_path).run(["hello world"])
    assert results[0].ok
    assert (tmp_path / "jobs_1.log").read_text().strip() == "hello world"


def test_command_parses_its_own_columns(tmp_path):
    # The runner stays column-agnostic; the command splits the row itself.
    code = "import sys; print(sys.argv[1].split(chr(9))[1])"  # 2nd tab-column
    cmd = f'{sys.executable} -c "{code}" {{}}'
    results = CommandRunner(cmd, log_dir=tmp_path).run([f"s1{TAB}A", f"s2{TAB}B"])
    assert [r.returncode for r in results] == [0, 0]
    assert (tmp_path / "jobs_1.log").read_text().strip() == "A"
    assert (tmp_path / "jobs_2.log").read_text().strip() == "B"


# --- CommandRunner: scheduling / robustness ---


def test_results_in_input_order(tmp_path):
    cmd = f'{sys.executable} -c "pass" {{}}'
    results = CommandRunner(cmd, log_dir=tmp_path).run(["c", "a", "b"])
    assert [(r.index, r.row) for r in results] == [(1, "c"), (2, "a"), (3, "b")]


def test_blank_rows_skipped_and_line_endings_stripped(tmp_path):
    cmd = f'{sys.executable} -c "import sys; sys.stdout.write(sys.stdin.read())"'
    results = CommandRunner(cmd, log_dir=tmp_path).run(["x\n", "   ", "", "y\r\n"])
    assert [r.row for r in results] == ["x", "y"]
    assert (tmp_path / "jobs_1.log").read_text().strip() == "x"
    assert (tmp_path / "jobs_2.log").read_text().strip() == "y"


def test_nonzero_exit_does_not_raise(tmp_path):
    cmd = f'{sys.executable} -c "import sys; sys.stderr.write(\'boom\'); sys.exit(3)"'
    results = CommandRunner(cmd, log_dir=tmp_path).run(["r1"])
    assert results[0].returncode == 3
    assert not results[0].ok
    assert "boom" in (tmp_path / "jobs_1.err").read_text()


def test_malformed_command_does_not_raise(tmp_path):
    # Unbalanced quote -> shlex.split raises ValueError; captured as a failure.
    results = CommandRunner("echo 'oops", log_dir=tmp_path).run(["r1"])
    assert results[0].returncode == -1
    assert "failed to launch" in (tmp_path / "jobs_1.err").read_text()


def test_launch_failure_returns_minus_one(tmp_path):
    results = CommandRunner("definitely-not-real-xyz {}", log_dir=tmp_path).run(["a"])
    assert results[0].returncode == -1
    assert "failed to launch" in (tmp_path / "jobs_1.err").read_text()


def test_empty_input(tmp_path):
    assert CommandRunner("echo {}", log_dir=tmp_path).run([]) == []


def test_creates_log_dir(tmp_path):
    log_dir = tmp_path / "nested" / "logs"
    CommandRunner(f'{sys.executable} -c "pass"', log_dir=log_dir).run(["r1"])
    assert log_dir.is_dir()


# --- CLI (python -m pytoolset.parallel) ---


def test_cli_from_stdin(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("a\nb\n"))
    cmd = f'{sys.executable} -c "import sys; sys.stdout.write(sys.argv[1])" {{}}'
    rc = _main(["-c", cmd, "-o", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / "jobs_1.log").read_text() == "a"
    assert (tmp_path / "jobs_2.log").read_text() == "b"
    assert "2 ok, 0 failed" in capsys.readouterr().out


def test_cli_from_input_file(tmp_path, capsys):
    rows = tmp_path / "rows.txt"
    rows.write_text("a\nb\nc\n")
    cmd = f'{sys.executable} -c "pass" {{}}'
    rc = _main(["-c", cmd, "-i", str(rows), "-o", str(tmp_path)])
    assert rc == 0
    assert "3 ok, 0 failed" in capsys.readouterr().out


def test_cli_reports_failure(tmp_path, capsys):
    rows = tmp_path / "rows.txt"
    rows.write_text("0\n2\n")
    cmd = f'{sys.executable} -c "import sys; sys.exit(int(sys.argv[1]))" {{}}'
    rc = _main(["-c", cmd, "-i", str(rows), "-o", str(tmp_path)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "1 ok, 1 failed" in out
    assert "row 2" in out
