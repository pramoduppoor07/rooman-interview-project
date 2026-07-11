"""Detect whether a PDF contains native (embedded) text or is image/scanned."""
from pathlib import Path
import pdfplumber

MIN_CHARS_PER_PAGE = 20


def detect_doc_type(pdf_path: str | Path) -> str:
    """Return 'native' if the PDF has embedded text, else 'scanned'."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if len(text.strip()) >= MIN_CHARS_PER_PAGE:
                return "native"

    return "scanned"
