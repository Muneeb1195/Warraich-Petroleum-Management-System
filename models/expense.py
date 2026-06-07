from models.base import BaseModel
from database.connection import get_connection


class ExpenseCategory(BaseModel):
    TABLE = "expense_categories"

    @classmethod
    def create(cls, name):
        conn = get_connection()
        conn.execute("INSERT INTO expense_categories (name) VALUES (?)", (name,))
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id


class Expense(BaseModel):
    TABLE = "expenses"

    @classmethod
    def create(cls, category_id, amount, description="", expense_date=None):
        conn = get_connection()
        if expense_date:
            conn.execute(
                "INSERT INTO expenses (category_id, amount, description, expense_date) VALUES (?,?,?,?)",
                (category_id, amount, description, expense_date),
            )
        else:
            conn.execute(
                "INSERT INTO expenses (category_id, amount, description) VALUES (?,?,?)",
                (category_id, amount, description),
            )
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id

    @classmethod
    def get_with_category(cls, expense_id=None):
        conn = get_connection()
        if expense_id:
            rows = conn.execute("""
                SELECT e.*, c.name as category_name
                FROM expenses e
                JOIN expense_categories c ON c.id = e.category_id
                WHERE e.id=?
                ORDER BY e.expense_date DESC
            """, (expense_id,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT e.*, c.name as category_name
                FROM expenses e
                JOIN expense_categories c ON c.id = e.category_id
                ORDER BY e.expense_date DESC
            """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def total_by_date_range(cls, start_date, end_date):
        conn = get_connection()
        row = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as total FROM expenses WHERE expense_date BETWEEN ? AND ?",
            (start_date, end_date),
        ).fetchone()
        conn.close()
        return row["total"]
