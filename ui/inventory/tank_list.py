from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
                               QComboBox, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from models.fuel import FuelType, Tank


class TankDialog(QDialog):
    def __init__(self, parent=None, tank=None):
        super().__init__(parent)
        self.tank = tank
        self.setWindowTitle("Add Tank" if not tank else "Edit Tank")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setToolTip("A label to identify this tank (e.g. Tank-1, Main Storage)")
        self.fuel_combo = QComboBox()
        self.fuel_combo.setToolTip("The type of fuel stored in this tank")
        fuels = FuelType.get_all()
        for f in fuels:
            self.fuel_combo.addItem(f["name"], f["id"])
        self.capacity_spin = QDoubleSpinBox()
        self.capacity_spin.setRange(0, 100000)
        self.capacity_spin.setDecimals(2)
        self.capacity_spin.setSuffix(" L")
        self.capacity_spin.setToolTip("Maximum fuel capacity of this tank in litres")
        self.level_spin = QDoubleSpinBox()
        self.level_spin.setRange(0, 100000)
        self.level_spin.setDecimals(2)
        self.level_spin.setSuffix(" L")
        self.level_spin.setToolTip("Current fuel level remaining in the tank")

        layout.addRow("Tank Name:", self.name_edit)
        layout.addRow("Fuel Type:", self.fuel_combo)
        layout.addRow("Capacity:", self.capacity_spin)
        layout.addRow("Current Level:", self.level_spin)

        if tank:
            self.name_edit.setText(tank["name"])
            idx = self.fuel_combo.findData(tank["fuel_type_id"])
            if idx >= 0:
                self.fuel_combo.setCurrentIndex(idx)
            self.capacity_spin.setValue(tank["capacity"])
            self.level_spin.setValue(tank["current_level"])

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save this tank and return to the list")
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
            QMessageBox.warning(self, "Error", "Tank name is required.")
            return
        if self.tank:
            from database.connection import get_connection
            conn = get_connection()
            conn.execute(
                "UPDATE tanks SET name=?, fuel_type_id=?, capacity=?, current_level=? WHERE id=?",
                (self.name_edit.text(), self.fuel_combo.currentData(),
                 self.capacity_spin.value(), self.level_spin.value(), self.tank["id"]),
            )
            conn.commit()
            conn.close()
        else:
            Tank.create(self.name_edit.text(), self.fuel_combo.currentData(),
                         self.capacity_spin.value(), self.level_spin.value())
        self.accept()


class TankListWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("Tank Management")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        add_btn = QPushButton("+ Add Tank")
        add_btn.setToolTip("Register a new fuel storage tank")
        add_btn.clicked.connect(self._add)
        header.addWidget(add_btn)
        layout.addLayout(header)

        subtitle = QLabel("Manage fuel storage tanks and track current fuel levels")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px; padding: 0 0 12px 0;")
        layout.addWidget(subtitle)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Fuel Type", "Capacity (L)", "Current Level (L)", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        tanks = Tank.get_with_fuel_type()
        self.table.setRowCount(len(tanks))
        for i, t in enumerate(tanks):
            self.table.setItem(i, 0, QTableWidgetItem(t["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(t["fuel_name"]))
            self.table.setItem(i, 2, QTableWidgetItem(f"{t['capacity']:,.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{t['current_level']:,.2f}"))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            edit_btn = QPushButton("Edit")
            edit_btn.setToolTip("Edit this tank's details")
            edit_btn.setFixedWidth(60)
            edit_btn.clicked.connect(lambda checked, tid=t["id"]: self._edit(tid))
            del_btn = QPushButton("Del")
            del_btn.setObjectName("dangerBtn")
            del_btn.setToolTip("Delete this tank permanently")
            del_btn.setFixedWidth(60)
            del_btn.clicked.connect(lambda checked, tid=t["id"]: self._delete(tid))
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch()
            self.table.setCellWidget(i, 4, btn_widget)

    def _add(self):
        dlg = TankDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit(self, tank_id):
        tank = Tank.get_by_id(tank_id)
        if tank:
            dlg = TankDialog(self, tank)
            if dlg.exec():
                self.refresh()

    def _delete(self, tank_id):
        reply = QMessageBox.question(self, "Confirm", "Delete this tank?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            Tank.delete(tank_id)
            self.refresh()
