from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from libs.database.settings import settings


def generate_invoice(inv_no, items, totals, payment_mode, customer_name=""):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    bw, bh = pdf.w, pdf.h
    margin = 15
    pdf.set_margins(margin, margin, margin)
    usable = bw - 2 * margin

    # === Company Header ===
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 10, settings.business_name(), align="C")
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 9)
    addr = settings.business_address()
    phone = settings.business_phone()
    gstin = settings.gstin()
    lines = [addr, f"Phone: {phone}"] if phone else [addr]
    if gstin:
        lines.append(f"GSTIN: {gstin}")
    for line in lines:
        pdf.cell(0, 4.5, line, align="C")
        pdf.ln(4.5)

    pdf.ln(2)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(margin, pdf.get_y(), bw - margin, pdf.get_y())
    pdf.ln(4)

    # === Invoice Info ===
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(usable / 2, 6, f"Invoice #: {inv_no}")
    pdf.cell(usable / 2, 6, f"Date: {datetime.now().strftime('%d/%m/%Y')}", align="R")
    pdf.ln(6)
    if customer_name:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Customer: {customer_name}")
        pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Payment: {payment_mode}")
    pdf.ln(4)

    pdf.set_draw_color(180, 180, 180)
    pdf.line(margin, pdf.get_y(), bw - margin, pdf.get_y())
    pdf.ln(4)

    # === Items Table Header ===
    col_w = [usable * 0.44, usable * 0.14, usable * 0.18, usable * 0.24]
    headers = ["Description", "Qty", "Rate", "Amount"]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, align="C" if i > 0 else "L", fill=True)
    pdf.ln()

    # === Items ===
    pdf.set_font("Helvetica", "", 9)
    for item in items:
        name = item.get("name", "")[:50]
        qty = item.get("qty_display", "")
        rate = item.get("rate_display", "")
        amt = item.get("amount_display", "")
        y_before = pdf.get_y()
        pdf.cell(col_w[0], 6, name, border=1)
        pdf.cell(col_w[1], 6, qty, border=1, align="C")
        pdf.cell(col_w[2], 6, rate, border=1, align="R")
        pdf.cell(col_w[3], 6, amt, border=1, align="R")
        pdf.ln()

    # === Totals ===
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    total_w = col_w[0] + col_w[1]
    val_w = col_w[2] + col_w[3]
    for label, val in [
        ("Subtotal:", totals.get("taxable_display", "")),
        ("CGST:", totals.get("cgst_display", "")),
        ("SGST:", totals.get("sgst_display", "")),
    ]:
        pdf.cell(total_w, 6, label, align="R")
        pdf.cell(val_w, 6, val, align="R")
        pdf.ln(6)

    pdf.set_draw_color(180, 180, 180)
    pdf.line(margin + total_w, pdf.get_y(), bw - margin, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(total_w, 7, "TOTAL:", align="R")
    pdf.cell(val_w, 7, totals.get("grand_total_display", ""), align="R")
    pdf.ln(10)

    # === Footer ===
    pdf.set_font("Helvetica", "", 9)
    pdf.ln(10)
    pdf.line(margin + total_w * 0.5, pdf.get_y(), bw - margin, pdf.get_y())
    y_sig = pdf.get_y() + 1
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4, "Authorized Signature", align="R")
    pdf.set_y(y_sig)

    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "Thank you for your business!", align="C")

    # === Save ===
    from libs.utils.paths import docs_dir
    out_dir = docs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"invoice_{inv_no.replace('/', '_')}.pdf"
    out_path = out_dir / filename
    pdf.output(str(out_path))
    return out_path
