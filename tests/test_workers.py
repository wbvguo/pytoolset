from __future__ import annotations

import time
from functools import partial

import pytest

from pytoolset import ProcessWorker, ThreadWorker


# --- helpers (module-level so ProcessPoolExecutor can pickle them) ---

def _double(x: int) -> int:
    return x * 2


def _identity(x: int) -> int:
    return x


def _raise_runtime() -> None:
    raise RuntimeError("cpu error")


def _print_and_return(msg: str, value: int) -> int:
    print(msg)
    return value


# --- ThreadWorker ---


def test_thread_returns_results_in_order():
    tasks = [lambda i=i: i * 2 for i in range(5)]
    assert ThreadWorker().run(tasks) == [0, 2, 4, 6, 8]


def test_thread_empty_list():
    assert ThreadWorker().run([]) == []


def test_thread_single_task():
    assert ThreadWorker().run([lambda: 42]) == [42]


def test_thread_max_workers():
    tasks = [lambda i=i: i for i in range(10)]
    assert ThreadWorker(max_workers=2).run(tasks) == list(range(10))


def test_thread_exception_propagates():
    def boom():
        raise ValueError("oops")

    with pytest.raises(ValueError, match="oops"):
        ThreadWorker().run([boom])


def test_thread_is_concurrent():
    sleep_time = 0.2
    n = 5
    tasks = [lambda: time.sleep(sleep_time)] * n
    start = time.monotonic()
    ThreadWorker().run(tasks)
    elapsed = time.monotonic() - start
    assert elapsed < sleep_time * n * 0.5


def test_thread_log_file_output(tmp_path):
    log_file = tmp_path / "run.log"
    tasks = [
        lambda: (print("hello from 1"), 1)[1],
        lambda: (print("hello from 2"), 2)[1],
    ]
    results = ThreadWorker(log_file=log_file).run(tasks)
    assert results == [1, 2]
    contents = log_file.read_text()
    assert "hello from 1" in contents
    assert "hello from 2" in contents


def test_thread_log_file_no_output(tmp_path):
    log_file = tmp_path / "run.log"
    assert ThreadWorker(log_file=log_file).run([lambda: 99]) == [99]
    assert log_file.read_text() == ""


def test_thread_log_file_results_correct(tmp_path):
    log_file = tmp_path / "run.log"
    tasks = [lambda i=i: i * 3 for i in range(4)]
    assert ThreadWorker(log_file=log_file).run(tasks) == [0, 3, 6, 9]


# --- ProcessWorker ---


def test_process_returns_results_in_order():
    tasks = [partial(_double, i) for i in range(5)]
    assert ProcessWorker().run(tasks) == [0, 2, 4, 6, 8]


def test_process_empty_list():
    assert ProcessWorker().run([]) == []


def test_process_single_task():
    assert ProcessWorker().run([partial(_double, 21)]) == [42]


def test_process_max_workers():
    tasks = [partial(_identity, i) for i in range(10)]
    assert ProcessWorker(max_workers=2).run(tasks) == list(range(10))


def test_process_exception_propagates():
    with pytest.raises(RuntimeError, match="cpu error"):
        ProcessWorker().run([_raise_runtime])


def test_process_log_files_output(tmp_path):
    prefix = tmp_path / "log"
    tasks = [
        partial(_print_and_return, "cpu hello 1", 10),
        partial(_print_and_return, "cpu hello 2", 20),
    ]
    results = ProcessWorker(log_prefix=prefix).run(tasks)
    assert results == [10, 20]
    assert (tmp_path / "log1.log").read_text().strip() == "cpu hello 1"
    assert (tmp_path / "log2.log").read_text().strip() == "cpu hello 2"


def test_process_log_files_no_output(tmp_path):
    prefix = tmp_path / "log"
    assert ProcessWorker(log_prefix=prefix).run([partial(_double, 5)]) == [10]
    assert (tmp_path / "log1.log").read_text() == ""


def test_process_log_files_results_correct(tmp_path):
    prefix = tmp_path / "log"
    tasks = [partial(_double, i) for i in range(4)]
    assert ProcessWorker(log_prefix=prefix).run(tasks) == [0, 2, 4, 6]
