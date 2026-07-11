"""Generates sample PDFs from HTML templates using xhtml2pdf."""
from pathlib import Path
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "samples" / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "samples" / "generated"

INVOICE_SAMPLES = [
    {
        "vendor_name": "Apex Solutions Ltd.",
        "vendor_address": "88 Commerce Park, Suite 4B, Austin, TX 78701",
        "vendor_email": "billing@apexsolutions.io",
        "vendor_phone": "+1 (512) 555-0192",
        "invoice_number": "INV-2024-0341",
        "issue_date": "2024-03-15",
        "due_date": "2024-04-14",
        "status": "UNPAID",
        "client_name": "Bright Futures Inc.",
        "client_address": "200 Innovation Blvd, Floor 9",
        "client_city": "San Francisco, CA 94107",
        "bank_name": "First National Bank",
        "account_number": "****7823",
        "swift_code": "FNBAUS6S",
        "items": [
            {"description": "Web Application Development (40 hrs)", "qty": 40, "unit_price": 120.00},
            {"description": "UI/UX Design Consultation", "qty": 8, "unit_price": 150.00},
            {"description": "Cloud Infrastructure Setup", "qty": 1, "unit_price": 850.00},
            {"description": "Monthly Maintenance Retainer", "qty": 1, "unit_price": 500.00},
        ],
        "subtotal": 7350.00,
        "tax_rate": 8.25,
        "tax_amount": 606.38,
        "total": 7956.38,
        "payment_terms": "Net 30",
        "notes": "Please reference invoice number on payment. Wire transfer preferred.",
    },
    {
        "vendor_name": "Meridian Consulting Group",
        "vendor_address": "1500 Market Street, Philadelphia, PA 19102",
        "vendor_email": "accounts@meridiancg.com",
        "vendor_phone": "+1 (215) 555-0847",
        "invoice_number": "INV-2024-0892",
        "issue_date": "2024-05-01",
        "due_date": "2024-05-31",
        "status": "OVERDUE",
        "client_name": "Northstar Manufacturing Co.",
        "client_address": "7700 Industrial Way",
        "client_city": "Detroit, MI 48201",
        "bank_name": "Keystone Commercial Bank",
        "account_number": "****2290",
        "swift_code": "KCOMUS33",
        "items": [
            {"description": "Strategic Planning Workshop (2 days)", "qty": 2, "unit_price": 2200.00},
            {"description": "Market Analysis Report", "qty": 1, "unit_price": 3500.00},
            {"description": "Implementation Roadmap Document", "qty": 1, "unit_price": 1200.00},
        ],
        "subtotal": 9100.00,
        "tax_rate": 6.00,
        "tax_amount": 546.00,
        "total": 9646.00,
        "payment_terms": "Net 30",
        "notes": "Late payment fee of 1.5% per month applies after due date.",
    },
]

RECEIPT_SAMPLES = [
    {
        "store_name": "FRESHMART GROCERY",
        "store_address": "412 Oak Avenue, Portland, OR 97201",
        "store_phone": "(503) 555-0288",
        "receipt_number": "RCP-88421",
        "date": "2024-06-10",
        "time": "14:32",
        "cashier": "Sarah K.",
        "payment_method": "Visa •••• 4412",
        "items": [
            {"name": "Organic Whole Milk 1gal", "qty": 2, "price": 5.49},
            {"name": "Sourdough Bread", "qty": 1, "price": 4.29},
            {"name": "Free Range Eggs 12ct", "qty": 1, "price": 6.99},
            {"name": "Avocado (ea)", "qty": 3, "price": 1.50},
            {"name": "Greek Yogurt 32oz", "qty": 1, "price": 7.49},
            {"name": "Baby Spinach 5oz", "qty": 1, "price": 3.99},
        ],
        "subtotal": 38.24,
        "discount": 2.00,
        "total": 36.24,
        "tendered": 40.00,
        "change": 3.76,
        "return_policy": "Returns accepted within 7 days with receipt.",
    },
    {
        "store_name": "QUICKFIX HARDWARE",
        "store_address": "230 Builder's Row, Denver, CO 80202",
        "store_phone": "(720) 555-0613",
        "receipt_number": "RCP-19057",
        "date": "2024-07-22",
        "time": "10:15",
        "cashier": "Marcus T.",
        "payment_method": "Cash",
        "items": [
            {"name": "3/4\" PVC Pipe 10ft", "qty": 4, "price": 3.89},
            {"name": "PVC Elbow Fitting", "qty": 6, "price": 0.79},
            {"name": "PVC Cement 8oz", "qty": 1, "price": 8.49},
            {"name": "Teflon Tape Roll", "qty": 2, "price": 1.29},
            {"name": "Adjustable Wrench 12\"", "qty": 1, "price": 24.99},
        ],
        "subtotal": 56.36,
        "discount": 0.00,
        "total": 56.36,
        "tendered": 60.00,
        "change": 3.64,
        "return_policy": "Unopened items returnable within 30 days.",
    },
]

