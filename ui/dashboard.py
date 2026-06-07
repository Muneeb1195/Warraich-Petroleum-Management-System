from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QGridLayout, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database.connection import get_connection
from utils.formatting import curr


class StatCard(QFrame):
    def __init__(self, title, value, accent_color="#58a6ff", icon=""):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumHeight(130)
        self.setMaximumHeight(150)
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: #161b22;
                border-radius: 8px;
                border: 1px solid #21262d;
                border-left: 4px solid {accent_color};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 28px;")
        icon_label.setFixedWidth(40)
        icon_label.setAlignment(Qt.AlignTop)
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;")
        text_layout.addWidget(self.title_label)

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("cardValue")
        self.value_label.setStyleSheet(f"color: #f0f6fc; font-size: 26px; font-weight: 700;")
        text_layout.addWidget(self.value_label)

        layout.addLayout(text_layout, 1)


class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #f0f6fc; padding: 0 0 20px 0;")
        layout.addWidget(title)

        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(16)
        layout.addLayout(self.cards_grid)

        self.today_sales_card = StatCard("Today's Sales", curr(0), "#58a6ff", "💰")
        self.month_sales_card = StatCard("This Month", curr(0), "#3fb950", "📈")
        self.profit_card = StatCard("Today's Profit", curr(0), "#d29922", "📊")
        self.today_expense_card = StatCard("Today's Expenses", curr(0), "#f85149", "💸")
        self.tank_count_card = StatCard("Fuel Tanks", "0", "#58a6ff", "⛽")
        self.lube_count_card = StatCard("Lube Products", "0", "#3fb950", "🛢️")
        self.staff_count_card = StatCard("Active Staff", "0", "#d29922", "👥")
        self.pending_payroll_card = StatCard("Pending Payroll", curr(0), "#f85149", "💵")

        positions = [
            (0, 0), (0, 1), (0, 2), (0, 3),
            (1, 0), (1, 1), (1, 2), (1, 3),
        ]
        cards = [
            self.today_sales_card, self.month_sales_card, self.profit_card, self.today_expense_card,
            self.tank_count_card, self.lube_count_card, self.staff_count_card, self.pending_payroll_card,
        ]
        for card, (r, c) in zip(cards, positions):
            self.cards_grid.addWidget(card, r, c)

        layout.addStretch()

        self.refresh()

    def refresh(self):
        conn = get_connection()

        today_sales = conn.execute(
            "SELECT COALESCE(SUM(grand_total),0) as t FROM sales WHERE sale_date=date('now')"
        ).fetchone()["t"]
        self.today_sales_card.value_label.setText(f"{curr(today_sales)}")

        month_sales = conn.execute(
            "SELECT COALESCE(SUM(grand_total),0) as t FROM sales WHERE strftime('%Y-%m', sale_date)=strftime('%Y-%m', 'now')"
        ).fetchone()["t"]
        self.month_sales_card.value_label.setText(f"{curr(month_sales)}")

        today_expense = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as t FROM expenses WHERE expense_date=date('now')"
        ).fetchone()["t"]
        self.today_expense_card.value_label.setText(f"{curr(today_expense)}")

        staff_count = conn.execute(
            "SELECT COUNT(*) as c FROM employees WHERE is_active=1"
        ).fetchone()["c"]
        self.staff_count_card.value_label.setText(str(staff_count))

        tank_count = conn.execute("SELECT COUNT(*) as c FROM tanks").fetchone()["c"]
        self.tank_count_card.value_label.setText(str(tank_count))

        lube_count = conn.execute("SELECT COUNT(*) as c FROM lube_products").fetchone()["c"]
        self.lube_count_card.value_label.setText(str(lube_count))

        pending = conn.execute(
            "SELECT COALESCE(SUM(net_salary),0) as t FROM payroll WHERE paid=0"
        ).fetchone()["t"]
        self.pending_payroll_card.value_label.setText(f"{curr(pending)}")

        cost_sold = conn.execute(
            """SELECT COALESCE(SUM(si.qty * pi.rate),0) as t FROM sale_items si
               JOIN sales s ON s.id = si.sale_id AND s.sale_date=date('now')
               JOIN purchase_items pi ON pi.fuel_type_id = si.pump_id
               WHERE si.item_type='fuel'"""
        ).fetchone()["t"]
        profit = today_sales - cost_sold - today_expense
        profit_color = "#3fb950" if profit >= 0 else "#f85149"
        self.profit_card.value_label.setStyleSheet(f"color: {profit_color}; font-size: 26px; font-weight: 700;")
        self.profit_card.value_label.setText(f"{curr(profit)}")

        conn.close()
