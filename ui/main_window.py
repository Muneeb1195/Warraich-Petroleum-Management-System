from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QStackedWidget, QFrame,
                               QStatusBar, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from datetime import datetime

from ui.dashboard import DashboardWidget
from ui.inventory.tank_list import TankListWidget
from ui.inventory.pump_list import PumpListWidget
from ui.inventory.lube_list import LubeListWidget
from ui.purchases.purchase_list import PurchaseListWidget
from ui.sales.pos import PosWidget
from ui.sales.customer_list import CustomerListWidget
from ui.expenses.expense_list import ExpenseListWidget
from ui.staff.employee_list import EmployeeListWidget
from ui.staff.attendance_widget import AttendanceWidget
from ui.payroll.payroll_widget import PayrollWidget
from ui.reports.report_widget import ReportWidget
from ui.reports.shift_reconciliation import ShiftReconciliationWidget
from ui.settings_dialog import SettingsDialog
from database.settings import settings
from database.backup import manual_backup
from database.cloud_backup import is_connected


class SidebarButton(QPushButton):
    def __init__(self, text, icon=""):
        super().__init__(f"  {icon}  {text}")
        self.setObjectName("navBtn")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(42)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Petrol Pump Management - {settings.business_name()}")
        self.setMinimumSize(1280, 800)
        self.resize(1440, 920)
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === HEADER BAR ===
        header = QWidget()
        header.setObjectName("headerBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        header_title = QLabel(settings.business_name())
        header_title.setObjectName("headerTitle")
        header_layout.addWidget(header_title)

        header_layout.addStretch()

        self.header_clock = QLabel()
        self.header_clock.setObjectName("headerTime")
        header_layout.addWidget(self.header_clock)

        backup_btn = QPushButton(" Backup Now")
        backup_btn.setObjectName("headerBackupBtn")
        backup_btn.setCursor(Qt.PointingHandCursor)
        backup_btn.clicked.connect(self._do_backup)
        header_layout.addWidget(backup_btn)

        main_layout.addWidget(header)

        # clock timer
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        # === BODY (sidebar + content) ===
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._sidebar = QWidget()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setFixedWidth(230)
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(2)

        sidebar_title = QLabel("⛽  Warraich Petroleum")
        sidebar_title.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(sidebar_title)

        sidebar_sub = QLabel("      Management System")
        sidebar_sub.setObjectName("sidebarSubtitle")
        sidebar_layout.addWidget(sidebar_sub)

        sidebar_layout.addSpacing(8)

        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊", "Dashboard"),
            ("inventory", "⛽", "Inventory"),
            ("purchases", "📦", "Purchases"),
            ("pos", "🧾", "POS / Sales"),
            ("customers", "👥", "Customers"),
            ("expenses", "💰", "Expenses"),
            ("staff", "👨‍💼", "Staff"),
            ("payroll", "💵", "Payroll"),
            ("reports", "📈", "Reports"),
            ("reconciliation", "🔄", "Shift Recon"),
            ("settings", "⚙️", "Settings"),
        ]

        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #21262d; margin: 4px 12px;")
        sidebar_layout.addWidget(separator)
        sidebar_layout.addSpacing(4)

        self.btn_group = []
        for key, icon, label in nav_items:
            btn = SidebarButton(label, icon)
            self.nav_buttons[key] = btn
            self.btn_group.append(btn)
            sidebar_layout.addWidget(btn)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))

        sidebar_layout.addStretch()

        version = QLabel("v1.0")
        version.setObjectName("sidebarVersion")
        version.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version)

        # Content area with a wrapper to add padding
        content_wrapper = QWidget()
        content_wrapper.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(24, 20, 24, 20)

        self._content_stack = QStackedWidget()
        self._content_stack.setObjectName("contentStack")
        content_layout.addWidget(self._content_stack)

        body_layout.addWidget(self._sidebar)
        body_layout.addWidget(content_wrapper, 1)

        main_layout.addWidget(body, 1)

        # === STATUS BAR ===
        status = self.statusBar()
        cloud_icon = "☁️" if is_connected() else ""
        cloud_text = f"Cloud: {settings.last_cloud_backup()}" if is_connected() else "☁️ Not connected"
        status_label = QLabel(
            f"  Auto-backup every {settings.backup_interval_days()} days  |  "
            f"{cloud_text}  |  "
            f"{settings.business_address() if settings.business_address() else ''}"
        )
        status.addWidget(status_label)

        self._navigate("dashboard")

    def _update_clock(self):
        now = datetime.now()
        self.header_clock.setText(now.strftime("%A, %d %B %Y  %I:%M:%S %p"))

    def _load_pages(self):
        self._pages = {}
        self._pages["dashboard"] = DashboardWidget()
        self._pages["inventory"] = self._make_tabbed_inventory()
        self._pages["purchases"] = PurchaseListWidget()
        self._pages["pos"] = PosWidget()
        self._pages["customers"] = CustomerListWidget()
        self._pages["expenses"] = ExpenseListWidget()
        self._pages["staff"] = self._make_tabbed_staff()
        self._pages["payroll"] = PayrollWidget()
        self._pages["reports"] = ReportWidget()
        self._pages["reconciliation"] = ShiftReconciliationWidget()
        self._pages["settings"] = SettingsDialog(self)

        for page in self._pages.values():
            if isinstance(page, QWidget) and page is not self._pages.get("settings"):
                self._content_stack.addWidget(page)

    def _make_tabbed_inventory(self):
        from PySide6.QtWidgets import QTabWidget
        tabs = QTabWidget()
        tabs.addTab(TankListWidget(), "Tanks")
        tabs.addTab(PumpListWidget(), "Pumps")
        tabs.addTab(LubeListWidget(), "Lubricants")
        return tabs

    def _make_tabbed_staff(self):
        from PySide6.QtWidgets import QTabWidget
        tabs = QTabWidget()
        tabs.addTab(EmployeeListWidget(), "Employees")
        tabs.addTab(AttendanceWidget(), "Attendance")
        return tabs

    def _navigate(self, page_key):
        for btn in self.btn_group:
            btn.setChecked(False)
        if page_key in self.nav_buttons:
            self.nav_buttons[page_key].setChecked(True)

        if not hasattr(self, "_pages"):
            self._load_pages()

        page = self._pages.get(page_key)
        if page:
            if isinstance(page, SettingsDialog):
                dlg = SettingsDialog(self)
                dlg.exec()
                return
            idx = self._content_stack.indexOf(page)
            if idx >= 0:
                self._content_stack.setCurrentIndex(idx)
            if hasattr(page, "refresh"):
                page.refresh()

    def _do_backup(self):
        try:
            path = manual_backup()
            QMessageBox.information(self, "Backup Complete", f"Database backed up to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", str(e))

    def refresh_current(self):
        if hasattr(self, "_pages"):
            w = self._content_stack.currentWidget()
            if hasattr(w, "refresh"):
                w.refresh()
