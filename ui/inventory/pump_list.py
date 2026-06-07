from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QDialog, QFormLayout, QLineEdit, QComboBox,
                               QMessageBox, QHeaderView)
from models.fuel import Pump, Tank


class PumpDialog(QDialog):
    def __init__(self, parent=None, pump=None):
        super().__init__(parent)
        self.pump = pump
        self.setWindowTitle("Add Pump" if not pump else "Edit Pump")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        self.pump_no = QLineEdit()
        self.pump_no.setToolTip("A unique number or code for this pump (e.g. P-01)")
        self.tank_combo = QComboBox()
        self.tank_combo.setToolTip("The tank this pump draws fuel from")
        tanks = Tank.get_with_fuel_type()
        for t in tanks:
            self.tank_combo.addItem(f"{t['name']} ({t['fuel_name']})", t["id"])
        self.desc_edit = QLineEdit()
        self.desc_edit.setToolTip("Optional notes about this pump's location or type")

        layout.addRow("Pump No:", self.pump_no)
        layout.addRow("Tank:", self.tank_combo)
        layout.addRow("Description:", self.desc_edit)

        if pump:
            self.pump_no.setText(pump["pump_no"])
            idx = self.tank_combo.findData(pump["tank_id"])
            if idx >= 0:
                self.tank_combo.setCurrentIndex(idx)
            self.desc_edit.setText(pump.get("description", ""))

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save this pump and return to the list")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setToolTip("Discard changes and go back")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _save(self):
        if not self.pump_no.text().strip():
            QMessageBox.warning(self, "Error", "Pump number is required.")
            return
        if self.pump:
            from database.connection import get_connection
            conn = get_connection()
            conn.execute(
                "UPDATE pumps SET pump_no=?, tank_id=?, description=? WHERE id=?",
                (self.pump_no.text(), self.tank_combo.currentData(),
                 self.desc_edit.text(), self.pump["id"]),
            )
            conn.commit()
            conn.close()
        else:
            Pump.create(self.pump_no.text(), self.tank_combo.currentData(),
                         self.desc_edit.text())
        self.accept()


class PumpListWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("Pump Management")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        add_btn = QPushButton("+ Add Pump")
        add_btn.setToolTip("Add a new dispensing pump")
        add_btn.clicked.connect(self._add)
        header.addWidget(add_btn)
        layout.addLayout(header)

        subtitle = QLabel("Configure dispensing pumps and link them to fuel tanks")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px; padding: 0 0 12px 0;")
        layout.addWidget(subtitle)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search pumps...")
        self.search_bar.textChanged.connect(self._filter)
        layout.addWidget(self.search_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Pump No", "Tank", "Fuel", "Description", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        pumps = Pump.get_with_tank()
        self.table.setRowCount(len(pumps))
        for i, p in enumerate(pumps):
            self.table.setItem(i, 0, QTableWidgetItem(p["pump_no"]))
            self.table.setItem(i, 1, QTableWidgetItem(p["tank_name"]))
            self.table.setItem(i, 2, QTableWidgetItem(p["fuel_name"]))
            self.table.setItem(i, 3, QTableWidgetItem(p.get("description", "")))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            edit_btn = QPushButton("Edit")
            edit_btn.setToolTip("Edit this pump's details")
            edit_btn.setFixedWidth(60)
            edit_btn.clicked.connect(lambda checked, pid=p["id"]: self._edit(pid))
            del_btn = QPushButton("Del")
            del_btn.setObjectName("dangerBtn")
            del_btn.setToolTip("Delete this pump permanently")
            del_btn.setFixedWidth(60)
            del_btn.clicked.connect(lambda checked, pid=p["id"]: self._delete(pid))
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch()
            self.table.setCellWidget(i, 4, btn_widget)

    def _add(self):
        dlg = PumpDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit(self, pump_id):
        pump = Pump.get_by_id(pump_id)
        if pump:
            dlg = PumpDialog(self, pump)
            if dlg.exec():
                self.refresh()

    def _delete(self, pump_id):
        reply = QMessageBox.question(self, "Confirm", "Delete this pump?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            Pump.delete(pump_id)
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
