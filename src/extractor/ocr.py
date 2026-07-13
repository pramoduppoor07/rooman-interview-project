"""OCR fallback for scanned/image-based PDFs using pdf2image + pytesseract.

System dependencies required:
  - Tesseract OCR binary: https://github.com/tesseract-ocr/tesseract#installing-tesseract
  - Poppler (Windows): https://github.com/oschwartz10612/poppler-windows/releases
"""
from __future__ import annotations
import os
from pathlib import Path
from PIL import Image
import pytesseract
from pytesseract import TesseractNotFoundError

# Allow overriding the Tesseract binary path via .env (TESSERACT_CMD=C:\...\tesseract.exe)
_cmd = os.environ.get("TESSERACT_CMD")
if _cmd:
    pytesseract.pytesseract.tesseract_cmd = _cmd

try:
    from pdf2image import convert_from_path
    from pdf2image.exceptions import PDFInfoNotInstalledError
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    PDFInfoNotInstalledError = Exception


def extract_ocr(pdf_path: str | Path) -> str:
    """Convert PDF pages to images and run Tesseract OCR on each."""
    if not PDF2IMAGE_AVAILABLE:
        raise RuntimeError("pdf2image is not installed — run: pip install pdf2image")

    path = Path(pdf_path)
    try:
        pages: list[Image.Image] = convert_from_path(str(path), dpi=200)
    except PDFInfoNotInstalledError:
        raise RuntimeError(
            "Poppler not found. Install it and add to PATH.\n"
            "Windows: https://github.com/oschwartz10612/poppler-windows/releases"
        )

    parts: list[str] = []
    for page_img in pages:
        try:
            text = pytesseract.image_to_string(page_img, config="--psm 6")
        except TesseractNotFoundError:
            raise RuntimeError(
                "Tesseract not found. Install it and add to PATH.\n"
                "https://github.com/tesseract-ocr/tesseract#installing-tesseract"
            )
        if text.strip():
            parts.append(text.strip())

    return "\n".join(parts)


def extract_ocr_from_image(image: Image.Image) -> str:
    """Run OCR on a single PIL Image (used for testing without a full PDF)."""
    try:
        return pytesseract.image_to_string(image, config="--psm 6").strip()
    except TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract not found. Install it and add to PATH.\n"
            "https://github.com/tesseract-ocr/tesseract#installing-tesseract"
        )
