from models.base import BaseModel
from database.connection import get_connection
from models.employee import Attendance


class Payroll(BaseModel):
    TABLE = "payroll"

    @classmethod
    def calculate(cls, employee_id, month, year):
        from models.employee import Employee
        emp = Employee.get_by_id(employee_id)
        if not emp:
            return None
        if emp["salary_type"] == "Fixed":
            gross = emp["salary_amount"]
            working_days = 30
        else:
            present_days = Attendance.get_present_days(employee_id, month, year)
            gross = present_days * emp["salary_amount"]
            working_days = present_days
        deductions = 0
        net = gross - deductions
        conn = get_connection()
        conn.execute(
            """INSERT OR REPLACE INTO payroll
               (employee_id, month, year, working_days, gross_salary, deductions, net_salary)
               VALUES (?,?,?,?,?,?,?)""",
            (employee_id, month, year, working_days, gross, deductions, net),
        )
        conn.commit()
        conn.close()
        return {"gross": gross, "deductions": deductions, "net": net}

    @classmethod
    def mark_paid(cls, payroll_id, notes=""):
        conn = get_connection()
        conn.execute(
            "UPDATE payroll SET paid=1, paid_date=date('now'), notes=? WHERE id=?",
            (notes, payroll_id),
        )
        conn.commit()
        conn.close()

    @classmethod
    def get_by_month(cls, month, year):
        conn = get_connection()
        rows = conn.execute("""
            SELECT p.*, e.name as employee_name, e.role, e.salary_type
            FROM payroll p
            JOIN employees e ON e.id = p.employee_id
            WHERE p.month=? AND p.year=?
            ORDER BY e.name
        """, (month, year)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def get_for_employee(cls, employee_id, month, year):
        conn = get_connection()
        row = conn.execute("""
            SELECT p.*, e.name as employee_name, e.role
            FROM payroll p
            JOIN employees e ON e.id = p.employee_id
            WHERE p.employee_id=? AND p.month=? AND p.year=?
        """, (employee_id, month, year)).fetchone()
        conn.close()
        return dict(row) if row else None
