"""End-to-end document extraction pipeline."""
from pathlib import Path
from src.extractor.detect import detect_doc_type
from src.extractor.native import extract_native
from src.extractor.ocr import extract_ocr
from src.llm.extractor import extract_fields
from src.validator.checks import validate
from src.validator.schema import ExtractedDocument


def process_document(pdf_path: str | Path) -> dict:
    """
    Process a single PDF through the full pipeline.

    Returns:
        {
            "path": str,
            "doc_format": "native" | "scanned",
            "raw_text": str,
            "extracted": dict,
            "document": ExtractedDocument | None,
            "flags": list[str],
            "ok": bool
        }
    """
    path = Path(pdf_path)

    doc_format = detect_doc_type(path)

    if doc_format == "native":
        raw_text = extract_native(path)
    else:
        raw_text = extract_ocr(path)

    extracted = extract_fields(raw_text)
    document, flags = validate(extracted)

    return {
        "path": str(path),
        "doc_format": doc_format,
        "raw_text": raw_text,
        "extracted": extracted,
        "document": document,
        "flags": flags,
        "ok": len(flags) == 0,
    }
