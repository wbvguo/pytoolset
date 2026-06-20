from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .parallel import CommandResult, CommandRunner
    from .path import find_file, find_project_root, get_absolute_path, mkdir
    from .pdf import extract_pages, extract_pdf_text, merge_pdfs, split_pdf
    from .select import select_rows
    from .session import sessionInfo
    from .token import count_tokens
    from .workers import ProcessWorker, ThreadWorker
    from .youtube import YouTubeDownloader

# Every public name is exposed lazily: importing the package imports none of the
# submodules below. This keeps ``import pytoolset`` cheap and, crucially, means a
# submodule run as ``python -m pytoolset.<module>`` is never already present in
# sys.modules at execution time, which is what triggers runpy's RuntimeWarning.
_LAZY_EXPORTS = {
    "find_file": ".path",
    "find_project_root": ".path",
    "get_absolute_path": ".path",
    "mkdir": ".path",
    "ThreadWorker": ".workers",
    "ProcessWorker": ".workers",
    "CommandRunner": ".parallel",
    "CommandResult": ".parallel",
    "select_rows": ".select",
    "sessionInfo": ".session",
    "extract_pdf_text": ".pdf",
    "merge_pdfs": ".pdf",
    "split_pdf": ".pdf",
    "extract_pages": ".pdf",
    "count_tokens": ".token",
    "YouTubeDownloader": ".youtube",
}

__all__ = list(_LAZY_EXPORTS)


def __getattr__(name: str):
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is not None:
        from importlib import import_module

        return getattr(import_module(module_name, __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
