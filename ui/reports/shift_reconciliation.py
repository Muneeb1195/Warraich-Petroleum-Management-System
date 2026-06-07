from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QComboBox, QDateEdit, QDoubleSpinBox,
                               QMessageBox, QHeaderView, QGroupBox, QFormLayout)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor

from database.connection import get_connection
from models.fuel import Pump
from database.settings import settings
from utils.formatting import curr


class ShiftReconciliationWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Shift Reconciliation")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #f0f6fc;")
        layout.addWidget(title)

        subtitle = QLabel("Record opening/closing readings per pump and compare with actual sales")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px; padding-bottom: 12px;")
        layout.addWidget(subtitle)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.refresh)
        controls.addWidget(self.date_edit)

        controls.addWidget(QLabel("Shift:"))
        self.shift_combo = QComboBox()
        self.shift_combo.addItems(["Morning", "Evening", "Night"])
        self.shift_combo.currentTextChanged.connect(self.refresh)
        controls.addWidget(self.shift_combo)

        controls.addStretch()

        start_btn = QPushButton("Start Shift")
        start_btn.setObjectName("successBtn")
        start_btn.clicked.connect(self._start_shift)
        controls.addWidget(start_btn)

        close_btn = QPushButton("Close Shift")
        close_btn.clicked.connect(self._close_shift)
        controls.addWidget(close_btn)

        reconcile_btn = QPushButton("Reconcile")
        reconcile_btn.setObjectName("warningBtn")
        reconcile_btn.clicked.connect(self._reconcile)
        controls.addWidget(reconcile_btn)

        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Pump", "Fuel", "Opening", "Closing", "Expected", "Actual Sales", "Variance"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("color: #8b949e; font-size: 13px; padding-top: 8px;")
        layout.addWidget(self.summary_label)

        self.refresh()

    def refresh(self):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        shift = self.shift_combo.currentText()
        conn = get_connection()

        pumps = Pump.get_with_tank()
        readings = {}
        for r in conn.execute(
            "SELECT pump_id, opening_reading, closing_reading, is_closed FROM shift_readings WHERE date=? AND shift=?",
            (date, shift),
        ).fetchall():
            readings[r["pump_id"]] = r

        sales_by_pump = {}
        for r in conn.execute("""
            SELECT p.id as pump_id, COALESCE(SUM(si.qty),0) as total_qty
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id AND s.sale_date=?
            JOIN pumps p ON p.id = si.pump_id
            WHERE si.item_type='fuel'
            GROUP BY p.id
        """, (date,)).fetchall():
            sales_by_pump[r["pump_id"]] = r["total_qty"]

        self.table.setRowCount(len(pumps))
        total_expected = 0
        total_actual = 0
        total_variance = 0

        for i, p in enumerate(pumps):
            self.table.setItem(i, 0, QTableWidgetItem(p["pump_no"]))
            self.table.setItem(i, 1, QTableWidgetItem(p["fuel_name"]))

            rd = readings.get(p["id"])

            if rd:
                self.table.setItem(i, 2, QTableWidgetItem(f"{rd['opening_reading']:,.2f}"))
                expected = rd["closing_reading"] - rd["opening_reading"]
                self.table.setItem(i, 3, QTableWidgetItem(f"{rd['closing_reading']:,.2f}"))
                self.table.setItem(i, 4, QTableWidgetItem(f"{expected:,.2f} L"))
            else:
                self.table.setItem(i, 2, QTableWidgetItem("—"))
                self.table.setItem(i, 3, QTableWidgetItem("—"))
                self.table.setItem(i, 4, QTableWidgetItem("—"))
                expected = 0

            actual = sales_by_pump.get(p["id"], 0)
            self.table.setItem(i, 5, QTableWidgetItem(f"{actual:,.2f} L"))

            if rd and rd["is_closed"]:
                variance = actual - expected
                total_expected += expected
                total_actual += actual
                total_variance += variance
                item = QTableWidgetItem(f"{variance:+,.2f} L")
                if abs(variance) > 2:
                    item.setBackground(QColor("#f8514922") if variance < 0 else QColor("#d2992222"))
                    item.setToolTip("Discrepancy detected!")
                self.table.setItem(i, 6, item)
            else:
                self.table.setItem(i, 6, QTableWidgetItem("⏳ Not closed"))

        conn.close()

        if total_expected > 0:
            pct = (total_variance / total_expected * 100) if total_expected else 0
            status = "✅ RECONCILED" if abs(pct) < 1 else "⚠️ DISCREPANCY"
            self.summary_label.setText(
                f"Expected: {total_expected:,.2f} L  |  "
                f"Actual: {total_actual:,.2f} L  |  "
                f"Variance: {total_variance:+,.2f} L ({pct:+.2f}%)  |  "
                f"Status: {status}"
            )

    def _start_shift(self):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        shift = self.shift_combo.currentText()
        pumps = Pump.get_with_tank()
        conn = get_connection()

        for p in pumps:
            existing = conn.execute(
                "SELECT id FROM shift_readings WHERE date=? AND shift=? AND pump_id=?",
                (date, shift, p["id"]),
            ).fetchone()
            if not existing:
                rate = settings.fuel_rate(p["fuel_name"].lower())
                conn.execute(
                    "INSERT INTO shift_readings (date, shift, pump_id, opening_reading) VALUES (?,?,?,?)",
                    (date, shift, p["id"], 0),
                )

        conn.commit()
        conn.close()
        QMessageBox.information(self, "Shift Started",
                                f"Shift '{shift}' started for {date}.\n"
                                "Enter opening readings for each pump.")
        self.refresh()

    def _close_shift(self):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        shift = self.shift_combo.currentText()
        conn = get_connection()
        pumps = Pump.get_with_tank()

        for p in pumps:
            rd = conn.execute(
                "SELECT id FROM shift_readings WHERE date=? AND shift=? AND pump_id=?",
                (date, shift, p["id"]),
            ).fetchone()
            if rd:
                conn.execute(
                    "UPDATE shift_readings SET closing_reading=?, is_closed=1, reconciled_at=datetime('now') WHERE id=?",
                    (0, rd["id"]),
                )

        conn.commit()
        conn.close()
        self.refresh()
        QMessageBox.information(self, "Shift Closed",
                                f"Shift '{shift}' closed.\nEnter closing readings then reconcile.")

    def _reconcile(self):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        shift = self.shift_combo.currentText()
        conn = get_connection()
        conn.execute(
            "UPDATE shift_readings SET reconciled_at=datetime('now') WHERE date=? AND shift=?",
            (date, shift),
        )
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Reconciled", "Shift reconciled successfully.")
        self.refresh()
