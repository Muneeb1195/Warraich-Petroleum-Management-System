from datetime import datetime, timedelta, date

from kivy.uix.screenmanager import Screen
from libs.utils.theme import *
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.clock import Clock

from libs.database.connection import get_connection
from libs.models.sale import Sale
from libs.models.expense import Expense
from libs.utils.formatting import curr


class ReportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_rows = []

    def on_enter(self):
        self._set_date_preset("this_month")

    def _set_date_preset(self, preset):
        today = date.today()
        if preset == "today":
            self.ids.from_input.text = today.isoformat()
            self.ids.to_input.text = today.isoformat()
        elif preset == "yesterday":
            yest = today - timedelta(days=1)
            self.ids.from_input.text = yest.isoformat()
            self.ids.to_input.text = yest.isoformat()
        elif preset == "this_month":
            self.ids.from_input.text = today.replace(day=1).isoformat()
            self.ids.to_input.text = today.isoformat()

    def generate(self):
        self._loading = Popup(
            title="",
            content=Label(text="Generating report...", color=TEXT_PRIMARY),
            size_hint=(0.5, 0.15),
            background="", background_color=(0.09, 0.09, 0.12, 0.95),
            auto_dismiss=False,
        )
        self._loading.open()
        Clock.schedule_once(lambda *a: self._do_generate(), 0.1)

    def _do_generate(self):
        report_type = self.ids.report_spinner.text
        from_d = self.ids.from_input.text.strip()
        to_d = self.ids.to_input.text.strip()

        try:
            if report_type == "Daily Summary":
                self._daily_summary(from_d, to_d)
            elif report_type == "Profit & Loss":
                self._profit_loss(from_d, to_d)
            elif report_type == "Sales Report":
                self._sales_report(from_d, to_d)
            elif report_type == "Stock Report":
                self._stock_report()
            elif report_type == "Expense Report":
                self._expense_report(from_d, to_d)
            elif report_type == "Payroll Report":
                self._payroll_report()
        except Exception as e:
            self._display_results([], [], f"Error: {e}")
        if hasattr(self, '_loading') and self._loading:
            self._loading.dismiss()

    def _display_results(self, headers, rows, summary=""):
        self.ids.summary_label.text = summary
        container = self.ids.result_container
        container.clear_widgets()

        self._current_rows = rows

        if not rows:
            container.add_widget(Label(
                text="No data found for the selected period.",
                color=TEXT_AMBER,
                size_hint_y=None, height=dp(40),
            ))
            container.add_widget(Widget(size_hint_y=1))
            return

        total_sx = sum(sx for _, sx in headers)
        header_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(26),
            spacing=dp(2), padding=[dp(2), 0],
        )
        for label, sx in headers:
            header_row.add_widget(Label(
                text=label, size_hint_x=sx / total_sx,
                bold=True, color=TEXT_SECONDARY, font_size="11sp",
            ))
        container.add_widget(header_row)

        for row in rows:
            row_box = BoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(30),
                spacing=dp(2), padding=[dp(2), dp(2)],
            )
            for cell, sx in zip(row, [sx for _, sx in headers]):
                lbl = Label(
                    text=str(cell) if cell is not None else "",
                    size_hint_x=sx / total_sx,
                    halign="left", color=TEXT_PRIMARY, font_size="11sp",
                )
                row_box.add_widget(lbl)
            container.add_widget(row_box)

        container.add_widget(Widget(size_hint_y=1))

    def _daily_summary(self, from_d, to_d):
        conn = get_connection()
        rows = conn.execute("""
            SELECT sale_date, COUNT(*) as invoices,
                   SUM(grand_total) as total_sales,
                   SUM(CASE WHEN payment_mode='Cash' THEN grand_total ELSE 0 END) as cash,
                   SUM(CASE WHEN payment_mode='Card' THEN grand_total ELSE 0 END) as card,
                   SUM(CASE WHEN payment_mode='UPI' THEN grand_total ELSE 0 END) as upi,
                   SUM(CASE WHEN payment_mode='Credit' THEN grand_total ELSE 0 END) as credit
            FROM sales
            WHERE sale_date BETWEEN ? AND ?
            GROUP BY sale_date
            ORDER BY sale_date DESC
        """, (from_d, to_d)).fetchall()
        conn.close()

        headers = [("Date", 1), ("Invoices", 1), ("Cash", 1.2), ("Card", 1.2), ("UPI", 1.2), ("Credit", 1.2), ("Total", 1.2)]
        display = []
        grand_total = 0
        for r in rows:
            display.append([r["sale_date"], str(r["invoices"]), curr(r["cash"]), curr(r["card"]), curr(r["upi"]), curr(r["credit"]), curr(r["total_sales"])])
            grand_total += r["total_sales"]

        expenses = Expense.total_by_date_range(from_d, to_d) if "Expense" in dir() else 0
        # Re-fetch expenses
        conn2 = get_connection()
        exp_row = conn2.execute(
            "SELECT COALESCE(SUM(amount),0) as t FROM expenses WHERE expense_date BETWEEN ? AND ?",
            (from_d, to_d),
        ).fetchone()
        expenses = exp_row["t"]
        conn2.close()
        summary = f"Total Sales: {curr(grand_total)}  |  Expenses: {curr(expenses)}  |  Net: {curr(grand_total - expenses)}"
        self._display_results(headers, display, summary)

    def _profit_loss(self, from_d, to_d):
        conn = get_connection()
        sales = conn.execute(
            "SELECT COALESCE(SUM(grand_total),0) as t FROM sales WHERE sale_date BETWEEN ? AND ?",
            (from_d, to_d),
        ).fetchone()["t"]
        expenses = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as t FROM expenses WHERE expense_date BETWEEN ? AND ?",
            (from_d, to_d),
        ).fetchone()["t"]
        payroll = conn.execute(
            "SELECT COALESCE(SUM(net_salary),0) as t FROM payroll WHERE paid_date BETWEEN ? AND ?",
            (from_d, to_d),
        ).fetchone()["t"]
        conn.close()
        profit = sales - expenses - payroll

        headers = [("Metric", 2), ("Amount", 1.5)]
        display = [
            ("Total Sales", curr(sales)),
            ("Total Expenses", curr(expenses)),
            ("Payroll Paid", curr(payroll)),
            ("Net Profit/Loss", curr(profit)),
            ("Margin %", f"{(profit / sales * 100) if sales > 0 else 0:.2f}%"),
        ]
        self._display_results(headers, display, f"Period: {from_d} to {to_d}")

    def _sales_report(self, from_d, to_d):
        conn = get_connection()
        rows = conn.execute("""
            SELECT s.invoice_no, s.sale_date, s.payment_mode, s.grand_total,
                   COALESCE(c.name, 'Walk-in') as customer_name
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            WHERE s.sale_date BETWEEN ? AND ?
            ORDER BY s.sale_date DESC
        """, (from_d, to_d)).fetchall()
        conn.close()

        headers = [("Invoice", 0.8), ("Date", 0.8), ("Customer", 1), ("Payment", 0.7), ("Total", 0.8)]
        display = []
        total = 0
        for r in rows:
            display.append([r["invoice_no"], r["sale_date"], r["customer_name"], r["payment_mode"], curr(r["grand_total"])])
            total += r["grand_total"]
        self._display_results(headers, display, f"Total Sales: {curr(total)}  |  Invoices: {len(rows)}")

    def _stock_report(self):
        conn = get_connection()
        tanks = conn.execute("""
            SELECT t.name, f.name as fuel, t.capacity, t.current_level
            FROM tanks t
            JOIN fuel_types f ON f.id = t.fuel_type_id
        """).fetchall()
        lubes = conn.execute("""
            SELECT brand, product_name, unit, stock_qty
            FROM lube_products
            ORDER BY brand
        """).fetchall()
        conn.close()

        headers = [("Item", 1.8), ("Type", 0.8), ("Stock", 1), ("Status", 0.6)]
        display = []

        display.append(["-- FUEL TANKS --", "", "", ""])
        for t in tanks:
            pct = (t["current_level"] / t["capacity"] * 100) if t["capacity"] > 0 else 0
            status = "OK" if pct > 25 else "LOW"
            display.append([
                t["name"], t["fuel"],
                f"{t['current_level']:,.0f} / {t['capacity']:,.0f} L",
                status,
            ])

        display.append(["-- LUBRICANTS --", "", "", ""])
        for l in lubes:
            status = "OK" if l["stock_qty"] > 0 else "OUT"
            display.append([
                f"{l['brand']} - {l['product_name']}", l["unit"],
                f"{l['stock_qty']:,.2f}", status,
            ])

        self._display_results(headers, display, "Stock status overview")

    def _expense_report(self, from_d, to_d):
        conn = get_connection()
        rows = conn.execute("""
            SELECT e.expense_date, c.name as category, e.amount, e.description
            FROM expenses e
            JOIN expense_categories c ON c.id = e.category_id
            WHERE e.expense_date BETWEEN ? AND ?
            ORDER BY e.expense_date DESC
        """, (from_d, to_d)).fetchall()
        conn.close()

        headers = [("Date", 0.8), ("Category", 1), ("Amount", 0.8), ("Description", 1.5)]
        display = []
        total = 0
        for r in rows:
            display.append([r["expense_date"], r["category"], curr(r["amount"]), r.get("description", "")])
            total += r["amount"]
        self._display_results(headers, display, f"Total Expenses: {curr(total)}")

    def _payroll_report(self):
        month = datetime.now().month
        year = datetime.now().year
        conn = get_connection()
        rows = conn.execute("""
            SELECT e.name as employee_name, e.role, p.working_days,
                   p.gross_salary, p.net_salary, p.paid
            FROM payroll p
            JOIN employees e ON e.id = p.employee_id
            WHERE p.month=? AND p.year=?
            ORDER BY e.name
        """, (month, year)).fetchall()
        conn.close()

        headers = [("Employee", 1.2), ("Role", 0.8), ("Days", 0.5), ("Gross", 1), ("Net", 1), ("Status", 0.6)]
        display = []
        total_gross = 0
        total_net = 0
        for r in rows:
            status = "Paid" if r["paid"] else "Pending"
            display.append([r["employee_name"], r["role"], str(r["working_days"]), curr(r["gross_salary"]), curr(r["net_salary"]), status])
            total_gross += r["gross_salary"]
            total_net += r["net_salary"]
        self._display_results(headers, display, f"Period: {month}/{year}  |  Gross: {curr(total_gross)}  |  Net: {curr(total_net)}")

    def export_excel(self):
        if not self._current_rows:
            self._show_error("Generate a report first.")
            return

        try:
            from openpyxl import Workbook
            from libs.utils.paths import docs_dir
        except ImportError:
            self._show_error("openpyxl not available for export.")
            return

        report_type = self.ids.report_spinner.text
        filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = docs_dir() / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        wb = Workbook()
        ws = wb.active
        ws.title = report_type

        container = self.ids.result_container
        for child in container.children:
            if isinstance(child, BoxLayout):
                row_data = []
                for c in child.children:
                    if isinstance(c, Label):
                        row_data.append(c.text)
                if row_data:
                    ws.append(row_data)
            break

        for row in self._current_rows:
            ws.append(list(row))

        wb.save(str(filepath))
        self._show_info("Exported", f"Report saved to:\n{filename}")

    def export_csv(self):
        if not self._current_rows:
            self._show_error("Generate a report first.")
            return

        import csv
        from libs.utils.paths import docs_dir

        report_type = self.ids.report_spinner.text
        filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = docs_dir() / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(str(filepath), "w", newline="") as f:
            writer = csv.writer(f)
            container = self.ids.result_container
            for child in container.children:
                if isinstance(child, BoxLayout):
                    header = [c.text for c in child.children if isinstance(c, Label)]
                    if header:
                        writer.writerow(header)
                break
            for row in self._current_rows:
                writer.writerow(list(row))

        self._show_info("Exported", f"CSV saved to:\n{filename}")

    def _show_error(self, msg):
        popup = Popup(
            title="Error",
            content=Label(text=msg, color=TEXT_ERROR),
            size_hint=(0.7, 0.3),
        )
        popup.open()

    def _show_info(self, title, msg):
        popup = Popup(
            title=title,
            content=Label(text=msg, color=TEXT_PRIMARY),
            size_hint=(0.8, 0.4),
        )
        popup.open()

    def go_back(self):
        self.manager.current = "main"
