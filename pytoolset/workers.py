from __future__ import annotations

import os
import sys
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import redirect_stdout
from functools import partial
from typing import TypeVar

T = TypeVar("T")


class ThreadWorker:
    """Run I/O-bound tasks in parallel using threads.

    Threads share one process, so when ``log_file`` is given all task output is
    redirected to that single file. Lines from concurrent tasks may interleave.

    Args:
        max_workers: The maximum number of worker threads. Defaults to ``None``,
            which lets :class:`~concurrent.futures.ThreadPoolExecutor` choose.
        log_file: If given, a file to which all task stdout is redirected.
            Defaults to ``None`` (output is left untouched).
    """

    def __init__(
        self,
        max_workers: int | None = None,
        log_file: str | os.PathLike[str] | None = None,
    ) -> None:
        self.max_workers = max_workers
        self.log_file = log_file

    def _run_all(self, tasks: list[Callable[[], T]]) -> list[T]:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(task) for task in tasks]
            return [f.result() for f in futures]

    def run(self, tasks: list[Callable[[], T]]) -> list[T]:
        """Run zero-arg callables in parallel.

        Args:
            tasks: The zero-argument callables to run.

        Returns:
            The task results, in the same order as ``tasks``.
        """
        if self.log_file is None:
            return self._run_all(tasks)
        with open(self.log_file, "w") as fh, redirect_stdout(fh):
            return self._run_all(tasks)


class ProcessWorker:
    """Run CPU-bound tasks in parallel using processes.

    Tasks must be picklable (module-level functions or functools.partial).
    Lambdas and locally-defined functions cannot be sent across processes.

    Processes are isolated, so when ``log_prefix`` is given each task's stdout is
    redirected to its own file named ``{log_prefix}{n}.log`` (1-indexed by input
    order), e.g. log_prefix="log" -> log1.log, log2.log, ...

    Args:
        max_workers: The maximum number of worker processes. Defaults to
            ``None``, which lets
            :class:`~concurrent.futures.ProcessPoolExecutor` choose.
        log_prefix: If given, the filename prefix for per-task stdout logs.
            Defaults to ``None`` (output is left untouched).
    """

    def __init__(
        self,
        max_workers: int | None = None,
        log_prefix: str | os.PathLike[str] | None = None,
    ) -> None:
        self.max_workers = max_workers
        self.log_prefix = log_prefix

    @staticmethod
    def _run_to_file(task: Callable[[], T], path: str) -> T:
        """Run a task with its stdout redirected to ``path`` (in a subprocess)."""
        with open(path, "w") as fh:
            original = sys.stdout
            sys.stdout = fh  # type: ignore[assignment]
            try:
                return task()
            finally:
                sys.stdout = original

    def run(self, tasks: list[Callable[[], T]]) -> list[T]:
        """Run zero-arg callables in parallel.

        Args:
            tasks: The zero-argument callables to run.

        Returns:
            The task results, in the same order as ``tasks``.
        """
        if self.log_prefix is not None:
            prefix = os.fspath(self.log_prefix)
            tasks = [
                partial(ProcessWorker._run_to_file, task, f"{prefix}{i + 1}.log")
                for i, task in enumerate(tasks)
            ]
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(task) for task in tasks]
            return [f.result() for f in futures]
