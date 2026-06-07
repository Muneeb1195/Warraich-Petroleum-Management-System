from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
                               QComboBox, QMessageBox, QHeaderView, QTabWidget,
                               QGroupBox, QTextEdit, QSpinBox)
from database.settings import settings
from models.sale import Sale
from models.customer import Customer
from models.fuel import Pump, FuelType
from models.lube import LubeProduct
from database.connection import get_connection
from utils.formatting import curr, CURRENCY_SYMBOL_RAW



class PosWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Point of Sale")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        tabs.addTab(self._make_fuel_tab(), "Fuel Sales")
        tabs.addTab(self._make_lube_tab(), "Lube Sales")
        tabs.addTab(self._make_cart_tab(), "Cart & Checkout")

    def _make_fuel_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        pumps = Pump.get_with_tank()
        self.fuel_items = []

        scroll = QWidget()
        scroll_layout = QVBoxLayout(scroll)

        if not pumps:
            scroll_layout.addWidget(QLabel("No pumps configured. Add pumps in Inventory first."))
        else:
            for p in pumps:
                gb = QGroupBox(f"Pump {p['pump_no']} - {p['fuel_name']}")
                gb_layout = QHBoxLayout(gb)
                gb_layout.addWidget(QLabel(f"Rate: {settings.fuel_rate(p['fuel_name'].lower()):.2f}/L"))

                gb_layout.addWidget(QLabel("Opening:"))
                opening_spin = QDoubleSpinBox()
                opening_spin.setRange(0, 999999)
                opening_spin.setDecimals(2)
                opening_spin.setValue(0)
                gb_layout.addWidget(opening_spin)

                gb_layout.addWidget(QLabel("Closing:"))
                closing_spin = QDoubleSpinBox()
                closing_spin.setRange(0, 999999)
                closing_spin.setDecimals(2)
                closing_spin.setValue(0)
                gb_layout.addWidget(closing_spin)

                gb_layout.addWidget(QLabel("Qty:"))
                qty_label = QLabel("0.00 L")
                gb_layout.addWidget(qty_label)

                def update_qty(op=opening_spin, cl=closing_spin, ql=qty_label):
                    q = max(0, cl.value() - op.value())
                    ql.setText(f"{q:.2f} L")

                opening_spin.valueChanged.connect(update_qty)
                closing_spin.valueChanged.connect(update_qty)

                add_btn = QPushButton("Add to Cart")
                add_btn.clicked.connect(
                    lambda checked, pp=p, op=opening_spin, cl=closing_spin,
                           ql=qty_label: self._add_fuel_to_cart(pp, op, cl, ql)
                )
                gb_layout.addWidget(add_btn)

                scroll_layout.addWidget(gb)
                self.fuel_items.append((p, opening_spin, closing_spin, qty_label))

        scroll_layout.addStretch()

        scroll_area = QWidget()
        scroll_area_layout = QVBoxLayout(scroll_area)
        scroll_area_layout.addWidget(scroll)
        layout.addWidget(scroll_area)
        return tab

    def _make_lube_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        lubes = LubeProduct.get_all("brand")
        self.lube_table = QTableWidget()
        self.lube_table.setColumnCount(6)
        self.lube_table.setHorizontalHeaderLabels(["Brand", "Product", "Price", "Stock", "Qty", "Action"])
        self.lube_table.horizontalHeader().setStretchLastSection(True)
        self.lube_table.setSelectionBehavior(QTableWidget.SelectRows)

        self.lube_table.setRowCount(len(lubes))
        for i, l in enumerate(lubes):
            self.lube_table.setItem(i, 0, QTableWidgetItem(l["brand"]))
            self.lube_table.setItem(i, 1, QTableWidgetItem(l["product_name"]))
            self.lube_table.setItem(i, 2, QTableWidgetItem(f"{curr(l['selling_price'])}"))
            self.lube_table.setItem(i, 3, QTableWidgetItem(f"{l['stock_qty']:,.2f} {l['unit']}"))

            qty_spin = QDoubleSpinBox()
            qty_spin.setRange(0, 9999)
            qty_spin.setDecimals(2)
            qty_spin.setValue(1)
            self.lube_table.setCellWidget(i, 4, qty_spin)

            add_btn = QPushButton("Add")
            add_btn.clicked.connect(lambda checked, li=l, qs=qty_spin: self._add_lube_to_cart(li, qs))
            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(2, 2, 2, 2)
            btn_l.addWidget(add_btn)
            self.lube_table.setCellWidget(i, 5, btn_w)

        layout.addWidget(self.lube_table)
        return tab

    def _make_cart_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.cart_items = []

        opts_group = QGroupBox("Sale Options")
        opts_layout = QHBoxLayout(opts_group)
        opts_layout.addWidget(QLabel("Customer:"))
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("Walk-in Customer", None)
        customers = Customer.get_all("name")
        for c in customers:
            self.customer_combo.addItem(f"{c['name']} ({c['phone']})", c["id"])
        opts_layout.addWidget(self.customer_combo)

        opts_layout.addWidget(QLabel("Payment:"))
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Cash", "Card", "UPI", "Credit"])
        opts_layout.addWidget(self.payment_combo)

        opts_layout.addWidget(QLabel("GST%:"))
        self.gst_spin = QDoubleSpinBox()
        self.gst_spin.setRange(0, 100)
        self.gst_spin.setDecimals(2)
        self.gst_spin.setValue(settings.default_gst_rate())
        opts_layout.addWidget(self.gst_spin)

        layout.addWidget(opts_group)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Item", "Qty", "Rate", "Amount", "Action"])
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.cart_table)

        self.totals_group = QGroupBox("Totals")
        totals_layout = QFormLayout(self.totals_group)
        self.taxable_label = QLabel(curr(0))
        self.cgst_label = QLabel(curr(0))
        self.sgst_label = QLabel(curr(0))
        self.total_label = QLabel(curr(0))
        self.round_off_label = QLabel(curr(0))
        self.grand_total_label = QLabel(curr(0))
        self.grand_total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1890ff;")
        totals_layout.addRow("Taxable Amount:", self.taxable_label)
        totals_layout.addRow("CGST:", self.cgst_label)
        totals_layout.addRow("SGST:", self.sgst_label)
        totals_layout.addRow("Total:", self.total_label)
        totals_layout.addRow("Round Off:", self.round_off_label)
        totals_layout.addRow("Grand Total:", self.grand_total_label)
        layout.addWidget(self.totals_group)

        btn_layout = QHBoxLayout()
        checkout_btn = QPushButton("Complete Sale")
        checkout_btn.setObjectName("successBtn")
        checkout_btn.clicked.connect(self._checkout)
        clear_btn = QPushButton("Clear Cart")
        clear_btn.setObjectName("dangerBtn")
        clear_btn.clicked.connect(self._clear_cart)
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(checkout_btn)
        layout.addLayout(btn_layout)

        return tab

    def _add_fuel_to_cart(self, pump, opening_spin, closing_spin, qty_label):
        qty = max(0, closing_spin.value() - opening_spin.value())
        if qty <= 0:
            QMessageBox.warning(self, "Error", "Closing reading must be greater than opening reading.")
            return
        rate = settings.fuel_rate(pump["fuel_name"].lower())
        if rate <= 0:
            QMessageBox.warning(self, "Error", f"Set {pump['fuel_name']} rate in Settings first.")
            return
        amount = qty * rate
        self.cart_items.append({
            "type": "fuel",
            "pump_id": pump["id"],
            "name": f"{pump['fuel_name']} - Pump {pump['pump_no']}",
            "opening": opening_spin.value(),
            "closing": closing_spin.value(),
            "qty": qty,
            "rate": rate,
            "amount": amount,
        })
        self._refresh_cart()

    def _add_lube_to_cart(self, lube, qty_spin):
        qty = qty_spin.value()
        if qty <= 0:
            return
        if qty > lube["stock_qty"]:
            QMessageBox.warning(self, "Error", f"Only {lube['stock_qty']:.2f} {lube['unit']} in stock.")
            return
        amount = qty * lube["selling_price"]
        self.cart_items.append({
            "type": "lube",
            "lube_id": lube["id"],
            "name": f"{lube['brand']} - {lube['product_name']}",
            "qty": qty,
            "rate": lube["selling_price"],
            "amount": amount,
        })
        self._refresh_cart()

    def _refresh_cart(self):
        self.cart_table.setRowCount(len(self.cart_items))
        taxable = 0
        for i, item in enumerate(self.cart_items):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item["name"]))
            self.cart_table.setItem(i, 1, QTableWidgetItem(f"{item['qty']:,.2f}"))
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"{curr(item['rate'])}"))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"{curr(item['amount'])}"))
            taxable += item["amount"]

            del_btn = QPushButton("X")
            del_btn.setObjectName("dangerBtn")
            del_btn.setFixedWidth(40)
            del_btn.clicked.connect(lambda checked, idx=i: self._remove_cart_item(idx))
            self.cart_table.setCellWidget(i, 4, del_btn)

        gst_rate = self.gst_spin.value()
        half_gst = round(taxable * gst_rate / 100 / 2, 2)
        total = taxable + half_gst * 2
        gt = round(total)
        round_off = round(gt - total, 2)

        self.taxable_label.setText(f"{curr(taxable)}")
        self.cgst_label.setText(f"{curr(half_gst)}")
        self.sgst_label.setText(f"{curr(half_gst)}")
        self.total_label.setText(f"{curr(total)}")
        self.round_off_label.setText(f"{curr(round_off)}")
        self.grand_total_label.setText(f"{curr(gt)}")

    def _remove_cart_item(self, idx):
        if 0 <= idx < len(self.cart_items):
            self.cart_items.pop(idx)
            self._refresh_cart()

    def _clear_cart(self):
        self.cart_items.clear()
        self._refresh_cart()

    def _checkout(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Error", "Cart is empty.")
            return

        sale_id, inv_no = Sale.create(
            customer_id=self.customer_combo.currentData(),
            payment_mode=self.payment_combo.currentText(),
            gst_rate=self.gst_spin.value(),
        )

        for item in self.cart_items:
            if item["type"] == "fuel":
                Sale.add_fuel_item(sale_id, item["pump_id"],
                                    item["opening"], item["closing"], item["rate"])
            else:
                Sale.add_lube_item(sale_id, item["lube_id"], item["qty"], item["rate"])
                LubeProduct.adjust_stock(item["lube_id"], -item["qty"])

        totals = Sale.calculate_totals(sale_id)

        if self.payment_combo.currentText() == "Credit" and self.customer_combo.currentData():
            Customer.update_balance(self.customer_combo.currentData(), totals["grand_total"])

        QMessageBox.information(
            self, "Sale Complete",
            f"Invoice: {inv_no}\n"
            f"Taxable: {curr(totals['taxable'])}\n"
            f"CGST: {curr(totals['cgst'])}\n"
            f"SGST: {curr(totals['sgst'])}\n"
            f"Grand Total: {curr(totals['grand_total'])}\n"
            f"Payment: {self.payment_combo.currentText()}"
        )

        self._clear_cart()

    def refresh(self):
        pass