PO_SAMPLES = [
    {
        "buyer_org": "Greenfield University",
        "buyer_address": "100 Campus Drive, Greenfield, MA 01301",
        "buyer_email": "procurement@greenfield.edu",
        "buyer_phone": "(413) 555-0320",
        "po_number": "PO-2024-GU-0055",
        "issue_date": "2024-04-08",
        "delivery_date": "2024-05-15",
        "vendor_name": "TechEquip Distributors LLC",
        "vendor_address": "980 Tech Corridor, Boston, MA 02110",
        "vendor_contact": "orders@techequip.com",
        "ship_to_name": "Greenfield University — IT Dept",
        "ship_to_address": "100 Campus Drive, Bldg C, Room 102",
        "ship_to_contact": "it-receiving@greenfield.edu",
        "bill_to_name": "Greenfield University — Accounts Payable",
        "bill_to_address": "100 Campus Drive, Admin Bldg, Room 201",
        "bill_to_contact": "ap@greenfield.edu",
        "payment_terms": "Net 45",
        "shipping_method": "Ground Freight",
        "fob_point": "Destination",
        "currency": "USD",
        "items": [
            {"sku": "MON-27-4K", "description": "27\" 4K IPS Monitor", "qty": 10, "unit": "EA", "unit_price": 399.00},
            {"sku": "KBD-MECH-BLK", "description": "Mechanical Keyboard (Black)", "qty": 10, "unit": "EA", "unit_price": 89.00},
            {"sku": "MSE-ERGO-GRY", "description": "Ergonomic Wireless Mouse", "qty": 10, "unit": "EA", "unit_price": 55.00},
            {"sku": "CAB-USB-C-6FT", "description": "USB-C Cable 6ft (10-pack)", "qty": 5, "unit": "PK", "unit_price": 34.00},
        ],
        "subtotal": 5600.00,
        "shipping_cost": 120.00,
        "total": 5720.00,
        "terms": "All goods subject to inspection. Payment within 45 days of receipt and invoice. Vendor to provide packing slip with each shipment.",
        "approver_name": "Dr. L. Patterson, VP Finance",
    },
    {
        "buyer_org": "Cascade Restaurants Group",
        "buyer_address": "55 Harbor View, Seattle, WA 98101",
        "buyer_email": "purchasing@cascadegroup.com",
        "buyer_phone": "(206) 555-0748",
        "po_number": "PO-2024-CRG-0312",
        "issue_date": "2024-08-19",
        "delivery_date": "2024-08-26",
        "vendor_name": "Pacific Coast Food Supply",
        "vendor_address": "3300 Pier Road, Tacoma, WA 98402",
        "vendor_contact": "sales@pacificcoastfood.com",
        "ship_to_name": "Cascade Restaurants — Central Kitchen",
        "ship_to_address": "120 Industrial Blvd, Unit 7, Seattle, WA 98108",
        "ship_to_contact": "kitchen-receiving@cascadegroup.com",
        "bill_to_name": "Cascade Restaurants Group — AP",
        "bill_to_address": "55 Harbor View, Seattle, WA 98101",
        "bill_to_contact": "ap@cascadegroup.com",
        "payment_terms": "Net 15",
        "shipping_method": "Refrigerated Delivery",
        "fob_point": "Origin",
        "currency": "USD",
        "items": [
            {"sku": "BEEF-GRND-80/20", "description": "Ground Beef 80/20, 10lb box", "qty": 50, "unit": "BOX", "unit_price": 42.00},
            {"sku": "CHKN-BRST-BNLS", "description": "Boneless Chicken Breast, 10lb", "qty": 30, "unit": "BAG", "unit_price": 38.50},
            {"sku": "SALM-ATL-FILLET", "description": "Atlantic Salmon Fillet, 5lb", "qty": 20, "unit": "PKG", "unit_price": 67.00},
            {"sku": "VEG-MIX-FRSH", "description": "Fresh Vegetable Mix, 20lb case", "qty": 15, "unit": "CASE", "unit_price": 28.00},
        ],
        "subtotal": 5015.00,
        "shipping_cost": 85.00,
        "total": 5100.00,
        "terms": "Refrigerated items must be delivered between 6AM–10AM. Vendor liable for spoilage if delivery window missed.",
        "approver_name": "M. Okafor, Purchasing Manager",
    },
]

MESSY_INVOICE = {
    "vendor_name": "Quickserve Freelance",
    "vendor_address": "P.O. Box 7711, Las Vegas, NV 89101",
    "vendor_email": "pay@quickserve.biz",
    "vendor_phone": "+1 (702) 555-0001",
    "invoice_number": "INV-EDGE-001",
    "issue_date": "2024-09-30",
    "due_date": "",
    "status": "UNPAID",
    "client_name": "TBD Client",
    "client_address": "Unknown",
    "client_city": "",
    "bank_name": "N/A",
    "account_number": "N/A",
    "swift_code": "N/A",
    "items": [
        {"description": "Logo Design", "qty": 1, "unit_price": 300.00},
        {"description": "Social Media Pack", "qty": 1, "unit_price": 150.00},
        {"description": "Rush Surcharge", "qty": 1, "unit_price": 75.00},
    ],
    "subtotal": 525.00,
    "tax_rate": 0.00,
    "tax_amount": 0.00,
    "total": 600.00,
    "payment_terms": "Due on receipt",
    "notes": "Total adjusted — prior credit applied. See attached.",
}


def render_pdf(template_name: str, context: dict, output_path: Path) -> None:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(template_name)
    html_content = template.render(**context)
    with open(output_path, "wb") as f:
        result = pisa.CreatePDF(BytesIO(html_content.encode("utf-8")), dest=f)
    if result.err:
        raise RuntimeError(f"PDF generation failed for {template_name}: {result.err}")
    print(f"  Generated: {output_path.name}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating sample PDFs...")

    for i, data in enumerate(INVOICE_SAMPLES, 1):
        render_pdf("invoice.html", data, OUTPUT_DIR / f"invoice_sample_{i}.pdf")

    for i, data in enumerate(RECEIPT_SAMPLES, 1):
        render_pdf("receipt.html", data, OUTPUT_DIR / f"receipt_sample_{i}.pdf")

    for i, data in enumerate(PO_SAMPLES, 1):
        render_pdf("purchase_order.html", data, OUTPUT_DIR / f"po_sample_{i}.pdf")

    render_pdf("invoice.html", MESSY_INVOICE, OUTPUT_DIR / "invoice_messy_edge.pdf")

    print(f"\nDone — 7 PDFs in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
