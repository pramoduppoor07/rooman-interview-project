"""Extract text and tables from native (embedded-text) PDFs using pdfplumber."""
from pathlib import Path
import pdfplumber


def extract_native(pdf_path: str | Path) -> str:
    """Return all text from a native PDF, including table contents."""
    path = Path(pdf_path)
    parts: list[str] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        cleaned = [cell.strip() if cell else "" for cell in row]
                        parts.append("\t".join(cleaned))
            else:
                text = page.extract_text()
                if text:
                    parts.append(text.strip())

    return "\n".join(parts)
