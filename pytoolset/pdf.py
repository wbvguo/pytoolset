from __future__ import annotations

import os
from pathlib import Path


def extract_pdf_text(pdf_path: str | os.PathLike[str]) -> str:
    """Extract and concatenate the text from a text-based PDF.

    Requires the optional ``pypdf`` dependency (``pip install pytoolset[text]``).

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        The text of every page joined by newlines.
    """
    from pypdf import PdfReader

    reader = PdfReader(os.fspath(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def merge_pdfs(
    input_paths: list[str | os.PathLike[str]],
    output_path: str | os.PathLike[str],
) -> str:
    """Merge several PDFs into a single file, preserving the given order.

    Requires the optional ``pypdf`` dependency (``pip install pytoolset[text]``).

    Args:
        input_paths: Paths to the PDFs to merge, in output order.
        output_path: Path to write the merged PDF to.

    Returns:
        The output path as a string.
    """
    from pypdf import PdfWriter

    writer = PdfWriter()
    for path in input_paths:
        writer.append(os.fspath(path))
    with open(os.fspath(output_path), "wb") as fh:
        writer.write(fh)
    return os.fspath(output_path)


def split_pdf(
    input_path: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
) -> list[str]:
    """Split a PDF into one single-page PDF per page.

    Requires the optional ``pypdf`` dependency (``pip install pytoolset[text]``).

    Args:
        input_path: Path to the PDF to split.
        output_dir: Directory to write the per-page PDFs to. Created if needed.

    Returns:
        The list of written page-file paths, in page order.
    """
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(os.fspath(input_path))
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(os.fspath(input_path)).stem

    written: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = out_dir / f"{stem}_p{index}.pdf"
        with open(out_path, "wb") as fh:
            writer.write(fh)
        written.append(str(out_path))
    return written


def extract_pages(
    input_path: str | os.PathLike[str],
    pages: list[int],
    output_path: str | os.PathLike[str],
) -> str:
    """Extract specific pages into a new PDF.

    Requires the optional ``pypdf`` dependency (``pip install pytoolset[text]``).

    Args:
        input_path: Path to the source PDF.
        pages: 1-based page numbers to keep, in the desired output order.
        output_path: Path to write the resulting PDF to.

    Returns:
        The output path as a string.

    Raises:
        IndexError: If a requested page number is out of range (page numbers
            are 1-based, so any value below 1 is also out of range).
    """
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(os.fspath(input_path))
    writer = PdfWriter()
    for page_number in pages:
        if page_number < 1:
            raise IndexError(f"page number must be >= 1, got {page_number}")
        writer.add_page(reader.pages[page_number - 1])
    with open(os.fspath(output_path), "wb") as fh:
        writer.write(fh)
    return os.fspath(output_path)
