"""LLM-based structured field extraction using Groq."""
from src.llm.groq_client import chat_json

SYSTEM_PROMPT = """You are a document data extractor. Given raw text from a financial document,
extract structured fields and return them as a single JSON object.

Rules:
- Identify the document type: "invoice", "receipt", or "purchase_order"
- Extract all fields you can find. Use null for fields that are missing or not applicable.
- Do NOT hallucinate values. If a field is absent from the text, set it to null.
- For monetary values, return numbers (not strings), e.g. 8605.88 not "$8,605.88"
- For dates, use YYYY-MM-DD format if possible, else return the string as-is.
- line_items should be a list of objects with: description, qty (number), unit_price (number), line_total (number)

Return exactly this JSON schema (all fields required at the top level, nullable where not present):
{
  "doc_type": "invoice" | "receipt" | "purchase_order",
  "doc_number": string | null,
  "issue_date": string | null,
  "due_date": string | null,
  "delivery_date": string | null,
  "vendor_name": string | null,
  "vendor_address": string | null,
  "client_name": string | null,
  "client_address": string | null,
  "ship_to": string | null,
  "bill_to": string | null,
  "line_items": [{"description": string, "qty": number, "unit_price": number, "line_total": number}],
  "subtotal": number | null,
  "tax_rate": number | null,
  "tax_amount": number | null,
  "shipping_cost": number | null,
  "discount": number | null,
  "total": number | null,
  "payment_method": string | null,
  "payment_terms": string | null,
  "currency": "USD" | string | null,
  "notes": string | null
}"""


def extract_fields(raw_text: str) -> dict:
    """Extract structured fields from raw document text via Groq LLM."""
    return chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"Extract fields from this document text:\n\n{raw_text}",
    )
