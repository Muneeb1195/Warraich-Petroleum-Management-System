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
    def update_balance(cls, id, amount_change):
        conn = get_connection()
        conn.execute("UPDATE customers SET balance = balance + ? WHERE id=?", (amount_change, id))
        conn.commit()
        conn.close()
