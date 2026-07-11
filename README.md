# Document Extraction Agent

> Extracts structured fields from invoice, receipt, and purchase order PDFs using Groq LLM + local text/OCR extraction.

---

## How to Run This Project

### Prerequisites

- Python 3.10 or higher
- A free [Groq API key](https://console.groq.com) — takes 2 minutes to create

### Step 1 — Clone the repo

```bash
git clone https://github.com/pramoduppoor07/rooman-interview-project.git
cd rooman-interview-project
```

### Step 2 — Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

| Platform | Command |
|---|---|
| Windows (CMD) | `.venv\Scripts\activate.bat` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Linux / Mac | `source .venv/bin/activate` |

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment

Copy the example env file and add your Groq API key:

```bash
# Windows
copy .env.example .env

# Linux / Mac
cp .env.example .env
```

Open `.env` and fill in:

```
GROQ_API_KEY=your_groq_api_key_here

# Optional: only needed if Tesseract is installed but not in PATH
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Step 5 — Generate sample documents

This creates 7 sample PDFs (invoices, receipts, purchase orders + 1 messy edge case):

```bash
python -m src.generator.generate_samples
```

Output goes to `samples/generated/`.

### Step 6 — Run the Streamlit viewer

```bash
streamlit run app.py
```

Opens at `http://localhost:8501` in your browser. You can:
- Select any sample from the dropdown and click **Extract**
- Upload your own PDF or image (JPG, PNG, etc.)
- See the raw extracted text, all parsed fields, line items table, and validation flags

### Step 7 — Run the batch CLI (optional)

Process an entire folder at once and get a summary report:

```bash
python -m src.cli process samples/generated/ --output results/
```

Each PDF gets a `results/<filename>.json` with the extracted data. A `results/summary.json` lists which documents passed and which were flagged and why.

---

### For scanned PDFs or image uploads (optional)

By default the project works on digital PDFs without any extra setup. If you want to process scanned documents or image files, you need two additional system binaries:

**Tesseract OCR**
- Windows: download and run the installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki), then add `C:\Program Files\Tesseract-OCR\` to your system PATH
- Linux: `sudo apt install tesseract-ocr`
- Mac: `brew install tesseract`

**Poppler** (required by pdf2image to convert scanned PDF pages to images)
- Windows: download from [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases), extract, add the `bin/` folder to PATH
- Linux: `sudo apt install poppler-utils`
- Mac: `brew install poppler`

---

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

---

## Tech Stack

| Layer | Tool Used | Why |
|---|---|---|
| LLM extraction | [Groq API](https://groq.com) — `llama-3.3-70b-versatile` | Fast inference, free tier, native JSON mode |
| Native PDF text | [pdfplumber](https://github.com/jsvine/pdfplumber) | Table-aware extraction, no API cost |
| OCR (scanned/image) | [pytesseract](https://github.com/madmaze/pytesseract) + [pdf2image](https://github.com/Belval/pdf2image) + [Pillow](https://python-pillow.org) | Free, runs locally, no data leaves the machine |
| PDF generation (samples) | [xhtml2pdf](https://github.com/xhtml2pdf/xhtml2pdf) | Pure Python, no system DLLs required on Windows |
| HTML templating | [Jinja2](https://jinja.palletsprojects.com) | Fills sample data into HTML templates before PDF render |
| Schema validation | [Pydantic v2](https://docs.pydantic.dev) | Type-safe parsing, built-in validators, clear error messages |
| Date parsing | [python-dateutil](https://dateutil.readthedocs.io) | Handles ambiguous date formats from LLM output |
| Batch CLI | [Click](https://click.palletsprojects.com) | Simple command-line interface with argument parsing |
| UI / viewer | [Streamlit](https://streamlit.io) | Rapid demo UI, no frontend code needed |
| Env config | [python-dotenv](https://github.com/theskumar/python-dotenv) | Loads `.env` for API keys and binary paths |

---

## What Can Be Replaced in Production

| Component | Current (prototype) | Production alternative | Why you'd switch |
|---|---|---|---|
| **LLM provider** | Groq (free tier, llama-3.3-70b) | OpenAI GPT-4o, Anthropic Claude, Azure OpenAI | SLA guarantees, data residency, fine-tuning support |
| **LLM model** | llama-3.3-70b-versatile | Fine-tuned smaller model (llama-3-8b on invoices) | Lower cost and latency once field patterns are well-defined |
| **PDF text extraction** | pdfplumber | [PyMuPDF (fitz)](https://pymupdf.readthedocs.io) | Faster, better on complex layouts and embedded fonts |
| **OCR engine** | pytesseract (Tesseract) | [AWS Textract](https://aws.amazon.com/textract/), [Google Document AI](https://cloud.google.com/document-ai), [Azure Form Recognizer](https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence) | Much higher accuracy on noisy scans; cloud-managed |
| **Image-based extraction** | pytesseract → text → LLM | Vision LLM (GPT-4o vision, Claude 3.5 Sonnet) | Skip OCR entirely; LLM reads image directly — better for handwritten docs |
| **Validation schema** | Single unified nullable schema | Per-doc-type strict schemas | Stricter enforcement once doc types are well-separated |
| **Sample PDF generation** | xhtml2pdf + HTML templates | Real-world document collection | More representative of production edge cases |
| **UI** | Streamlit | React / Next.js frontend | Better UX, authentication, multi-user support |
| **Batch processing** | Local CLI | Celery + Redis / AWS SQS + Lambda | Async queue for high volume, retries, dead-letter handling |
| **Storage** | Local filesystem (`results/`) | S3 / GCS + PostgreSQL or DynamoDB | Persistence, search, audit trail across runs |

---

## Sample Documents

7 synthetic PDFs generated via HTML templates → xhtml2pdf:
- **Invoice** × 2 (itemized table, tax, due date)
- **Receipt** × 2 (single-column, unit prices + line totals)
- **Purchase Order** × 2 (ship-to/bill-to split, no tax)
- **Messy edge case** × 1 (missing due date, line items that don't sum to total — intentionally flagged)

---

## Validation Logic

- Line items sum within ±0.02 of stated subtotal (where applicable)
- Total = subtotal + tax + shipping − discount (within ±0.02)
- Dates parse correctly; due_date ≥ issue_date
- Required fields per doc type:
  - Invoice → `vendor_name`, `due_date`, `total`
  - Receipt → `total`
  - Purchase Order → `doc_number`, `delivery_date`
- Flagged documents appear in `results/summary.json` with reasons

---

## Tradeoffs

- **Local text extraction over vision-LLM** — cheaper, deterministic, no extra API cost; tradeoff is OCR quality degrades on noisy or handwritten scans
- **Single unified nullable schema** — one prompt handles invoice/receipt/PO without branching; tradeoff is looser than per-type strict schemas
- **HTML→PDF synthetic samples** — full control over layout variance and edge cases; tradeoff is synthetic docs are cleaner than real-world documents
- **Groq free tier** — fast and zero-cost for prototyping; tradeoff is no SLA, rate limits, and model may change

**Known limitations:** OCR untested on truly noisy scans; currency/locale format assumptions (e.g. `1,00,000` Indian formatting); multi-page table support not implemented.

---

## Future Work

### Extraction quality
- [ ] **Per-field confidence scores** — LLM rates certainty per field (e.g. `total: {value: 600.0, confidence: 0.4}`); low-confidence fields get flagged for human review
- [ ] **Multi-page document support** — currently handles single-page extraction; long invoices with multiple pages of line items get truncated
- [ ] **Template-specific extraction rules** — once 100+ invoices from the same vendor are seen, cache their layout pattern and skip the LLM for those (faster + cheaper)
- [ ] **Vision LLM for image input** — replace pytesseract with GPT-4o / Claude vision to handle handwritten receipts and low-quality phone photos

### Smarter validation
- [ ] **Currency/locale normalisation** — handle `1,00,000` (Indian) vs `1.000,00` (European) vs `1,000.00` (US) as the same number
- [ ] **Duplicate invoice detection** — flag when the same invoice number + vendor + amount appears more than once
- [ ] **Vendor-level anomaly detection** — flag invoices where the total is significantly higher than the historical average for that vendor

### New document types
- [ ] **Bank statements** — detect and extract transaction rows, opening/closing balance
- [ ] **Utility bills** — bill period, meter readings, usage charges
- [ ] **Credit notes / debit notes** — already partially handled via doc_type normalisation; needs dedicated schema

### Production infrastructure
- [ ] **Async processing queue** — Celery + Redis or AWS SQS so the UI doesn't block waiting for Groq to respond
- [ ] **Human review workflow** — approve/reject UI for flagged documents; currently they just sit in `summary.json`
- [ ] **Persistent storage** — store extracted results in PostgreSQL or DynamoDB with search and audit trail
- [ ] **REST API** — expose `POST /extract` endpoint so other services can submit documents programmatically
- [ ] **Multi-language support** — Indian regional languages (Hindi, Kannada, Tamil), European languages (German, French)
- [ ] **Audit trail** — log who processed what document, when, what was flagged, and whether it was approved or rejected
