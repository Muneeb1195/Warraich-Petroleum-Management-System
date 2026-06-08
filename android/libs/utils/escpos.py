ESC = b"\x1b"
GS = b"\x1d"


def init():
    return ESC + b"@"


def align(n):
    return ESC + b"a" + bytes([n])


def bold_set(on=True):
    return ESC + b"!" + bytes([8 if on else 0])


def char_size(n):
    return GS + b"!" + bytes([n])


def linefeed(n=1):
    return b"\n" * n


def cut():
    return GS + b"V\x00"


def text(s, encoding="cp437"):
    return s.encode(encoding, errors="replace")


def hline(c="-", width=32):
    return (c * width)[:width] + "\n"


def format_receipt(sale_data, business_info):
    lines = bytearray()
    lines.extend(init())
    lines.extend(align(1))
    lines.extend(bold_set(True))
    lines.extend(char_size(1))
    lines.extend(text(business_info.get("name", "WARRAICH PETROLEUM")))
    lines.extend(linefeed())
    lines.extend(bold_set(False))
    lines.extend(char_size(0))
    addr = business_info.get("address", "")
    if addr:
        lines.extend(text(addr))
        lines.extend(linefeed())
    phone = business_info.get("phone", "")
    if phone:
        lines.extend(text(f"Phone: {phone}"))
        lines.extend(linefeed())
    gstin = business_info.get("gstin", "")
    if gstin:
        lines.extend(text(f"GSTIN: {gstin}"))
        lines.extend(linefeed())
    lines.extend(align(0))
    lines.extend(text(hline()))
    lines.extend(text(f"Invoice: {sale_data.get('invoice', 'N/A')}"))
    lines.extend(linefeed())
    lines.extend(text(f"Date: {sale_data.get('date', '')}"))
    lines.extend(linefeed())
    lines.extend(text(f"Payment: {sale_data.get('payment_mode', '')}"))
    lines.extend(linefeed())
    lines.extend(text(hline()))
    lines.extend(text(f"{'Item':<18}{'Qty':>6}{'Rate':>8}{'Amount':>8}"))
    lines.extend(linefeed())
    for it in sale_data.get("items", []):
        name = it.get("name", "")[:18]
        qty = it.get("qty_display", "")
        rate = it.get("rate_display", "")
        amt = it.get("amount_display", "")
        lines.extend(text(f"{name:<18}{qty:>6}{rate:>8}{amt:>8}"))
        lines.extend(linefeed())
    lines.extend(text(hline()))
    lines.extend(text(f"{'Subtotal':>26}{'':>8}{sale_data.get('taxable_display', ''):>8}"))
    lines.extend(linefeed())
    lines.extend(text(f"{'CGST':>26}{'':>8}{sale_data.get('cgst_display', ''):>8}"))
    lines.extend(linefeed())
    lines.extend(text(f"{'SGST':>26}{'':>8}{sale_data.get('sgst_display', ''):>8}"))
    lines.extend(linefeed())
    lines.extend(text(hline("-", 42)))
    lines.extend(bold_set(True))
    lines.extend(text(f"{'TOTAL':>26}{'':>8}{sale_data.get('grand_total_display', ''):>8}"))
    lines.extend(linefeed())
    lines.extend(bold_set(False))
    lines.extend(linefeed())
    lines.extend(align(1))
    lines.extend(text("Thank you!"))
    lines.extend(linefeed(3))
    lines.extend(cut())
    return bytes(lines)
