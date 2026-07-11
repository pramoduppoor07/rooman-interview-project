# Document Extraction Agent

> Extracts structured fields from invoice, receipt, and purchase order PDFs using Groq LLM + local text/OCR extraction.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your GROQ_API_KEY
```

**System dependencies (only needed for scanned PDFs / image uploads):**
- **Tesseract OCR**: [install guide](https://github.com/UB-Mannheim/tesseract/wiki)
- **Poppler** (for pdf2image on Windows): [download](https://github.com/oschwartz10612/poppler-windows/releases)

> Digital PDFs (most invoices received by email) work without any system dependencies.

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
PDF / Image input
  └─ Document type detection (native text vs scanned vs image)
       ├─ Native PDF  → pdfplumber text extraction
       ├─ Scanned PDF → pdf2image + pytesseract OCR
       └─ Image file  → pytesseract OCR directly
            └─ Raw text → Groq LLM (llama-3.3-70b-versatile, JSON mode)
                 └─ Structured JSON → Pydantic schema + sanity checks
                      └─ {doc_type, extracted fields, validation flags}
```

**Stage breakdown:**
1. **Detection** — checks PDF for embedded text; routes to OCR if absent; handles raw images directly
2. **Extraction** — pdfplumber for native PDFs (table-aware); pytesseract for scanned/image input
3. **LLM parsing** — single unified prompt handles all three doc types; nullable fields for schema variance (invoices have tax, POs don't); doc_type variants like "bill", "GST invoice", "tax invoice" are normalised automatically
4. **Validation** — Pydantic schema + sanity checks (line-item sum ≈ total, valid dates, required fields per doc type)

## Tech Stack

| Layer | Tool Used | Why |
|---|---|---|
| LLM extraction | [Groq API](https://groq.com) — `llama-3.3-70b-versatile` | Fast inference, free tier, native JSON mode |
| Native PDF text | [pdfplumber](https://github.com/jsvine/pdfplumber) | Table-aware extraction, no API cost |
| OCR (scanned/image) | [pytesseract](https://github.com/madmaze/pytesseract) + [pdf2image](https://github.com/Belval/pdf2image) + [Pillow](https://python-pillow.org) | Free, runs locally, no data leaves the machine |
| PDF generation (samples) | [xhtml2pdf](https://github.com/xhtml2pdf/xhtml2pdf) | Pure Python, no system DLLs required on Windows |
| HTML templating | [Jinja2](https://jinja.palletsprojects.com) | Used to fill sample data into HTML templates before PDF render |
| Schema validation | [Pydantic v2](https://docs.pydantic.dev) | Type-safe parsing, built-in validators, clear error messages |
| Date parsing | [python-dateutil](https://dateutil.readthedocs.io) | Handles ambiguous date formats from LLM output |
| Batch CLI | [Click](https://click.palletsprojects.com) | Simple command-line interface with argument parsing |
| UI / viewer | [Streamlit](https://streamlit.io) | Rapid demo UI, no frontend code needed |
| Env config | [python-dotenv](https://github.com/theskumar/python-dotenv) | Loads `.env` for API keys and binary paths |

## What Can Be Replaced in Production

| Component | Current (prototype) | Production alternative | Why you'd switch |
|---|---|---|---|
| **LLM provider** | Groq (free tier, llama-3.3-70b) | OpenAI GPT-4o, Anthropic Claude, Azure OpenAI | SLA guarantees, data residency, fine-tuning support |
| **LLM model** | llama-3.3-70b-versatile | A fine-tuned smaller model (e.g. llama-3-8b fine-tuned on invoices) | Lower cost and latency once field patterns are well-defined |
| **PDF text extraction** | pdfplumber | [PyMuPDF (fitz)](https://pymupdf.readthedocs.io) | Faster, better handling of complex layouts and embedded fonts |
| **OCR engine** | pytesseract (Tesseract) | [AWS Textract](https://aws.amazon.com/textract/), [Google Document AI](https://cloud.google.com/document-ai), [Azure Form Recognizer](https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence) | Much higher accuracy on real-world noisy scans; cloud managed |
| **Image-based extraction** | pytesseract → text → LLM | Vision LLM (GPT-4o vision, Claude 3.5 Sonnet) | Skip OCR entirely; LLM reads the image directly — better for handwritten or low-quality scans |
| **Validation schema** | Single unified nullable schema | Per-doc-type strict schemas | Stricter enforcement once doc types are well-separated |
| **Sample PDF generation** | xhtml2pdf + HTML templates | Actual real-world document collection | More representative of edge cases in production data |
| **UI** | Streamlit | React / Next.js frontend | Better UX, auth, multi-user support |
| **Batch processing** | Local CLI | Celery + Redis / AWS SQS + Lambda | Async queue for high volume, retries, dead-letter handling |
| **Storage** | Local filesystem (`results/`) | S3 / GCS + PostgreSQL or DynamoDB | Persistence, search, audit trail |

## Sample Documents

7 synthetic PDFs generated via HTML templates → xhtml2pdf:
- **Invoice** × 2 (itemized table, tax, due date)
- **Receipt** × 2 (single-column, unit prices + line totals)
- **Purchase Order** × 2 (ship-to/bill-to split, no tax)
- **Messy edge case** × 1 (missing due date, line items that don't sum to total — intentionally flagged)

## Validation Logic

- Line items sum within ±0.02 of stated subtotal (where applicable)
- Total = subtotal + tax + shipping − discount (within ±0.02)
- Dates parse correctly; due_date ≥ issue_date
- Required fields per doc type:
  - Invoice → `vendor_name`, `due_date`, `total`
  - Receipt → `total`
  - Purchase Order → `doc_number`, `delivery_date`
- Flagged documents appear in `results/summary.json` with reasons

## Tradeoffs

- **Local text extraction over vision-LLM** — cheaper, deterministic, no extra API cost; tradeoff is OCR quality degrades on noisy or handwritten scans
- **Single unified nullable schema** — one prompt handles invoice/receipt/PO without branching; tradeoff is looser than per-type strict schemas
- **HTML→PDF synthetic samples** — full control over layout variance and edge cases; tradeoff is synthetic docs are cleaner than real-world documents
- **Groq free tier** — fast and zero-cost for prototyping; tradeoff is no SLA, rate limits, and model may change

**Known limitations:** OCR untested on truly noisy scans; currency/locale format assumptions (e.g. `1,00,000` Indian formatting); multi-page table support not implemented.

**What I'd add with more time:** per-field confidence scores, multi-page document support, fine-tuned extraction model, async batch processing pipeline.
