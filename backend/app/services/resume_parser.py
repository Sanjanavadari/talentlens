from pathlib import Path

import fitz


def extract_text_from_pdf_bytes(data: bytes) -> str:
    with fitz.open(stream=data, filetype="pdf") as doc:
        pages = [page.get_text() for page in doc]
    return "\n".join(pages).strip()


def extract_text_from_pdf_path(path: str | Path) -> str:
    with fitz.open(path) as doc:
        pages = [page.get_text() for page in doc]
    return "\n".join(pages).strip()
