from __future__ import annotations

import os
from pathlib import Path

from .pdf import extract_pdf_text


def count_tokens(
    text: str | None = None,
    *,
    file_path: str | os.PathLike[str] | None = None,
    encoding_name: str = "o200k_base",
) -> int:
    """Count the number of tokens in a string or in a text/PDF file.

    Args:
        text: Raw text to tokenize.
        file_path: Path to the input file. ``.pdf`` files are read via
            :func:`pytoolset.pdf.extract_pdf_text`; everything else is read as
            UTF-8 text.
        encoding_name: Tokenizer encoding name. Use ``"o200k_base"`` for newer
            OpenAI models, or ``"cl100k_base"`` for GPT-4/GPT-3.5-style models.

    Returns:
        The number of tokens.

    Raises:
        ValueError: If neither or both of ``text`` and ``file_path`` are given.
        FileNotFoundError: If ``file_path`` does not exist.
    """
    import tiktoken

    if (text is None) == (file_path is None):
        raise ValueError("Provide exactly one of 'text' or 'file_path'.")

    if file_path is not None:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.suffix.lower() == ".pdf":
            text = extract_pdf_text(path)
        else:
            text = path.read_text(encoding="utf-8")

    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))
