from models.base import BaseModel
from database.connection import get_connection


class LubeProduct(BaseModel):
    TABLE = "lube_products"

    @classmethod
    def create(cls, brand, product_name, unit="Bottle", purchase_rate=0,
               selling_price=0, stock_qty=0, hsn_code="", gst_rate=18):
        conn = get_connection()
        conn.execute(
            """INSERT INTO lube_products
               (brand, product_name, unit, purchase_rate, selling_price, stock_qty, hsn_code, gst_rate)
               VALUES (?,?,?,?,?,?,?,?)""",
            (brand, product_name, unit, purchase_rate, selling_price, stock_qty, hsn_code, gst_rate),
        )
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id

    @classmethod
    def update(cls, id, **kwargs):
        allowed = ["brand", "product_name", "unit", "purchase_rate",
                   "selling_price", "stock_qty", "hsn_code", "gst_rate"]
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k in allowed:
                sets.append(f"{k}=?")
                vals.append(v)
        if not sets:
            return
        vals.append(id)
        conn = get_connection()
        conn.execute(f"UPDATE lube_products SET {', '.join(sets)} WHERE id=?", vals)
        conn.commit()
        conn.close()

    @classmethod
    def adjust_stock(cls, id, qty_change):
        conn = get_connection()
        conn.execute("UPDATE lube_products SET stock_qty = stock_qty + ? WHERE id=?", (qty_change, id))
        conn.commit()
        conn.close()
