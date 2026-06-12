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


def count_file_tokens(
    file_path: str | os.PathLike[str],
    encoding_name: str = "o200k_base",
) -> int:
    """Count the number of tokens in a text or PDF file.

    Requires the optional ``tiktoken`` (and, for PDFs, ``pypdf``) dependency
    (``pip install pytoolset[text]``).

    Args:
        file_path: Path to the input file. ``.pdf`` files are read via
            :func:`extract_pdf_text`; everything else is read as UTF-8 text.
        encoding_name: Tokenizer encoding name. Use ``"o200k_base"`` for newer
            OpenAI models, or ``"cl100k_base"`` for GPT-4/GPT-3.5-style models.

    Returns:
        The number of tokens in the file.

    Raises:
        FileNotFoundError: If ``file_path`` does not exist.
    """
    import tiktoken

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.suffix.lower() == ".pdf":
        text = extract_pdf_text(file_path)
    else:
        text = file_path.read_text(encoding="utf-8")

    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))
