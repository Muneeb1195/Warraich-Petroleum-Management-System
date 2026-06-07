from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
                               QComboBox, QMessageBox, QHeaderView)
from models.lube import LubeProduct
from utils.formatting import curr, CURRENCY_SYMBOL_RAW



class LubeDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Add Lubricant" if not product else "Edit Lubricant")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self.brand_edit = QLineEdit()
        self.brand_edit.setToolTip("Brand name of the lubricant (e.g. Shell, Mobil)")
        self.name_edit = QLineEdit()
        self.name_edit.setToolTip("Product name (e.g. Engine Oil 20W-50)")
        self.unit_combo = QComboBox()
        self.unit_combo.setToolTip("Unit of measurement for this product")
        self.unit_combo.addItems(["Bottle", "Can", "Liter", "Pouch", "Box"])
        self.purchase_rate = QDoubleSpinBox()
        self.purchase_rate.setRange(0, 999999)
        self.purchase_rate.setDecimals(2)
        self.purchase_rate.setToolTip("Cost price per unit paid to the supplier")
        self.selling_price = QDoubleSpinBox()
        self.selling_price.setRange(0, 999999)
        self.selling_price.setDecimals(2)
        self.selling_price.setToolTip("Retail selling price per unit to customers")
        self.stock_qty = QDoubleSpinBox()
        self.stock_qty.setRange(0, 999999)
        self.stock_qty.setDecimals(2)
        self.stock_qty.setToolTip("Current quantity available in stock")
        self.hsn_edit = QLineEdit("271019")
        self.hsn_edit.setToolTip("Harmonized System code for GST classification")
        self.gst_rate = QDoubleSpinBox()
        self.gst_rate.setRange(0, 100)
        self.gst_rate.setDecimals(2)
        self.gst_rate.setValue(18)
        self.gst_rate.setToolTip("GST tax rate percentage applicable to this product")

        layout.addRow("Brand:", self.brand_edit)
        layout.addRow("Product Name:", self.name_edit)
        layout.addRow("Unit:", self.unit_combo)
        layout.addRow("Purchase Rate:", self.purchase_rate)
        layout.addRow("Selling Price:", self.selling_price)
        layout.addRow("Stock Qty:", self.stock_qty)
        layout.addRow("HSN Code:", self.hsn_edit)
        layout.addRow("GST Rate (%):", self.gst_rate)

        if product:
            self.brand_edit.setText(product["brand"])
            self.name_edit.setText(product["product_name"])
            idx = self.unit_combo.findText(product["unit"])
            if idx >= 0:
                self.unit_combo.setCurrentIndex(idx)
            self.purchase_rate.setValue(product["purchase_rate"])
            self.selling_price.setValue(product["selling_price"])
            self.stock_qty.setValue(product["stock_qty"])
            self.hsn_edit.setText(product.get("hsn_code", ""))
            self.gst_rate.setValue(product.get("gst_rate", 18))

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save this product and return to the list")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setToolTip("Discard changes and go back")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _save(self):
        if not self.name_edit.text().strip() or not self.brand_edit.text().strip():
            QMessageBox.warning(self, "Error", "Brand and Product Name are required.")
            return
        if self.product:
            LubeProduct.update(self.product["id"],
                               brand=self.brand_edit.text(),
                               product_name=self.name_edit.text(),
                               unit=self.unit_combo.currentText(),
                               purchase_rate=self.purchase_rate.value(),
                               selling_price=self.selling_price.value(),
                               stock_qty=self.stock_qty.value(),
                               hsn_code=self.hsn_edit.text(),
                               gst_rate=self.gst_rate.value())
        else:
            LubeProduct.create(self.brand_edit.text(), self.name_edit.text(),
                                self.unit_combo.currentText(),
                                self.purchase_rate.value(), self.selling_price.value(),
                                self.stock_qty.value(), self.hsn_edit.text(),
                                self.gst_rate.value())
        self.accept()


class LubeListWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("Lubricants Inventory")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        add_btn = QPushButton("+ Add Product")
        add_btn.setToolTip("Add a new lubricant product to inventory")
        add_btn.clicked.connect(self._add)
        header.addWidget(add_btn)
        layout.addLayout(header)

        subtitle = QLabel("Manage lubricant products with stock tracking and pricing")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px; padding: 0 0 12px 0;")
        layout.addWidget(subtitle)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search products...")
        self.search_bar.textChanged.connect(self._filter)
        layout.addWidget(self.search_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Brand", "Product", "Unit", "Purchase Rate", "Selling Price", "Stock", "GST (%)", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        products = LubeProduct.get_all("brand")
        self.table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.table.setItem(i, 0, QTableWidgetItem(p["brand"]))
            self.table.setItem(i, 1, QTableWidgetItem(p["product_name"]))
            self.table.setItem(i, 2, QTableWidgetItem(p["unit"]))
            self.table.setItem(i, 3, QTableWidgetItem(f"{curr(p['purchase_rate'])}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{curr(p['selling_price'])}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{p['stock_qty']:,.2f}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{p.get('gst_rate', 18)}%"))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            edit_btn = QPushButton("Edit")
            edit_btn.setToolTip("Edit this product's details")
            edit_btn.setFixedWidth(60)
            edit_btn.clicked.connect(lambda checked, pid=p["id"]: self._edit(pid))
            del_btn = QPushButton("Del")
            del_btn.setObjectName("dangerBtn")
            del_btn.setToolTip("Delete this product permanently")
            del_btn.setFixedWidth(60)
            del_btn.clicked.connect(lambda checked, pid=p["id"]: self._delete(pid))
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch()
            self.table.setCellWidget(i, 7, btn_widget)

    def _add(self):
        dlg = LubeDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit(self, pid):
        p = LubeProduct.get_by_id(pid)
        if p:
            dlg = LubeDialog(self, p)
            if dlg.exec():
                self.refresh()

    def _delete(self, pid):
        reply = QMessageBox.question(self, "Confirm", "Delete this product?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            LubeProduct.delete(pid)
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
