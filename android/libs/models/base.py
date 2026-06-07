from database.connection import get_connection


class BaseModel:

    TABLE = ""

    @classmethod
    def get_all(cls, order_by="id"):
        conn = get_connection()
        rows = conn.execute(f"SELECT * FROM {cls.TABLE} ORDER BY {order_by}").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def get_by_id(cls, id):
        conn = get_connection()
        row = conn.execute(f"SELECT * FROM {cls.TABLE} WHERE id=?", (id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def delete(cls, id):
        conn = get_connection()
        conn.execute(f"DELETE FROM {cls.TABLE} WHERE id=?", (id,))
        conn.commit()
        conn.close()

    @classmethod
    def count(cls):
        conn = get_connection()
        row = conn.execute(f"SELECT COUNT(*) as c FROM {cls.TABLE}").fetchone()
        conn.close()
        return row["c"]

    @classmethod
    def execute(cls, query, params=None):
        conn = get_connection()
        if params:
            conn.execute(query, params)
        else:
            conn.execute(query)
        conn.commit()
        conn.close()

    @classmethod
    def fetch(cls, query, params=None):
        conn = get_connection()
        if params:
            rows = conn.execute(query, params).fetchall()
        else:
            rows = conn.execute(query).fetchall()
        conn.close()
        return [dict(r) for r in rows]
