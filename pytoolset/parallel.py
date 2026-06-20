from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Outcome of a single row's command run by :class:`CommandRunner`.

    Attributes:
        index: The 1-based position of the row in the input.
        row: The input row the command was run for.
        command: The resolved command that ran (after any ``{}`` substitution),
            for display and debugging.
        returncode: The subprocess exit code, or ``-1`` if it never launched.
        log_file: Path to the file capturing the job's stdout.
        err_file: Path to the file capturing the job's stderr.
    """

    index: int
    row: str
    command: str
    returncode: int
    log_file: str
    err_file: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class CommandRunner:
    """Run a command once per input row, concurrently (think ``xargs -P``).

    This is a row-oriented parallel runner. It owns only the concurrency and the
    per-row logging; it does **not** parse columns or know anything about a row's
    structure. The command itself is responsible for interpreting each row.

    A bounded thread pool acts as the work queue: at most ``max_workers`` rows
    run at once and the rest wait their turn. Threads (not processes) are used
    because each job simply blocks waiting on its subprocess, which does the real
    work in its own OS process.

    Each row is delivered to the command in one of two ways:

    - If ``command`` contains ``placeholder`` (default ``"{}"``), the row is
      substituted in as a single argument and the command's stdin is left empty.
    - Otherwise, the row is written to the command's standard input.

    Either way the command receives the whole row and splits its own columns.

    A job's stdout and stderr are redirected to ``{log_dir}/{prefix}{index}.log``
    and ``{log_dir}/{prefix}{index}.err`` (``index`` is the 1-based row
    position). A failing job never raises into the caller: its non-zero return
    code (or ``-1`` if it could not start) is captured in the returned
    :class:`CommandResult`.

    Args:
        command: The command to run. May contain ``placeholder`` to receive the
            row as an argument; otherwise the row is piped to stdin.
        max_workers: Maximum number of rows to run concurrently. Defaults to
            ``None`` (:class:`~concurrent.futures.ThreadPoolExecutor` chooses).
        log_dir: Directory for the per-row log/err files. Defaults to ``"."``.
        prefix: Filename prefix for the per-row log/err files. Defaults to
            ``"jobs_"``.
        shell: Whether to run each command through the shell. Defaults to
            ``False`` (the command is split with :func:`shlex.split`).
        placeholder: The token replaced by the row when present in ``command``.
            Defaults to ``"{}"``.
    """

    def __init__(
        self,
        command: str,
        max_workers: int | None = None,
        log_dir: str | os.PathLike[str] = ".",
        prefix: str = "jobs_",
        shell: bool = False,
        placeholder: str = "{}",
    ) -> None:
        self.command = command
        self.max_workers = max_workers
        self.log_dir = log_dir
        self.prefix = prefix
        self.shell = shell
        self.placeholder = placeholder

    def _prepare(self, row: str) -> tuple[str | list[str], str | None]:
        """Resolve a row into the subprocess command and optional stdin text.

        Args:
            row: The input row.

        Returns:
            A ``(cmd, stdin_text)`` pair. ``cmd`` is what to hand to
            :func:`subprocess.run` (a string when ``shell`` is set, else an argv
            list). ``stdin_text`` is the row to feed on stdin, or ``None`` when
            the row was substituted into ``cmd`` as an argument instead.
        """
        has_placeholder = self.placeholder in self.command
        if self.shell:
            if has_placeholder:
                return self.command.replace(self.placeholder, shlex.quote(row)), None
            return self.command, row
        argv = shlex.split(self.command)
        if has_placeholder:
            return [token.replace(self.placeholder, row) for token in argv], None
        return argv, row

    def _run_one(self, index: int, row: str) -> CommandResult:
        cmd, stdin_text = self._prepare(row)
        display = cmd if isinstance(cmd, str) else shlex.join(cmd)
        log_path = os.path.join(self.log_dir, f"{self.prefix}{index}.log")
        err_path = os.path.join(self.log_dir, f"{self.prefix}{index}.err")
        with open(log_path, "w") as out, open(err_path, "w") as err:
            try:
                if stdin_text is None:
                    completed = subprocess.run(
                        cmd,
                        stdout=out,
                        stderr=err,
                        shell=self.shell,
                        stdin=subprocess.DEVNULL,
                        check=False,
                    )
                else:
                    completed = subprocess.run(
                        cmd,
                        stdout=out,
                        stderr=err,
                        shell=self.shell,
                        input=stdin_text + "\n",
                        text=True,
                        check=False,
                    )
                returncode = completed.returncode
            except (OSError, ValueError) as exc:
                # OSError: command not found / failed to launch.
                # ValueError: shlex.split could not parse the command
                # (e.g. an unbalanced quote). Neither must crash the batch.
                err.write(f"failed to launch command: {exc}\n")
                returncode = -1
        return CommandResult(
            index=index,
            row=row,
            command=display,
            returncode=returncode,
            log_file=log_path,
            err_file=err_path,
        )

    def run(self, rows: Iterable[str]) -> list[CommandResult]:
        """Run the command once per row, concurrently.

        Line endings are stripped from each row, and rows that are empty after
        stripping are ignored.

        Args:
            rows: The input rows (e.g. the lines of a file or stdin).

        Returns:
            One :class:`CommandResult` per non-blank row, in input order.
        """
        cleaned = [row.rstrip("\r\n") for row in rows]
        cleaned = [row for row in cleaned if row.strip()]
        if not cleaned:
            return []
        os.makedirs(self.log_dir, exist_ok=True)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._run_one, index, row)
                for index, row in enumerate(cleaned, start=1)
            ]
            return [f.result() for f in futures]


def _main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m pytoolset.parallel``.

    Reads rows from an input file (or stdin) and runs the command once per row,
    concurrently, then prints a summary.

    Args:
        argv: Argument list to parse. Defaults to ``None`` (uses ``sys.argv``).

    Returns:
        A process exit code: ``0`` if all jobs succeeded, ``1`` if any failed.
    """
    parser = argparse.ArgumentParser(
        prog="pytoolset.parallel",
        description="Run a command once per input row, concurrently, with "
        "per-row log/err files.",
    )
    parser.add_argument("-c", "--cmd", required=True,
                        help="command to run; include '{}' to receive the row as "
                        "an argument, otherwise the row is piped to stdin")
    parser.add_argument("-i", "--input", default=None,
                        help="input file of rows (default: read rows from stdin)")
    parser.add_argument("-j", "--jobs", type=int, default=None,
                        help="number of concurrent jobs (default: CPU-based)")
    parser.add_argument("-o", "--log-dir", default=".",
                        help="directory for per-row log/err files (default: cwd)")
    parser.add_argument("--prefix", default="jobs_", help="log filename prefix")
    parser.add_argument("--shell", action="store_true",
                        help="run via the shell instead of shlex.split")
    args = parser.parse_args(argv)

    if args.input is not None:
        with open(args.input) as fh:
            rows = fh.readlines()
    else:
        rows = sys.stdin.readlines()

    results = CommandRunner(
        args.cmd,
        max_workers=args.jobs,
        log_dir=args.log_dir,
        prefix=args.prefix,
        shell=args.shell,
    ).run(rows)

    if not results:
        print("no rows to run", file=sys.stderr)
        return 0

    failed = [r for r in results if not r.ok]
    print(f"done: {len(results) - len(failed)} ok, {len(failed)} failed")
    for r in failed:
        print(f"  failed: row {r.index} (exit {r.returncode})  ->  {r.err_file}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
