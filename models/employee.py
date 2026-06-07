from models.base import BaseModel
from database.connection import get_connection


class Employee(BaseModel):
    TABLE = "employees"

    @classmethod
    def create(cls, name, role, phone="", address="", bank_name="",
               bank_account="", ifsc_code="", salary_type="Fixed",
               salary_amount=0):
        conn = get_connection()
        conn.execute(
            """INSERT INTO employees
               (name, role, phone, address, bank_name, bank_account, ifsc_code, salary_type, salary_amount)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (name, role, phone, address, bank_name, bank_account, ifsc_code, salary_type, salary_amount),
        )
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id

    @classmethod
    def update(cls, id, **kwargs):
        allowed = ["name", "role", "phone", "address", "bank_name",
                   "bank_account", "ifsc_code", "salary_type", "salary_amount", "is_active"]
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
        conn.execute(f"UPDATE employees SET {', '.join(sets)} WHERE id=?", vals)
        conn.commit()
        conn.close()

    @classmethod
    def get_active(cls):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM employees WHERE is_active=1 ORDER BY name"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def get_roles(cls):
        conn = get_connection()
        rows = conn.execute(
            "SELECT DISTINCT role FROM employees WHERE is_active=1 ORDER BY role"
        ).fetchall()
        conn.close()
        return [r["role"] for r in rows]


class Attendance(BaseModel):
    TABLE = "attendance"

    @classmethod
    def mark(cls, employee_id, date, shift, status="Present"):
        conn = get_connection()
        conn.execute(
            """INSERT OR REPLACE INTO attendance (employee_id, date, shift, status)
               VALUES (?,?,?,?)""",
            (employee_id, date, shift, status),
        )
        conn.commit()
        conn.close()

    @classmethod
    def get_by_date(cls, date):
        conn = get_connection()
        rows = conn.execute("""
            SELECT a.*, e.name as employee_name, e.role
            FROM attendance a
            JOIN employees e ON e.id = a.employee_id
            WHERE a.date=?
            ORDER BY e.name
        """, (date,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def get_present_days(cls, employee_id, month, year):
        conn = get_connection()
        rows = conn.execute(
            """SELECT COUNT(*) as days FROM attendance
               WHERE employee_id=? AND status='Present'
               AND strftime('%m', date)=? AND strftime('%Y', date)=?""",
            (employee_id, f"{month:02d}", str(year)),
        ).fetchone()
        conn.close()
        return rows["days"] if rows else 0

    @classmethod
    def get_by_month(cls, employee_id, month, year):
        conn = get_connection()
        rows = conn.execute(
            """SELECT * FROM attendance
               WHERE employee_id=?
               AND strftime('%m', date)=? AND strftime('%Y', date)=?
               ORDER BY date""",
            (employee_id, f"{month:02d}", str(year)),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
