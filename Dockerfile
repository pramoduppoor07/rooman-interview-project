# ─────────────────────────────────────────────
# Stage 1 — builder
# Install all Python dependencies into an
# isolated venv so nothing leaks into the
# final image.
# ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Build-time system deps (only needed to compile
# certain Python packages — not kept in final image)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Create an isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip once, then install deps.
# Copy requirements first so this layer is cached
# unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────
# Stage 2 — final runtime image
# Slim base + only what is needed at runtime.
# ─────────────────────────────────────────────
FROM python:3.11-slim AS final

# Runtime system dependencies:
#   tesseract-ocr      — OCR engine for scanned PDFs / image uploads
#   tesseract-ocr-eng  — English language data for Tesseract
#   poppler-utils      — pdf2image uses pdfinfo/pdftoppm under the hood
#   libgomp1           — OpenMP runtime required by some ML libs
#   curl               — used by the HEALTHCHECK below
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        poppler-utils \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built venv from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Environment config
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Tell pytesseract where the binary lives (set by apt to this path)
    TESSERACT_CMD=/usr/bin/tesseract

# Create a non-root user — never run as root in production
RUN useradd -m -u 1000 -s /bin/sh appuser

WORKDIR /app

# Copy application source.
# .dockerignore excludes .env, __pycache__, generated outputs, etc.
COPY --chown=appuser:appuser . .

# Pre-create writable output directories and hand them to appuser
RUN mkdir -p results samples/generated \
    && chown -R appuser:appuser results samples/generated

USER appuser

EXPOSE 8501

# Lightweight liveness check — Streamlit exposes a health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -sf http://localhost:8501/_stcore/health || exit 1

# Entrypoint:
#   1. Generate sample PDFs on first run (fast, idempotent — skipped if files exist)
#   2. Start Streamlit (config is read from .streamlit/config.toml)
CMD ["sh", "-c", \
     "python -m src.generator.generate_samples && \
      streamlit run app.py"]
