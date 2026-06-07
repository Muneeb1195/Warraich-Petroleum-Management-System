from models.base import BaseModel
from database.connection import get_connection


class Supplier(BaseModel):
    TABLE = "suppliers"

    @classmethod
    def create(cls, name, phone="", address="", gstin=""):
        conn = get_connection()
        conn.execute(
            "INSERT INTO suppliers (name, phone, address, gstin) VALUES (?,?,?,?)",
            (name, phone, address, gstin),
        )
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id

    @classmethod
    def update(cls, id, **kwargs):
        allowed = ["name", "phone", "address", "gstin"]
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
        conn.execute(f"UPDATE suppliers SET {', '.join(sets)} WHERE id=?", vals)
        conn.commit()
        conn.close()
