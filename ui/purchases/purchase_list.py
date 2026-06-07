from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
                               QComboBox, QMessageBox, QHeaderView, QDateEdit,
                               QTabWidget)
from PySide6.QtCore import QDate
from models.supplier import Supplier
from models.purchase import Purchase
from models.fuel import FuelType
from models.lube import LubeProduct
from database.connection import get_connection
from utils.formatting import curr, CURRENCY_SYMBOL_RAW



class SupplierDialog(QDialog):
    def __init__(self, parent=None, supplier=None):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle("Add Supplier" if not supplier else "Edit Supplier")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.gstin_edit = QLineEdit()

        layout.addRow("Name:", self.name_edit)
        layout.addRow("Phone:", self.phone_edit)
        layout.addRow("Address:", self.address_edit)
        layout.addRow("GSTIN:", self.gstin_edit)

        if supplier:
            self.name_edit.setText(supplier["name"])
            self.phone_edit.setText(supplier["phone"])
            self.address_edit.setText(supplier["address"])
            self.gstin_edit.setText(supplier["gstin"])

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
            QMessageBox.warning(self, "Error", "Supplier name is required.")
            return
        if self.supplier:
            Supplier.update(self.supplier["id"], name=self.name_edit.text(),
                            phone=self.phone_edit.text(), address=self.address_edit.text(),
                            gstin=self.gstin_edit.text())
        else:
            Supplier.create(self.name_edit.text(), self.phone_edit.text(),
                            self.address_edit.text(), self.gstin_edit.text())
        self.accept()


