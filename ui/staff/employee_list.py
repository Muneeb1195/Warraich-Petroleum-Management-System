from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
                               QComboBox, QMessageBox, QHeaderView)
from models.employee import Employee
from utils.formatting import curr, CURRENCY_SYMBOL_RAW



class EmployeeDialog(QDialog):
    def __init__(self, parent=None, employee=None):
        super().__init__(parent)
        self.employee = employee
        self.setWindowTitle("Add Employee" if not employee else "Edit Employee")
        self.setMinimumWidth(500)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setToolTip("Employee's full name (required)")
        self.role_combo = QComboBox()
        self.role_combo.setToolTip("Job role or position")
        self.role_combo.addItems(["Manager", "Cashier", "Attendant", "Supervisor", "Other"])
        self.phone_edit = QLineEdit()
        self.phone_edit.setToolTip("Contact phone number")
        self.address_edit = QLineEdit()
        self.address_edit.setToolTip("Residential address")
        self.bank_name_edit = QLineEdit()
        self.bank_name_edit.setToolTip("Bank name for salary transfer")
        self.bank_ac_edit = QLineEdit()
        self.bank_ac_edit.setToolTip("Bank account number")
        self.ifsc_edit = QLineEdit()
        self.ifsc_edit.setToolTip("Bank IFSC code for transfers")
        self.salary_type_combo = QComboBox()
        self.salary_type_combo.setToolTip("Fixed = monthly salary, Daily = paid per working day")
        self.salary_type_combo.addItems(["Fixed", "Daily"])
        self.salary_amount = QDoubleSpinBox()
        self.salary_amount.setRange(0, 999999)
        self.salary_amount.setDecimals(2)
        self.salary_amount.setToolTip("Monthly salary (Fixed) or daily wage (Daily)")

        layout.addRow("Name:", self.name_edit)
        layout.addRow("Role:", self.role_combo)
        layout.addRow("Phone:", self.phone_edit)
        layout.addRow("Address:", self.address_edit)
        layout.addRow("Bank Name:", self.bank_name_edit)
        layout.addRow("Bank Account:", self.bank_ac_edit)
        layout.addRow("IFSC Code:", self.ifsc_edit)
        layout.addRow("Salary Type:", self.salary_type_combo)
        layout.addRow("Salary Amount:", self.salary_amount)

        if employee:
            self.name_edit.setText(employee["name"])
            idx = self.role_combo.findText(employee["role"])
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)
            self.phone_edit.setText(employee.get("phone", ""))
            self.address_edit.setText(employee.get("address", ""))
            self.bank_name_edit.setText(employee.get("bank_name", ""))
            self.bank_ac_edit.setText(employee.get("bank_account", ""))
            self.ifsc_edit.setText(employee.get("ifsc_code", ""))
            idx2 = self.salary_type_combo.findText(employee["salary_type"])
            if idx2 >= 0:
                self.salary_type_combo.setCurrentIndex(idx2)
            self.salary_amount.setValue(employee["salary_amount"])

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save this employee record")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setToolTip("Discard changes and go back")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _save(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Error", "Employee name is required.")
            return
        if self.employee:
            Employee.update(self.employee["id"],
                            name=self.name_edit.text(),
                            role=self.role_combo.currentText(),
                            phone=self.phone_edit.text(),
                            address=self.address_edit.text(),
                            bank_name=self.bank_name_edit.text(),
                            bank_account=self.bank_ac_edit.text(),
                            ifsc_code=self.ifsc_edit.text(),
                            salary_type=self.salary_type_combo.currentText(),
                            salary_amount=self.salary_amount.value())
        else:
            Employee.create(self.name_edit.text(), self.role_combo.currentText(),
                            self.phone_edit.text(), self.address_edit.text(),
                            self.bank_name_edit.text(), self.bank_ac_edit.text(),
                            self.ifsc_edit.text(), self.salary_type_combo.currentText(),
                            self.salary_amount.value())
        self.accept()


class EmployeeListWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("Employees")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        add_btn = QPushButton("+ Add Employee")
        add_btn.setToolTip("Add a new staff member")
        add_btn.clicked.connect(self._add)
        header.addWidget(add_btn)
        layout.addLayout(header)

        subtitle = QLabel("Manage staff information and employment details")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px; padding: 0 0 12px 0;")
        layout.addWidget(subtitle)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search employees...")
        self.search_bar.textChanged.connect(self._filter)
        layout.addWidget(self.search_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Role", "Phone", "Salary Type", f"Salary ({CURRENCY_SYMBOL_RAW})", "Active", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        employees = Employee.get_all("name")
        self.table.setRowCount(len(employees))
        for i, e in enumerate(employees):
            self.table.setItem(i, 0, QTableWidgetItem(e["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(e["role"]))
            self.table.setItem(i, 2, QTableWidgetItem(e.get("phone", "")))
            self.table.setItem(i, 3, QTableWidgetItem(e["salary_type"]))
            self.table.setItem(i, 4, QTableWidgetItem(f"{curr(e['salary_amount'])}"))
            self.table.setItem(i, 5, QTableWidgetItem("✅" if e["is_active"] else "❌"))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            edit_btn = QPushButton("Edit")
            edit_btn.setToolTip("Edit this employee's details")
            edit_btn.setFixedWidth(60)
            edit_btn.clicked.connect(lambda checked, eid=e["id"]: self._edit(eid))
            toggle_btn = QPushButton("Deactivate" if e["is_active"] else "Activate")
            toggle_btn.setToolTip("Enable or disable this employee's access")
            toggle_btn.setFixedWidth(80)
            toggle_btn.clicked.connect(lambda checked, eid=e["id"], st=e["is_active"]: self._toggle(eid, st))
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(toggle_btn)
            btn_layout.addStretch()
            self.table.setCellWidget(i, 6, btn_widget)

    def _add(self):
        dlg = EmployeeDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit(self, eid):
        emp = Employee.get_by_id(eid)
        if emp:
            dlg = EmployeeDialog(self, emp)
            if dlg.exec():
                self.refresh()

    def _toggle(self, eid, current_status):
        Employee.update(eid, is_active=0 if current_status else 1)
        self.refresh()

    def _filter(self, text):
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
