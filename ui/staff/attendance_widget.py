from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QComboBox, QMessageBox, QHeaderView, QDateEdit)
from PySide6.QtCore import QDate
from models.employee import Employee, Attendance


class AttendanceWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Daily Attendance")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

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

        mark_all_btn = QPushButton("Mark All Present")
        mark_all_btn.clicked.connect(self._mark_all_present)
        controls.addWidget(mark_all_btn)

        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Employee", "Role", "Status", "Action"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        shift = self.shift_combo.currentText()
        employees = Employee.get_active()
        attendance = {a["employee_id"]: a for a in Attendance.get_by_date(date) if a["shift"] == shift}

        self.table.setRowCount(len(employees))
        for i, emp in enumerate(employees):
            self.table.setItem(i, 0, QTableWidgetItem(emp["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(emp["role"]))

            att = attendance.get(emp["id"])
            status = att["status"] if att else "Not Marked"
            self.table.setItem(i, 2, QTableWidgetItem(status))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)

            for s in ["Present", "Absent", "Half Day", "Leave"]:
                b = QPushButton(s)
                b.setFixedWidth(70)
                if s == status:
                    b.setStyleSheet("background-color: #1890ff; color: white;")
                b.clicked.connect(lambda checked, eid=emp["id"], st=s: self._mark(eid, date, shift, st))
                btn_layout.addWidget(b)
            btn_layout.addStretch()
            self.table.setCellWidget(i, 3, btn_widget)

    def _mark(self, employee_id, date, shift, status):
        Attendance.mark(employee_id, date, shift, status)
        self.refresh()

    def _mark_all_present(self):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        shift = self.shift_combo.currentText()
        employees = Employee.get_active()
        for emp in employees:
            Attendance.mark(emp["id"], date, shift, "Present")
        self.refresh()
