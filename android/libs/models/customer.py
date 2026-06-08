from models.base import BaseModel
from database.connection import get_connection


class Customer(BaseModel):
    TABLE = "customers"

    @classmethod
    def create(cls, name, phone="", address="", gstin="", credit_limit=0):
        conn = get_connection()
        conn.execute(
            "INSERT INTO customers (name, phone, address, gstin, credit_limit) VALUES (?,?,?,?,?)",
            (name, phone, address, gstin, credit_limit),
        )
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id

    @classmethod
    def search(cls, text=""):
        if not text.strip():
            return cls.get_all("name")
        conn = get_connection()
        like = f"%{text.strip()}%"
        rows = conn.execute(
            "SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? ORDER BY name",
            (like, like),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def update_balance(cls, id, amount_change):
        conn = get_connection()
        conn.execute("UPDATE customers SET balance = balance + ? WHERE id=?", (amount_change, id))
        conn.commit()
        conn.close()
