from models.base import BaseModel
from database.connection import get_connection


class Purchase(BaseModel):
    TABLE = "purchases"

    @classmethod
    def create(cls, supplier_id, invoice_no="", notes="", purchase_date=None):
        conn = get_connection()
        if purchase_date:
            conn.execute(
                "INSERT INTO purchases (supplier_id, invoice_no, notes, purchase_date) VALUES (?,?,?,?)",
                (supplier_id, invoice_no, notes, purchase_date),
            )
        else:
            conn.execute(
                "INSERT INTO purchases (supplier_id, invoice_no, notes) VALUES (?,?,?)",
                (supplier_id, invoice_no, notes),
            )
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id

    @classmethod
    def add_item(cls, purchase_id, item_type, fuel_type_id=None,
                 lube_product_id=None, qty=0, rate=0):
        amount = qty * rate
        conn = get_connection()
        conn.execute(
            """INSERT INTO purchase_items
               (purchase_id, item_type, fuel_type_id, lube_product_id, qty, rate, amount)
               VALUES (?,?,?,?,?,?,?)""",
            (purchase_id, item_type, fuel_type_id, lube_product_id, qty, rate, amount),
        )
        conn.commit()
        conn.close()
        return amount

    @classmethod
    def update_total(cls, purchase_id):
        conn = get_connection()
        row = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as total FROM purchase_items WHERE purchase_id=?",
            (purchase_id,),
        ).fetchone()
        conn.execute("UPDATE purchases SET total_amount=? WHERE id=?", (row["total"], purchase_id))
        conn.commit()
        conn.close()
        return row["total"]

    @classmethod
    def get_with_supplier(cls, purchase_id):
        conn = get_connection()
        row = conn.execute("""
            SELECT p.*, s.name as supplier_name
            FROM purchases p
            JOIN suppliers s ON s.id = p.supplier_id
            WHERE p.id=?
        """, (purchase_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def get_items(cls, purchase_id):
        conn = get_connection()
        rows = conn.execute("""
            SELECT pi.*, f.name as fuel_name, lp.product_name as lube_name, lp.brand
            FROM purchase_items pi
            LEFT JOIN fuel_types f ON f.id = pi.fuel_type_id
            LEFT JOIN lube_products lp ON lp.id = pi.lube_product_id
            WHERE pi.purchase_id=?
        """, (purchase_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def get_all_with_supplier(cls):
        conn = get_connection()
        rows = conn.execute("""
            SELECT p.*, s.name as supplier_name
            FROM purchases p
            JOIN suppliers s ON s.id = p.supplier_id
            ORDER BY p.purchase_date DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
