"""Streamlit viewer for the document extraction pipeline."""
import json
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Document Extractor", layout="wide")
st.title("Document Extraction Agent")
st.caption("Upload a PDF or image, or select a sample — see raw text, extracted fields, and validation flags.")

SAMPLES_DIR = Path("samples/generated")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def get_sample_files() -> list[Path]:
    if SAMPLES_DIR.exists():
        return sorted(SAMPLES_DIR.glob("*.pdf"))
    return []


# --- Sidebar: input selection ---
with st.sidebar:
    st.header("Input")
    mode = st.radio("Source", ["Upload file", "Use sample file"])

    upload_path: Path | None = None
    is_image = False

    if mode == "Upload file":
        uploaded = st.file_uploader(
            "Choose a PDF or image",
            type=["pdf", "jpg", "jpeg", "png", "bmp", "tiff", "webp"],
        )
        if uploaded:
            suffix = Path(uploaded.name).suffix.lower()
            is_image = suffix in IMAGE_EXTENSIONS
            tmp_name = "_upload_tmp" + suffix
            tmp = Path("results") / tmp_name
            tmp.parent.mkdir(exist_ok=True)
            tmp.write_bytes(uploaded.read())
            upload_path = tmp

            if is_image:
                st.image(str(tmp), caption=uploaded.name, use_container_width=True)
    else:
        samples = get_sample_files()
        if samples:
            choice = st.selectbox("Sample file", [s.name for s in samples])
            upload_path = SAMPLES_DIR / choice
        else:
            st.warning("No sample files found. Run `python -m src.generator.generate_samples` first.")

    run = st.button("Extract", type="primary", disabled=(upload_path is None))

# --- Main area ---
if run and upload_path:
    with st.spinner("Processing..."):
        try:
            if is_image:
                from src.pipeline import process_image
                result = process_image(upload_path)
            else:
                from src.pipeline import process_document
                result = process_document(upload_path)
        except RuntimeError as exc:
            if "Tesseract" in str(exc) or "Poppler" in str(exc):
                st.error(str(exc))
                st.info(
                    "**OCR requires system binaries:**\n"
                    "- **Tesseract**: https://github.com/UB-Mannheim/tesseract/wiki\n"
                    "- **Poppler** (for PDF→image): https://github.com/oschwartz10612/poppler-windows/releases"
                )
            else:
                st.error(f"Pipeline error: {exc}")
            st.stop()
        except Exception as exc:
            st.error(f"Pipeline error: {exc}")
            st.stop()

    doc = result["extracted"]
    flags = result["flags"]

    doc_type_label = (doc.get("doc_type") or "unknown").upper()
    if result["ok"]:
        st.success(f"Passed validation — {doc_type_label}")
    else:
        st.warning(f"{len(flags)} validation issue(s) — {doc_type_label}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Doc Type", (doc.get("doc_type") or "—").replace("_", " ").title())
    col2.metric("Doc Number", doc.get("doc_number") or "—")
    col3.metric("PDF Format", result["doc_format"].replace("_", " ").title())

    if flags:
        st.subheader("Validation Flags")
        for flag in flags:
            st.error(f"• {flag}")

    tabs = st.tabs(["Extracted Fields", "Line Items", "Raw Text", "Full JSON"])

    with tabs[0]:
        fields = {
            k: v for k, v in doc.items()
            if k not in ("line_items",) and v is not None
        }
        col_a, col_b = st.columns(2)
        items = list(fields.items())
        mid = len(items) // 2
        with col_a:
            for k, v in items[:mid]:
                st.text_input(k, value=str(v), disabled=True, key=f"fa_{k}")
        with col_b:
            for k, v in items[mid:]:
                st.text_input(k, value=str(v), disabled=True, key=f"fb_{k}")

    with tabs[1]:
        line_items = doc.get("line_items", [])
        if line_items:
            st.dataframe(line_items, use_container_width=True)
        else:
            st.info("No line items extracted.")

    with tabs[2]:
        st.text_area("Raw extracted text", result["raw_text"], height=400)

    with tabs[3]:
        st.json(result["extracted"])

elif not run:
    st.info("Select a file and click **Extract** to begin.")
