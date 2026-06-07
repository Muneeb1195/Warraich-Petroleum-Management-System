from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QDoubleSpinBox, QComboBox,
                               QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from database.settings import settings
from models.sale import Sale
from models.customer import Customer
from models.lube import LubeProduct
from database.connection import get_connection
from utils.formatting import curr


class QuickSaleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Sale")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._sale_id = None
        self._inv_no = None

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("Quick Sale")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Enter the amount received and select payment mode.\nNo meter readings or items required.")
        desc.setStyleSheet("color: #8b949e; font-size: 12px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Amount
        amt_layout = QVBoxLayout()
        amt_layout.setSpacing(4)
        amt_label = QLabel(f"Amount ({settings.currency_symbol()})")
        amt_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #c9d1d9;")
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(0)
        self.amount_spin.selectAll()
        self.amount_spin.setFixedHeight(50)
        self.amount_spin.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px 12px;")
        amt_layout.addWidget(amt_label)
        amt_layout.addWidget(self.amount_spin)
        layout.addLayout(amt_layout)

        # Payment mode
        pay_layout = QHBoxLayout()
        pay_layout.addWidget(QLabel("Payment:"))
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Cash", "Card", "UPI", "Credit"])
        pay_layout.addWidget(self.payment_combo, 1)
        layout.addLayout(pay_layout)

        # Customer
        cust_layout = QHBoxLayout()
        cust_layout.addWidget(QLabel("Customer:"))
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("Walk-in Customer", None)
        customers = Customer.get_all("name")
        for c in customers:
            self.customer_combo.addItem(f"{c['name']} ({c['phone']})", c["id"])
        cust_layout.addWidget(self.customer_combo, 1)
        layout.addLayout(cust_layout)

        layout.addStretch()

        # Buttons
        complete_btn = QPushButton("Complete Sale")
        complete_btn.setObjectName("successBtn")
        complete_btn.setMinimumHeight(50)
        complete_btn.setStyleSheet(
            "font-size: 16px; font-weight: bold; background-color: #238636; "
            "color: white; border-radius: 8px; padding: 12px;"
        )
        complete_btn.clicked.connect(self._complete)
        layout.addWidget(complete_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        # Enter key shortcut
        QShortcut(QKeySequence("Return"), self).activated.connect(self._complete)
        QShortcut(QKeySequence("Enter"), self).activated.connect(self._complete)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.reject)

    def _complete(self):
        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "Error", "Enter an amount greater than zero.")
            return

        pmt = self.payment_combo.currentText()
        customer_id = self.customer_combo.currentData()

        sale_id, inv_no = Sale.create(
            customer_id=customer_id,
            payment_mode=pmt,
            gst_rate=0,
        )

        conn = get_connection()
        conn.execute(
            "INSERT INTO sale_items (sale_id, item_type, qty, rate, amount) VALUES (?, 'lube', 1, ?, ?)",
            (sale_id, amount, amount),
        )
        conn.commit()
        conn.close()

        totals = Sale.calculate_totals(sale_id)

        if pmt == "Credit" and customer_id:
            Customer.update_balance(customer_id, totals["grand_total"])

        self._sale_id = sale_id
        self._inv_no = inv_no

        reply = QMessageBox.question(
            self, "Sale Complete",
            f"Invoice: {inv_no}\n"
            f"Amount: {curr(amount)}\n"
            f"Payment: {pmt}\n\n"
            f"Print Invoice?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            from ui.sales.invoice_pdf import generate_invoice
            sale = Sale.get_with_details(sale_id)
            if sale:
                path = generate_invoice(sale, sale["items"])
                if path:
                    from PySide6.QtCore import QUrl
                    from PySide6.QtGui import QDesktopServices
                    QDesktopServices.openUrl(QUrl.fromLocalFile(path))

        self.accept()

    @property
    def last_sale_id(self):
        return self._sale_id