class PurchaseDialog(QDialog):
    def __init__(self, parent=None, purchase_id=None):
        super().__init__(parent)
        self.purchase_id = purchase_id
        self.items = []
        self.setWindowTitle("New Purchase" if not purchase_id else "View Purchase")
        self.setMinimumSize(600, 500)
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.supplier_combo = QComboBox()
        suppliers = Supplier.get_all("name")
        for s in suppliers:
            self.supplier_combo.addItem(s["name"], s["id"])
        self.invoice_edit = QLineEdit()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("Supplier:", self.supplier_combo)
        form_layout.addRow("Invoice No:", self.invoice_edit)
        form_layout.addRow("Date:", self.date_edit)
        layout.addLayout(form_layout)

        item_header = QHBoxLayout()
        item_label = QLabel("Items")
        item_label.setStyleSheet("font-weight: bold;")
        item_header.addWidget(item_label)
        item_header.addStretch()

        self.item_type_combo = QComboBox()
        self.item_type_combo.addItems(["Fuel", "Lube"])
        self.item_type_combo.currentTextChanged.connect(self._update_item_fields)
        item_header.addWidget(QLabel("Type:"))
        item_header.addWidget(self.item_type_combo)

        self.item_select_combo = QComboBox()
        self.item_select_combo.setMinimumWidth(200)
        item_header.addWidget(self.item_select_combo)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0, 999999)
        self.qty_spin.setDecimals(2)
        item_header.addWidget(QLabel("Qty:"))
        item_header.addWidget(self.qty_spin)

        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0, 999999)
        self.rate_spin.setDecimals(2)
        item_header.addWidget(QLabel("Rate:"))
        item_header.addWidget(self.rate_spin)

        add_item_btn = QPushButton("+ Add")
        add_item_btn.clicked.connect(self._add_item)
        item_header.addWidget(add_item_btn)

        layout.addLayout(item_header)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Item", "Qty", "Rate", "Amount", "Action"])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.items_table)

        self.total_label = QLabel(f"Total: {curr(0)}")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
        layout.addWidget(self.total_label)

        btn_layout = QHBoxLayout()
        if not purchase_id:
            save_btn = QPushButton("Save Purchase")
            save_btn.clicked.connect(self._save)
            btn_layout.addStretch()
            btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("Close")
        cancel_btn.clicked.connect(self.accept)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self._update_item_fields()

    def _update_item_fields(self):
        self.item_select_combo.clear()
        if self.item_type_combo.currentText() == "Fuel":
            fuels = FuelType.get_all()
            for f in fuels:
                self.item_select_combo.addItem(f["name"], ("fuel", f["id"]))
        else:
            lubes = LubeProduct.get_all("brand")
            for l in lubes:
                self.item_select_combo.addItem(f"{l['brand']} - {l['product_name']}", ("lube", l["id"]))

    def _add_item(self):
        item_type, item_id = self.item_select_combo.currentData()
        name = self.item_select_combo.currentText()
        qty = self.qty_spin.value()
        rate = self.rate_spin.value()
        if qty <= 0 or rate <= 0:
            QMessageBox.warning(self, "Error", "Qty and Rate must be > 0")
            return
        amount = qty * rate
        self.items.append({"type": item_type, "id": item_id, "name": name, "qty": qty, "rate": rate, "amount": amount})
        self._refresh_items_table()

    def _refresh_items_table(self):
        self.items_table.setRowCount(len(self.items))
        total = 0
        for i, it in enumerate(self.items):
            self.items_table.setItem(i, 0, QTableWidgetItem(it["name"]))
            self.items_table.setItem(i, 1, QTableWidgetItem(f"{it['qty']:,.2f}"))
            self.items_table.setItem(i, 2, QTableWidgetItem(f"{curr(it['rate'])}"))
            self.items_table.setItem(i, 3, QTableWidgetItem(f"{curr(it['amount'])}"))
            total += it["amount"]
            del_btn = QPushButton("X")
            del_btn.setObjectName("dangerBtn")
            del_btn.setFixedWidth(40)
            del_btn.clicked.connect(lambda checked, idx=i: self._remove_item(idx))
            self.items_table.setCellWidget(i, 4, del_btn)
        self.total_label.setText(f"Total: {curr(total)}")

    def _remove_item(self, idx):
        if 0 <= idx < len(self.items):
            self.items.pop(idx)
            self._refresh_items_table()

    def _save(self):
        if not self.items:
            QMessageBox.warning(self, "Error", "Add at least one item.")
            return
        purchase_id = Purchase.create(
            self.supplier_combo.currentData(),
            self.invoice_edit.text(),
            purchase_date=self.date_edit.date().toString("yyyy-MM-dd"),
        )
        for it in self.items:
            if it["type"] == "fuel":
                Purchase.add_item(purchase_id, "fuel", fuel_type_id=it["id"], qty=it["qty"], rate=it["rate"])
                from models.lube import LubeProduct
            else:
                Purchase.add_item(purchase_id, "lube", lube_product_id=it["id"], qty=it["qty"], rate=it["rate"])
                LubeProduct.adjust_stock(it["id"], it["qty"])
        Purchase.update_total(purchase_id)
        QMessageBox.information(self, "Success", f"Purchase saved (ID: {purchase_id})")
        self.accept()


class PurchaseListWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("Purchases")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        add_btn = QPushButton("+ New Purchase")
        add_btn.clicked.connect(self._add)
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Supplier", "Invoice", "Total", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        purchases = Purchase.get_all_with_supplier()
        self.table.setRowCount(len(purchases))
        for i, p in enumerate(purchases):
            self.table.setItem(i, 0, QTableWidgetItem(p["purchase_date"]))
            self.table.setItem(i, 1, QTableWidgetItem(p["supplier_name"]))
            self.table.setItem(i, 2, QTableWidgetItem(p.get("invoice_no", "")))
            self.table.setItem(i, 3, QTableWidgetItem(f"{curr(p['total_amount'])}"))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            view_btn = QPushButton("View")
            view_btn.setFixedWidth(60)
            view_btn.clicked.connect(lambda checked, pid=p["id"]: self._view(pid))
            btn_layout.addWidget(view_btn)
            btn_layout.addStretch()
            self.table.setCellWidget(i, 4, btn_widget)

    def _add(self):
        dlg = PurchaseDialog(self)
        if dlg.exec():
            self.refresh()

    def _view(self, pid):
        dlg = PurchaseDialog(self, pid)
        dlg.exec()
