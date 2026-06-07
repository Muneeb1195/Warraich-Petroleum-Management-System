from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, Image)
from reportlab.pdfgen import canvas

from database.settings import settings
from utils.paths import docs_dir

OUTPUT_DIR = docs_dir()


def generate_invoice(sale_data, items):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"invoice_{sale_data['invoice_no']}.pdf"
    filepath = OUTPUT_DIR / filename

    doc = SimpleDocTemplate(
        str(filepath), pagesize=A4,
        topMargin=15*mm, bottomMargin=15*mm,
        leftMargin=15*mm, rightMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"],
                                  fontSize=18, textColor=colors.HexColor("#0d1117"),
                                  spaceAfter=4, spaceBefore=0)
    normal = ParagraphStyle("Normal2", parent=styles["Normal"],
                             fontSize=10, textColor=colors.HexColor("#333"),
                             spaceAfter=2)
    small = ParagraphStyle("Small2", parent=styles["Normal"],
                            fontSize=9, textColor=colors.HexColor("#555"))

    elements = []

    # Header
    elements.append(Paragraph(f"<b>{settings.business_name()}</b>", title_style))
    addr = settings.business_address() or "Address not set"
    elements.append(Paragraph(addr, normal))
    gst = settings.gstin()
    if gst:
        elements.append(Paragraph(f"GSTIN: {gst}", normal))
    phone = settings.business_phone()
    if phone:
        elements.append(Paragraph(f"Phone: {phone}", normal))
    elements.append(Spacer(1, 8*mm))

    # Invoice info
    inv_style = ParagraphStyle("Inv", parent=normal, fontSize=10, spaceAfter=2)
    cust_name = sale_data.get("customer_name") or "Walk-in Customer"
    elements.append(Paragraph(f"Invoice: <b>{sale_data['invoice_no']}</b>", inv_style))
    elements.append(Paragraph(f"Date: {sale_data['sale_date']}", inv_style))
    elements.append(Paragraph(f"Customer: {cust_name}", inv_style))
    if sale_data.get("customer_gstin"):
        elements.append(Paragraph(f"Customer GSTIN: {sale_data['customer_gstin']}", inv_style))
    elements.append(Paragraph(f"Payment: {sale_data['payment_mode']}", inv_style))
    elements.append(Spacer(1, 6*mm))

    # Items table header
    data = [["#", "Item", "Qty", "Rate", "Amount"]]
    for i, item in enumerate(items, 1):
        name = item.get("fuel_name") or f"{item.get('brand', '')} {item.get('lube_name', '')}".strip() or "Quick Sale"
        pump = item.get("pump_no")
        if pump:
            name = f"{name} - {pump}"
        unit = item.get("unit", "")
        qty_str = f"{item['qty']:,.2f}"
        if item.get("opening_reading") is not None:
            qty_str += " L"
        data.append([
            str(i),
            name,
            qty_str,
            f"{settings.currency_symbol()}{item['rate']:,.2f}",
            f"{settings.currency_symbol()}{item['amount']:,.2f}",
        ])

    # Totals
    data.append(["", "", "", "Taxable:", f"{settings.currency_symbol()}{sale_data['taxable_amount']:,.2f}"])
    data.append(["", "", "", f"CGST @ {sale_data['gst_rate']/2:.1f}%:", f"{settings.currency_symbol()}{sale_data['cgst_amount']:,.2f}"])
    data.append(["", "", "", f"SGST @ {sale_data['gst_rate']/2:.1f}%:", f"{settings.currency_symbol()}{sale_data['sgst_amount']:,.2f}"])
    data.append(["", "", "", "Total:", f"{settings.currency_symbol()}{sale_data['total_amount']:,.2f}"])
    if sale_data['round_off']:
        data.append(["", "", "", "Round Off:", f"{settings.currency_symbol()}{sale_data['round_off']:,.2f}"])
    data.append(["", "", "", "GRAND TOTAL:", f"{settings.currency_symbol()}{sale_data['grand_total']:,.0f}"])

    col_widths = [20*mm, 80*mm, 30*mm, 30*mm, 35*mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, -5), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -5), (-1, -1), 10),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#0d1117")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f2f5")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f5e9")),
        ("GRID", (0, 0), (-1, -5), 0.5, colors.HexColor("#ddd")),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#333")),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10*mm))

    # Footer
    elements.append(Spacer(1, 10*mm))
    words = _number_to_words(int(sale_data['grand_total']))
    elements.append(Paragraph(
        f"Amount in words: <b>{settings.currency_symbol()} {words} only</b>", small))
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph("Thank you for your business!", normal))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%d/%m/%Y %I:%M %p')}", small))

    doc.build(elements)
    return str(filepath)


def _number_to_words(n):
    if n == 0:
        return "Zero"
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    if n < 20:
        return ones[n]
    if n < 100:
        return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
    if n < 1000:
        return ones[n // 100] + " Hundred" + (" " + _number_to_words(n % 100) if n % 100 else "")
    if n < 100000:
        return _number_to_words(n // 1000) + " Thousand" + (" " + _number_to_words(n % 1000) if n % 1000 else "")
    if n < 10000000:
        return _number_to_words(n // 100000) + " Lakh" + (" " + _number_to_words(n % 100000) if n % 100000 else "")
    return _number_to_words(n // 10000000) + " Crore" + (" " + _number_to_words(n % 10000000) if n % 10000000 else "")
