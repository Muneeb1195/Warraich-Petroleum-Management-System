from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QComboBox, QSpinBox, QMessageBox, QHeaderView,
                               QGroupBox, QFormLayout)
from PySide6.QtCore import Qt
from database.connection import get_connection
from models.employee import Employee
from models.payroll import Payroll
from database.settings import settings
from datetime import datetime
from utils.formatting import curr, CURRENCY_SYMBOL_RAW



class PayrollWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Payroll Management")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Month:"))
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(datetime.now().month)
        controls.addWidget(self.month_spin)

        controls.addWidget(QLabel("Year:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2050)
        self.year_spin.setValue(datetime.now().year)
        controls.addWidget(self.year_spin)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        controls.addWidget(refresh_btn)

        generate_all_btn = QPushButton("Generate All")
        generate_all_btn.setObjectName("successBtn")
        generate_all_btn.clicked.connect(self._generate_all)
        controls.addWidget(generate_all_btn)

        controls.addStretch()
        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Employee", "Role", "Type", "Work Days", "Gross", "Net", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        pay_selected_btn = QPushButton("Mark Selected as Paid")
        pay_selected_btn.clicked.connect(self._pay_selected)
        btn_layout.addWidget(pay_selected_btn)

        pay_all_btn = QPushButton("Mark All as Paid")
        pay_all_btn.setObjectName("successBtn")
        pay_all_btn.clicked.connect(self._pay_all)
        btn_layout.addWidget(pay_all_btn)

        payslip_btn = QPushButton("Generate Payslip PDF")
        payslip_btn.clicked.connect(self._payslip)
        btn_layout.addWidget(payslip_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.refresh()

    def refresh(self):
        month = self.month_spin.value()
        year = self.year_spin.value()
        records = Payroll.get_by_month(month, year)
        self.table.setRowCount(len(records))
        for i, r in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(r["employee_name"]))
            self.table.setItem(i, 1, QTableWidgetItem(r["role"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["salary_type"]))
            self.table.setItem(i, 3, QTableWidgetItem(str(r["working_days"])))
            self.table.setItem(i, 4, QTableWidgetItem(f"{curr(r['gross_salary'])}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{curr(r['net_salary'])}"))
            status = "✅ Paid" if r["paid"] else "⏳ Pending"
            self.table.setItem(i, 6, QTableWidgetItem(status))

    def _generate_all(self):
        month = self.month_spin.value()
        year = self.year_spin.value()
        employees = Employee.get_active()
        count = 0
        for emp in employees:
            Payroll.calculate(emp["id"], month, year)
            count += 1
        QMessageBox.information(self, "Done", f"Payroll generated for {count} employees.")
        self.refresh()

    def _pay_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a row first.")
            return
        row = selected[0].row()
        month = self.month_spin.value()
        year = self.year_spin.value()
        records = Payroll.get_by_month(month, year)
        if row < len(records):
            Payroll.mark_paid(records[row]["id"])
            self.refresh()

    def _pay_all(self):
        month = self.month_spin.value()
        year = self.year_spin.value()
        records = Payroll.get_by_month(month, year)
        for r in records:
            if not r["paid"]:
                Payroll.mark_paid(r["id"])
        QMessageBox.information(self, "Done", "All pending payroll marked as paid.")
        self.refresh()

    def _payslip(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Error", "Select an employee row first.")
            return
        row = selected[0].row()
        month = self.month_spin.value()
        year = self.year_spin.value()
        records = Payroll.get_by_month(month, year)
        if row >= len(records):
            return
        record = records[row]
        emp = Employee.get_by_id(record["employee_id"])
        if not emp:
            return
        self._generate_payslip_pdf(emp, record)
        QMessageBox.information(self, "Success",
                                f"Payslip saved to reports/payslip_{emp['name']}_{month}_{year}.pdf")

    def _generate_payslip_pdf(self, emp, record):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from pathlib import Path

        filename = f"reports/payslip_{emp['name']}_{record['month']}_{record['year']}.pdf"
        filepath = Path(__file__).resolve().parent.parent.parent / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(filepath), pagesize=A4)
        width, height = A4

        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, settings.business_name())
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"GSTIN: {settings.gstin()}")
        c.drawString(50, height - 85, f"Address: {settings.business_address()}")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 115, "PAYSLIP")
        c.line(50, height - 120, width - 50, height - 120)

        y = height - 145
        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"Employee: {emp['name']}")
        c.drawString(300, y, f"Role: {emp['role']}")
        y -= 20
        c.drawString(50, y, f"Month: {record['month']}/{record['year']}")
        c.drawString(300, y, f"Working Days: {record['working_days']}")

        y -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Earnings")
        c.line(50, y - 5, width - 50, y - 5)

        c.setFont("Helvetica", 12)
        y -= 25
        c.drawString(50, y, "Gross Salary:")
        c.drawRightString(width - 50, y, f"{curr(record['gross_salary'])}")

        y -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Deductions")
        c.line(50, y - 5, width - 50, y - 5)

        c.setFont("Helvetica", 12)
        y -= 25
        c.drawString(50, y, "Total Deductions:")
        c.drawRightString(width - 50, y, f"{curr(record['deductions'])}")

        y -= 40
        c.line(50, y, width - 50, y)
        c.setFont("Helvetica-Bold", 14)
        y -= 25
        c.drawString(50, y, "NET SALARY:")
        c.drawRightString(width - 50, y, f"{curr(record['net_salary'])}")
        c.setFont("Helvetica", 10)
        y -= 30
        c.drawString(50, y, f"Amount in words: Rupees {self._number_to_words(int(record['net_salary']))} only")

        if record["paid"]:
            y -= 30
            c.setFont("Helvetica", 10)
            c.drawString(50, y, f"Paid on: {record['paid_date']}")

        c.save()

    def _number_to_words(self, n):
        if n == 0:
            return "Zero"
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        if n < 20:
            return ones[n]
        if n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
        if n < 1000:
            return ones[n // 100] + " Hundred" + (" " + self._number_to_words(n % 100) if n % 100 else "")
        if n < 100000:
            return self._number_to_words(n // 1000) + " Thousand" + (" " + self._number_to_words(n % 1000) if n % 1000 else "")
        if n < 10000000:
            return self._number_to_words(n // 100000) + " Lakh" + (" " + self._number_to_words(n % 100000) if n % 100000 else "")
        return self._number_to_words(n // 10000000) + " Crore" + (" " + self._number_to_words(n % 10000000) if n % 10000000 else "")
