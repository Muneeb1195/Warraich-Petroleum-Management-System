from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
                               QMessageBox, QHeaderView)
from models.customer import Customer
from database.connection import get_connection
from utils.formatting import curr, CURRENCY_SYMBOL_RAW



class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("Add Customer" if not customer else "Edit Customer")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.gstin_edit = QLineEdit()
        self.credit_limit = QDoubleSpinBox()
        self.credit_limit.setRange(0, 999999)
        self.credit_limit.setDecimals(2)

        layout.addRow("Name:", self.name_edit)
        layout.addRow("Phone:", self.phone_edit)
        layout.addRow("Address:", self.address_edit)
        layout.addRow("GSTIN:", self.gstin_edit)
        layout.addRow("Credit Limit:", self.credit_limit)

        if customer:
            self.name_edit.setText(customer["name"])
            self.phone_edit.setText(customer["phone"])
            self.address_edit.setText(customer["address"])
            self.gstin_edit.setText(customer["gstin"])
            self.credit_limit.setValue(customer["credit_limit"])

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _save(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Error", "Customer name is required.")
            return
        if self.customer:
            from database.connection import get_connection
            conn = get_connection()
            conn.execute(
                "UPDATE customers SET name=?, phone=?, address=?, gstin=?, credit_limit=? WHERE id=?",
                (self.name_edit.text(), self.phone_edit.text(), self.address_edit.text(),
                 self.gstin_edit.text(), self.credit_limit.value(), self.customer["id"]),
            )
            conn.commit()
            conn.close()
        else:
            Customer.create(self.name_edit.text(), self.phone_edit.text(),
                            self.address_edit.text(), self.gstin_edit.text(),
                            self.credit_limit.value())
        self.accept()


class CustomerListWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("Customers")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        add_btn = QPushButton("+ Add Customer")
        add_btn.clicked.connect(self._add)
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Phone", "GSTIN", "Credit Limit", "Balance", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        customers = Customer.get_all("name")
        self.table.setRowCount(len(customers))
        for i, c in enumerate(customers):
            self.table.setItem(i, 0, QTableWidgetItem(c["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(c.get("phone", "")))
            self.table.setItem(i, 2, QTableWidgetItem(c.get("gstin", "")))
            self.table.setItem(i, 3, QTableWidgetItem(f"{curr(c['credit_limit'])}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{curr(c['balance'])}"))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(60)
            edit_btn.clicked.connect(lambda checked, cid=c["id"]: self._edit(cid))
            del_btn = QPushButton("Del")
            del_btn.setObjectName("dangerBtn")
            del_btn.setFixedWidth(60)
            del_btn.clicked.connect(lambda checked, cid=c["id"]: self._delete(cid))
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch()
            self.table.setCellWidget(i, 5, btn_widget)

    def _add(self):
        dlg = CustomerDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit(self, cid):
        c = Customer.get_by_id(cid)
        if c:
            dlg = CustomerDialog(self, c)
            if dlg.exec():
                self.refresh()

    def _delete(self, cid):
        reply = QMessageBox.question(self, "Confirm", "Delete this customer?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            Customer.delete(cid)
            self.refresh()
