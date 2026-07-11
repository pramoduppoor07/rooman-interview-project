"""Sanity checks on top of Pydantic schema validation."""
from __future__ import annotations
from dateutil import parser as dateparser
from pydantic import ValidationError
from src.validator.schema import ExtractedDocument

LINE_ITEM_TOLERANCE = 0.02


def validate(raw: dict) -> tuple[ExtractedDocument | None, list[str]]:
    """
    Validate extracted fields. Returns (document, flags).
    flags is a list of human-readable warning/error strings.
    document is None if schema validation itself fails.
    """
    flags: list[str] = []

    try:
        doc = ExtractedDocument.model_validate(raw)
    except ValidationError as e:
        return None, [f"Schema error: {e.error_count()} issue(s) — {e.errors()[0]['msg']}"]

    _check_required_fields(doc, flags)
    _check_line_item_sums(doc, flags)
    _check_dates(doc, flags)
    _check_total_vs_components(doc, flags)

    return doc, flags


def _check_required_fields(doc: ExtractedDocument, flags: list[str]) -> None:
    if doc.doc_type == "invoice":
        if not doc.vendor_name:
            flags.append("Missing vendor_name (required for invoice)")
        if not doc.due_date:
            flags.append("Missing due_date (expected for invoice)")
        if doc.total is None:
            flags.append("Missing total (required for invoice)")

    elif doc.doc_type == "purchase_order":
        if not doc.doc_number:
            flags.append("Missing doc_number / PO number")
        if not doc.delivery_date:
            flags.append("Missing delivery_date (expected for purchase order)")

    elif doc.doc_type == "receipt":
        if doc.total is None:
            flags.append("Missing total (required for receipt)")


def _check_line_item_sums(doc: ExtractedDocument, flags: list[str]) -> None:
    if not doc.line_items:
        return

    for i, item in enumerate(doc.line_items):
        expected = round(item.qty * item.unit_price, 2)
        if abs(item.line_total - expected) > LINE_ITEM_TOLERANCE:
            flags.append(
                f"Line item {i+1} ({item.description!r}): "
                f"line_total {item.line_total} != qty×unit_price {expected}"
            )

    computed_subtotal = round(sum(i.qty * i.unit_price for i in doc.line_items), 2)
    if doc.subtotal is not None and abs(doc.subtotal - computed_subtotal) > LINE_ITEM_TOLERANCE:
        flags.append(
            f"Subtotal mismatch: stated {doc.subtotal}, computed from line items {computed_subtotal}"
        )


def _check_dates(doc: ExtractedDocument, flags: list[str]) -> None:
    dates: dict[str, str | None] = {
        "issue_date": doc.issue_date,
        "due_date": doc.due_date,
        "delivery_date": doc.delivery_date,
    }
    parsed: dict[str, object] = {}

    for field, value in dates.items():
        if value:
            try:
                parsed[field] = dateparser.parse(value)
            except (ValueError, OverflowError):
                flags.append(f"Unparseable date in {field}: {value!r}")

    if "issue_date" in parsed and "due_date" in parsed:
        if parsed["due_date"] < parsed["issue_date"]:
            flags.append("due_date is before issue_date")


def _check_total_vs_components(doc: ExtractedDocument, flags: list[str]) -> None:
    if doc.total is None or doc.subtotal is None:
        return

    expected = doc.subtotal
    if doc.tax_amount:
        expected += doc.tax_amount
    if doc.shipping_cost:
        expected += doc.shipping_cost
    if doc.discount:
        expected -= doc.discount

    expected = round(expected, 2)
    if abs(doc.total - expected) > LINE_ITEM_TOLERANCE:
        flags.append(
            f"Total mismatch: stated {doc.total}, "
            f"computed subtotal±tax±shipping±discount = {expected}"
        )
