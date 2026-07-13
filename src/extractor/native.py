"""Extract text and tables from native (embedded-text) PDFs using pdfplumber."""
from __future__ import annotations
from pathlib import Path
import pdfplumber


def extract_native(pdf_path: str | Path) -> str:
    """Return all text from a native PDF, always using full-page text extraction.

    pdfplumber's table extractor can miss large portions of a page when the layout
    has many nested/adjacent tables (e.g. PO documents). Using extract_text() on the
    full page gives a complete, ordered view; table-specific rows are then appended
    only when they contain content not already captured by the page text.
    """
    path = Path(pdf_path)
    parts: list[str] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                parts.append(page_text.strip())

            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    cleaned = [cell.strip() if cell else "" for cell in row]
                    row_str = "\t".join(cleaned)
                    if row_str.strip() and row_str not in page_text:
                        parts.append(row_str)

    return "\n".join(parts)
