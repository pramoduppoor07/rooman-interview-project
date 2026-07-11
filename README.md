# Document Extraction Agent

> Extracts structured fields from invoice, receipt, and purchase order PDFs using Groq LLM + local text/OCR extraction.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your GROQ_API_KEY
```

**System dependencies:**
- **Tesseract OCR**: [install guide](https://github.com/tesseract-ocr/tesseract#installing-tesseract)
- **Poppler** (for pdf2image on Windows): [download](https://github.com/oschwartz10612/poppler-windows/releases)
- **WeasyPrint deps** (Linux/Mac): `sudo apt install libpango-1.0-0 libcairo2` or `brew install pango`

## Usage

**Generate sample PDFs:**
```bash
python -m src.generator.generate_samples
```

**Batch process a folder:**
```bash
python -m src.cli process samples/generated/ --output results/
```

**Streamlit viewer:**
```bash
streamlit run app.py
```

## Architecture

```
PDF input
  └─ Document type detection (native text vs scanned)
       ├─ Native text → pdfplumber extraction
       └─ Scanned     → pdf2image + pytesseract OCR
            └─ Extracted text → Groq LLM (llama-3.3-70b-versatile)
                 └─ Structured JSON → Pydantic validation + sanity checks
                      └─ {doc_type, fields, flags}
```

**Stage breakdown:**
1. **Detection** — checks PDF for embedded text; falls back to OCR if absent
2. **Extraction** — pdfplumber for native PDFs; pytesseract for image-based
3. **LLM parsing** — doc-type-aware prompt, JSON-mode response, nullable fields for schema variance (invoices have tax, POs don't)
4. **Validation** — Pydantic schema + sanity checks (line-item sum ≈ total, valid dates, required fields per doc type)

## Sample Documents

7 synthetic PDFs generated via HTML templates → WeasyPrint:
- **Invoice** × 2 (itemized table, tax, due date)
- **Receipt** × 2 (single-column, no formal bill-to)
- **Purchase Order** × 2 (ship-to/bill-to split, no tax)
- **Messy edge case** × 1 (missing due date, line items that don't sum to total)

## Validation Logic

- Line items sum within ±0.01 of stated total (where applicable)
- Dates parse correctly and due_date ≥ issue_date
- Required fields present per doc type (e.g. vendor required for invoice, PO number for PO)
- Flagged docs appear in batch summary report

## Tradeoffs

- **Local extraction over vision-LLM**: cheaper, deterministic, no extra API dependency; tradeoff is OCR quality on noisy scans
- **HTML→PDF samples**: full control over layout variance; tradeoff is they're cleaner than real-world docs
- **Unified nullable schema**: handles all three doc types in one prompt; tradeoff is looser schema than per-type models

**Known limitations:** OCR untested on truly noisy scans; currency/locale format assumptions; multi-page table support not implemented.

**What I'd add with more time:** per-field confidence scores, multi-page document support, template-specific extraction rules.
