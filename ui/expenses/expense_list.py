from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
                               QComboBox, QMessageBox, QHeaderView, QDateEdit)
from PySide6.QtCore import QDate
from models.expense import Expense, ExpenseCategory
from database.connection import get_connection
from utils.formatting import curr, CURRENCY_SYMBOL_RAW



class ExpenseDialog(QDialog):
    def __init__(self, parent=None, expense=None):
        super().__init__(parent)
        self.expense = expense
        self.setWindowTitle("Add Expense" if not expense else "Edit Expense")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self.category_combo = QComboBox()
        categories = ExpenseCategory.get_all("name")
        for cat in categories:
            self.category_combo.addItem(cat["name"], cat["id"])
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999)
        self.amount_spin.setDecimals(2)
        self.desc_edit = QLineEdit()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)

        layout.addRow("Category:", self.category_combo)
        layout.addRow("Amount:", self.amount_spin)
        layout.addRow("Description:", self.desc_edit)
        layout.addRow("Date:", self.date_edit)

        if expense:
            idx = self.category_combo.findData(expense["category_id"])
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            self.amount_spin.setValue(expense["amount"])
            self.desc_edit.setText(expense.get("description", ""))
            self.date_edit.setDate(QDate.fromString(expense["expense_date"], "yyyy-MM-dd"))

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
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Error", "Amount must be > 0.")
            return
        if self.expense:
            conn = get_connection()
            conn.execute(
                "UPDATE expenses SET category_id=?, amount=?, description=?, expense_date=? WHERE id=?",
                (self.category_combo.currentData(), self.amount_spin.value(),
                 self.desc_edit.text(), self.date_edit.date().toString("yyyy-MM-dd"),
                 self.expense["id"]),
            )
            conn.commit()
            conn.close()
        else:
            Expense.create(self.category_combo.currentData(), self.amount_spin.value(),
                           self.desc_edit.text(),
                           self.date_edit.date().toString("yyyy-MM-dd"))
        self.accept()


class ExpenseListWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("Expenses")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        add_btn = QPushButton("+ Add Expense")
        add_btn.clicked.connect(self._add)
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Category", "Amount", "Description", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        expenses = Expense.get_with_category()
        self.table.setRowCount(len(expenses))
        for i, e in enumerate(expenses):
            self.table.setItem(i, 0, QTableWidgetItem(e["expense_date"]))
            self.table.setItem(i, 1, QTableWidgetItem(e["category_name"]))
            self.table.setItem(i, 2, QTableWidgetItem(f"{curr(e['amount'])}"))
            self.table.setItem(i, 3, QTableWidgetItem(e.get("description", "")))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(60)
            edit_btn.clicked.connect(lambda checked, eid=e["id"]: self._edit(eid))
            del_btn = QPushButton("Del")
            del_btn.setObjectName("dangerBtn")
            del_btn.setFixedWidth(60)
            del_btn.clicked.connect(lambda checked, eid=e["id"]: self._delete(eid))
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch()
            self.table.setCellWidget(i, 4, btn_widget)

    def _add(self):
        dlg = ExpenseDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit(self, eid):
        e = Expense.get_by_id(eid)
        if e:
            dlg = ExpenseDialog(self, e)
            if dlg.exec():
                self.refresh()

    def _delete(self, eid):
        reply = QMessageBox.question(self, "Confirm", "Delete this expense?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            Expense.delete(eid)
            self.refresh()
