"""Pydantic schema and sanity-check validation for extracted document fields."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, field_validator


class LineItem(BaseModel):
    description: str
    qty: float
    unit_price: float
    line_total: float


class ExtractedDocument(BaseModel):
    doc_type: Literal["invoice", "receipt", "purchase_order"]
    doc_number: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    delivery_date: str | None = None
    vendor_name: str | None = None
    vendor_address: str | None = None
    client_name: str | None = None
    client_address: str | None = None
    ship_to: str | None = None
    bill_to: str | None = None
    line_items: list[LineItem] = []
    subtotal: float | None = None
    tax_rate: float | None = None
    tax_amount: float | None = None
    shipping_cost: float | None = None
    discount: float | None = None
    total: float | None = None
    payment_method: str | None = None
    payment_terms: str | None = None
    currency: str | None = "USD"
    notes: str | None = None

    @field_validator("doc_type", mode="before")
    @classmethod
    def normalize_doc_type(cls, v: str) -> str:
        if not isinstance(v, str):
            return v
        v = v.lower().strip()
        if any(k in v for k in ("invoice", "bill", "tax inv", "proforma", "debit note", "credit note")):
            return "invoice"
        if any(k in v for k in ("receipt", "payment receipt", "cash memo")):
            return "receipt"
        if any(k in v for k in ("purchase order", "purchase_order", "po ", "p.o.")):
            return "purchase_order"
        return v
