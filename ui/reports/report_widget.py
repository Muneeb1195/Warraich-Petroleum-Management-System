from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QComboBox, QDateEdit, QMessageBox, QHeaderView,
                               QGroupBox, QFormLayout, QSpinBox, QTextEdit)
from PySide6.QtCore import QDate, Qt
from database.connection import get_connection
from database.settings import settings
from models.sale import Sale
from models.expense import Expense
from models.payroll import Payroll
from datetime import datetime, timedelta
from utils.formatting import curr, CURRENCY_SYMBOL_RAW



class ReportWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Reports")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("View business summaries and export data to Excel")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px; padding: 0 0 12px 0;")
        layout.addWidget(subtitle)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("From:"))
        self.from_date = QDateEdit(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        self.from_date.setToolTip("Start date for the report range")
        controls.addWidget(self.from_date)

        controls.addWidget(QLabel("To:"))
        self.to_date = QDateEdit(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setToolTip("End date for the report range")
        controls.addWidget(self.to_date)

        self.report_combo = QComboBox()
        self.report_combo.setToolTip("Select the type of report to generate")
        self.report_combo.addItems([
            "Daily Summary",
            "Profit & Loss",
            "Sales Report",
            "Stock Report",
            "Expense Report",
            "Payroll Report",
        ])
        controls.addWidget(QLabel("Report:"))
        controls.addWidget(self.report_combo)

        generate_btn = QPushButton("Generate")
        generate_btn.setToolTip("Generate the selected report")
        generate_btn.clicked.connect(self._generate)
        controls.addWidget(generate_btn)

        export_btn = QPushButton("Export Excel")
        export_btn.setObjectName("successBtn")
        export_btn.setToolTip("Export the current report to an Excel file")
        export_btn.clicked.connect(self._export_excel)
        controls.addWidget(export_btn)

        controls.addStretch()
        layout.addLayout(controls)

        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        layout.addWidget(self.summary_label)

    def _generate(self):
        report_type = self.report_combo.currentText()
        from_d = self.from_date.date().toString("yyyy-MM-dd")
        to_d = self.to_date.date().toString("yyyy-MM-dd")

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

        self.result_table.setColumnCount(7)
        self.result_table.setHorizontalHeaderLabels(
            ["Date", "Invoices", "Cash", "Card", "UPI", "Credit", "Total"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setRowCount(len(rows))

        grand_total = 0
        for i, r in enumerate(rows):
            self.result_table.setItem(i, 0, QTableWidgetItem(r["sale_date"]))
            self.result_table.setItem(i, 1, QTableWidgetItem(str(r["invoices"])))
            self.result_table.setItem(i, 2, QTableWidgetItem(f"{curr(r['cash'])}"))
            self.result_table.setItem(i, 3, QTableWidgetItem(f"{curr(r['card'])}"))
            self.result_table.setItem(i, 4, QTableWidgetItem(f"{curr(r['upi'])}"))
            self.result_table.setItem(i, 5, QTableWidgetItem(f"{curr(r['credit'])}"))
            self.result_table.setItem(i, 6, QTableWidgetItem(f"{curr(r['total_sales'])}"))
            grand_total += r["total_sales"]

        expenses = Expense.total_by_date_range(from_d, to_d)
        self.summary_label.setText(
            f"Total Sales: {curr(grand_total)}  |  Total Expenses: {curr(expenses)}  |  "
            f"Net: {curr(grand_total - expenses)}")
        conn.close()

    def _profit_loss(self, from_d, to_d):
        conn = get_connection()
        sales = conn.execute(
            "SELECT COALESCE(SUM(grand_total),0) as t FROM sales WHERE sale_date BETWEEN ? AND ?",
            (from_d, to_d)).fetchone()["t"]
        expenses = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as t FROM expenses WHERE expense_date BETWEEN ? AND ?",
            (from_d, to_d)).fetchone()["t"]
        payroll = conn.execute(
            "SELECT COALESCE(SUM(net_salary),0) as t FROM payroll WHERE paid_date BETWEEN ? AND ?",
            (from_d, to_d)).fetchone()["t"]
        profit = sales - expenses - payroll
        conn.close()

        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["Metric", "Amount"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setRowCount(5)
        items = [
            ("Total Sales", f"{curr(sales)}"),
            ("Total Expenses", f"{curr(expenses)}"),
            ("Payroll Paid", f"{curr(payroll)}"),
            ("Net Profit/Loss", f"{curr(profit)}"),
            ("Margin %", f"{(profit / sales * 100) if sales > 0 else 0:.2f}%"),
        ]
        for i, (k, v) in enumerate(items):
            self.result_table.setItem(i, 0, QTableWidgetItem(k))
            self.result_table.setItem(i, 1, QTableWidgetItem(v))
        self.summary_label.setText(f"Period: {from_d} to {to_d}")

    def _sales_report(self, from_d, to_d):
        conn = get_connection()
        rows = conn.execute("""
            SELECT s.invoice_no, s.sale_date, s.payment_mode, s.grand_total,
                   c.name as customer_name
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            WHERE s.sale_date BETWEEN ? AND ?
            ORDER BY s.sale_date DESC
        """, (from_d, to_d)).fetchall()

        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(
            ["Invoice", "Date", "Customer", "Payment", "Total"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setRowCount(len(rows))

        total = 0
        for i, r in enumerate(rows):
            self.result_table.setItem(i, 0, QTableWidgetItem(r["invoice_no"]))
            self.result_table.setItem(i, 1, QTableWidgetItem(r["sale_date"]))
            self.result_table.setItem(i, 2, QTableWidgetItem(r.get("customer_name", "Walk-in")))
            self.result_table.setItem(i, 3, QTableWidgetItem(r["payment_mode"]))
            self.result_table.setItem(i, 4, QTableWidgetItem(f"{curr(r['grand_total'])}"))
            total += r["grand_total"]
        self.summary_label.setText(f"Total Sales: {curr(total)} | Invoices: {len(rows)}")
        conn.close()

    def _stock_report(self):
        conn = get_connection()
        tanks = conn.execute("""
            SELECT t.name, f.name as fuel, t.capacity, t.current_level,
                   (t.capacity - t.current_level) as space
            FROM tanks t
            JOIN fuel_types f ON f.id = t.fuel_type_id
        """).fetchall()
        lubes = conn.execute("""
            SELECT brand, product_name, unit, stock_qty
            FROM lube_products
            ORDER BY brand
        """).fetchall()

        total_rows = len(tanks) + len(lubes) + 2
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["Item", "Type", "Unit", "Stock", "Status"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setRowCount(total_rows)

        i = 0
        self.result_table.setItem(i, 0, QTableWidgetItem("-- FUEL TANKS --"))
        self.result_table.setItem(i, 1, QTableWidgetItem(""))
        self.result_table.setItem(i, 2, QTableWidgetItem(""))
        self.result_table.setItem(i, 3, QTableWidgetItem(""))
        self.result_table.setItem(i, 4, QTableWidgetItem(""))
        i += 1

        for t in tanks:
            self.result_table.setItem(i, 0, QTableWidgetItem(t["name"]))
            self.result_table.setItem(i, 1, QTableWidgetItem(t["fuel"]))
            self.result_table.setItem(i, 2, QTableWidgetItem("Litre"))
            self.result_table.setItem(i, 3, QTableWidgetItem(f"{t['current_level']:,.2f} / {t['capacity']:,.2f}"))
            pct = (t["current_level"] / t["capacity"] * 100) if t["capacity"] > 0 else 0
            status = "🟢" if pct > 25 else "🔴"
            self.result_table.setItem(i, 4, QTableWidgetItem(status))
            i += 1

        self.result_table.setItem(i, 0, QTableWidgetItem("-- LUBRICANTS --"))
        i += 1
        for l in lubes:
            self.result_table.setItem(i, 0, QTableWidgetItem(f"{l['brand']} - {l['product_name']}"))
            self.result_table.setItem(i, 1, QTableWidgetItem("Lube"))
            self.result_table.setItem(i, 2, QTableWidgetItem(l["unit"]))
            self.result_table.setItem(i, 3, QTableWidgetItem(f"{l['stock_qty']:,.2f}"))
            status = "🟢" if l["stock_qty"] > 0 else "🔴"
            self.result_table.setItem(i, 4, QTableWidgetItem(status))
            i += 1

        self.summary_label.setText("Stock status overview")
        conn.close()

    def _expense_report(self, from_d, to_d):
        conn = get_connection()
        rows = conn.execute("""
            SELECT e.expense_date, c.name as category, e.amount, e.description
            FROM expenses e
            JOIN expense_categories c ON c.id = e.category_id
            WHERE e.expense_date BETWEEN ? AND ?
            ORDER BY e.expense_date DESC
        """, (from_d, to_d)).fetchall()

        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["Date", "Category", "Amount", "Description"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setRowCount(len(rows))

        total = 0
        for i, r in enumerate(rows):
            self.result_table.setItem(i, 0, QTableWidgetItem(r["expense_date"]))
            self.result_table.setItem(i, 1, QTableWidgetItem(r["category"]))
            self.result_table.setItem(i, 2, QTableWidgetItem(f"{curr(r['amount'])}"))
            self.result_table.setItem(i, 3, QTableWidgetItem(r.get("description", "")))
            total += r["amount"]
        self.summary_label.setText(f"Total Expenses: {curr(total)}")
        conn.close()

    def _payroll_report(self):
        month = datetime.now().month
        year = datetime.now().year
        records = Payroll.get_by_month(month, year)

        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels(
            ["Employee", "Role", "Days", "Gross", "Net", "Paid"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setRowCount(len(records))

        total_gross = 0
        total_net = 0
        for i, r in enumerate(records):
            self.result_table.setItem(i, 0, QTableWidgetItem(r["employee_name"]))
            self.result_table.setItem(i, 1, QTableWidgetItem(r["role"]))
            self.result_table.setItem(i, 2, QTableWidgetItem(str(r["working_days"])))
            self.result_table.setItem(i, 3, QTableWidgetItem(f"{curr(r['gross_salary'])}"))
            self.result_table.setItem(i, 4, QTableWidgetItem(f"{curr(r['net_salary'])}"))
            self.result_table.setItem(i, 5, QTableWidgetItem("✅" if r["paid"] else "❌"))
            total_gross += r["gross_salary"]
            total_net += r["net_salary"]
        self.summary_label.setText(
            f"Month: {month}/{year} | Total Gross: {curr(total_gross)} | Total Net: {curr(total_net)}")

    def _export_excel(self):
        from openpyxl import Workbook
        from utils.paths import docs_dir

        report_type = self.report_combo.currentText()
        filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = docs_dir() / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        wb = Workbook()
        ws = wb.active
        ws.title = report_type

        headers = [self.result_table.horizontalHeaderItem(i).text()
                   for i in range(self.result_table.columnCount())]
        ws.append(headers)

        for row in range(self.result_table.rowCount()):
            row_data = []
            for col in range(self.result_table.columnCount()):
                item = self.result_table.item(row, col)
                row_data.append(item.text() if item else "")
            ws.append(row_data)

        wb.save(str(filepath))
        QMessageBox.information(self, "Exported", f"Report saved to {filename}")

    def refresh(self):
        pass
