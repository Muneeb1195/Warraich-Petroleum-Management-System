from datetime import datetime

from models.base import BaseModel
from database.connection import get_connection
from database.settings import settings


class Sale(BaseModel):
    TABLE = "sales"

    @classmethod
    def create(cls, customer_id=None, payment_mode="Cash", gst_rate=None):
        if gst_rate is None:
            gst_rate = settings.default_gst_rate()
        conn = get_connection()
        inv_no = cls._next_invoice_no(conn)
        conn.execute(
            """INSERT INTO sales
               (invoice_no, customer_id, payment_mode, gst_rate)
               VALUES (?,?,?,?)""",
            (inv_no, customer_id, payment_mode, gst_rate),
        )
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id, inv_no

    @classmethod
    def _next_invoice_no(cls, conn):
        row = conn.execute("SELECT COUNT(*) as c FROM sales").fetchone()
        return f"INV-{row['c'] + 1:05d}"

    @classmethod
    def add_fuel_item(cls, sale_id, pump_id, opening_reading, closing_reading, rate):
        qty = closing_reading - opening_reading
        amount = round(qty * rate, 2)
        conn = get_connection()
        conn.execute(
            """INSERT INTO sale_items
               (sale_id, item_type, pump_id, opening_reading, closing_reading, qty, rate, amount)
               VALUES (?, 'fuel', ?, ?, ?, ?, ?, ?)""",
            (sale_id, pump_id, opening_reading, closing_reading, qty, rate, amount),
        )
        conn.commit()
        conn.close()
        return amount

    @classmethod
    def add_lube_item(cls, sale_id, lube_product_id, qty, rate):
        amount = round(qty * rate, 2)
        conn = get_connection()
        conn.execute(
            """INSERT INTO sale_items
               (sale_id, item_type, lube_product_id, qty, rate, amount)
               VALUES (?, 'lube', ?, ?, ?, ?)""",
            (sale_id, lube_product_id, qty, rate, amount),
        )
        conn.commit()
        conn.close()
        return amount

    @classmethod
    def calculate_totals(cls, sale_id):
        conn = get_connection()
        sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
        if not sale:
            conn.close()
            return None
        taxable = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as t FROM sale_items WHERE sale_id=?",
            (sale_id,),
        ).fetchone()["t"]
        taxable = round(taxable, 2)
        gst_rate = sale["gst_rate"]
        half_gst = round(taxable * gst_rate / 100 / 2, 2)
        total = taxable + half_gst * 2
        gt = round(total)
        round_off = round(gt - total, 2)
        conn.execute(
            """UPDATE sales SET
               taxable_amount=?, cgst_amount=?, sgst_amount=?,
               total_amount=?, round_off=?, grand_total=?
               WHERE id=?""",
            (taxable, half_gst, half_gst, total, round_off, gt, sale_id),
        )
        conn.commit()
        conn.close()
        return {
            "taxable": taxable,
            "cgst": half_gst,
            "sgst": half_gst,
            "total": total,
            "round_off": round_off,
            "grand_total": gt,
        }

    @classmethod
    def get_with_details(cls, sale_id):
        conn = get_connection()
        sale = conn.execute("""
            SELECT s.*, c.name as customer_name, c.gstin as customer_gstin
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            WHERE s.id=?
        """, (sale_id,)).fetchone()
        if not sale:
            conn.close()
            return None
        items = conn.execute("""
            SELECT si.*, p.pump_no, f.name as fuel_name,
                   lp.brand, lp.product_name as lube_name, lp.unit
            FROM sale_items si
            LEFT JOIN pumps p ON p.id = si.pump_id
            LEFT JOIN tanks t ON t.id = p.tank_id
            LEFT JOIN fuel_types f ON f.id = t.fuel_type_id
            LEFT JOIN lube_products lp ON lp.id = si.lube_product_id
            WHERE si.sale_id=?
        """, (sale_id,)).fetchall()
        conn.close()
        result = dict(sale)
        result["items"] = [dict(r) for r in items]
        return result

    @classmethod
    def get_all_summary(cls, limit=100, include_voided=False):
        conn = get_connection()
        where = "" if include_voided else "WHERE s.voided IS NULL OR s.voided = 0"
        rows = conn.execute(f"""
            SELECT s.id, s.invoice_no, s.sale_date, s.payment_mode,
                   s.grand_total, s.voided, c.name as customer_name
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            {where}
            ORDER BY s.sale_date DESC, s.id DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def void(cls, sale_id, reason=""):
        conn = get_connection()
        sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
        if not sale:
            conn.close()
            return False, "Sale not found."
        if sale.get("voided"):
            conn.close()
            return False, "Sale already voided."

        # Reverse lube stock
        items = conn.execute(
            "SELECT * FROM sale_items WHERE sale_id=? AND item_type='lube'",
            (sale_id,),
        ).fetchall()
        for item in items:
            conn.execute(
                "UPDATE lube_products SET stock_qty = stock_qty + ? WHERE id=?",
                (item["qty"], item["lube_product_id"]),
            )

        # Reverse customer balance if credit
        if sale["payment_mode"] == "Credit" and sale["customer_id"]:
            conn.execute(
                "UPDATE customers SET balance = balance - ? WHERE id=?",
                (sale["grand_total"], sale["customer_id"]),
            )

        conn.execute(
            "UPDATE sales SET voided=1, voided_at=?, void_reason=? WHERE id=?",
            (datetime.now().isoformat(), reason, sale_id),
        )
        conn.commit()
        conn.close()
        return True, "Sale voided."
