"""Order invoice PDF generation.

Kept deliberately simple (fpdf2, no HTML/CSS rendering engine, no external
service) -- an invoice is a small, structured, one-page document, and this
avoids pulling in a heavyweight rendering stack for it.
"""
from fpdf import FPDF


def _safe(text) -> str:
    """fpdf2's built-in core fonts (Helvetica included) only support Latin-1.
    Every string here can contain arbitrary user input -- a customer's name,
    a shipping address, a product name -- so anything outside that range
    (accented characters are fine; curly quotes, emoji, or non-Latin scripts
    are not) would crash PDF generation entirely. Degrading a character to
    '?' is far better than a 500 on every invoice download for that order."""
    text = str(text)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_invoice_pdf(order) -> bytes:
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Kaira", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 6, "Ghana Fashion Marketplace", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, f"Invoice - Order #{order.id}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Date: {order.created_at.strftime('%d %B %Y')}", ln=True)
    pdf.cell(0, 6, f"Status: {order.get_status_display()}  |  Payment: {order.get_payment_status_display()}", ln=True)
    if order.tracking_number:
        pdf.cell(0, 6, _safe(f"Tracking number: {order.tracking_number}"), ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Bill / ship to", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _safe(order.shipping_name), ln=True)
    pdf.multi_cell(0, 6, _safe(order.shipping_address or "-"))
    pdf.cell(0, 6, _safe(order.shipping_phone), ln=True)
    pdf.ln(4)

    # Items table
    pdf.set_font("Helvetica", "B", 10)
    col_widths = (80, 30, 30, 25, 25)
    headers = ("Item", "Size/Color", "Qty", "Unit price", "Line total")
    for width, header in zip(col_widths, headers):
        pdf.cell(width, 8, header, border="B")
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    for item in order.items.all():
        pdf.cell(col_widths[0], 8, _safe(item.product_name[:40]))
        pdf.cell(col_widths[1], 8, _safe(f"{item.size}/{item.color}"))
        pdf.cell(col_widths[2], 8, str(item.quantity))
        pdf.cell(col_widths[3], 8, f"GHS {item.unit_price:.2f}")
        pdf.cell(col_widths[4], 8, f"GHS {item.line_total:.2f}")
        pdf.ln()

    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    label_width = sum(col_widths[:-1])
    pdf.cell(label_width, 7, "Shipping", align="R")
    pdf.cell(col_widths[-1], 7, f"GHS {order.shipping_cost:.2f}")
    pdf.ln()

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(label_width, 8, "Total", align="R")
    pdf.cell(col_widths[-1], 8, f"GHS {order.total_amount:.2f}")

    return bytes(pdf.output())
