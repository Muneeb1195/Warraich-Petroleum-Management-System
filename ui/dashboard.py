from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QGridLayout, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QPieSeries,
                               QBarSeries, QBarSet, QBarCategoryAxis,
                               QValueAxis, QPieSlice)

from database.connection import get_connection
from utils.formatting import curr


class StatCard(QFrame):
    def __init__(self, title, value, accent_color="#58a6ff", icon=""):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumHeight(120)
        self.setMaximumHeight(140)
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: #161b22;
                border-radius: 8px;
                border: 1px solid #21262d;
                border-left: 4px solid {accent_color};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 26px;")
        icon_label.setFixedWidth(36)
        icon_label.setAlignment(Qt.AlignTop)
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #8b949e; font-size: 11px; font-weight: 600; "
                                        "text-transform: uppercase; letter-spacing: 0.5px;")
        text_layout.addWidget(self.title_label)

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("color: #f0f6fc; font-size: 24px; font-weight: 700;")
        text_layout.addWidget(self.value_label)

        layout.addLayout(text_layout, 1)


class ChartCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("card")
        self.setStyleSheet("""
            QFrame#card {
                background-color: #161b22;
                border-radius: 8px;
                border: 1px solid #21262d;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #8b949e; font-size: 11px; font-weight: 600; "
                                   "text-transform: uppercase; letter-spacing: 0.5px; "
                                   "padding-bottom: 8px;")
        layout.addWidget(title_label)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(200)
        layout.addWidget(self.chart_view)


class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #f0f6fc; padding: 0 0 4px 0;")
        layout.addWidget(title)

        subtitle = QLabel("Real-time overview of sales, profit, stock, and staff")
        subtitle.setStyleSheet("color: #8b949e; font-size: 12px; padding: 0 0 16px 0;")
        layout.addWidget(subtitle)

        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(12)
        layout.addLayout(self.cards_grid)

        self.today_sales_card = StatCard("Today's Sales", curr(0), "#58a6ff", "💰")
        self.month_sales_card = StatCard("This Month", curr(0), "#3fb950", "📈")
        self.profit_card = StatCard("Today's Profit", curr(0), "#d29922", "📊")
        self.today_expense_card = StatCard("Today's Expenses", curr(0), "#f85149", "💸")
        self.tank_count_card = StatCard("Fuel Tanks", "0", "#58a6ff", "⛽")
        self.lube_count_card = StatCard("Lube Products", "0", "#3fb950", "🛢️")
        self.staff_count_card = StatCard("Active Staff", "0", "#d29922", "👥")
        self.pending_payroll_card = StatCard("Pending Payroll", curr(0), "#f85149", "💵")

        positions = [(0, 0), (0, 1), (0, 2), (0, 3),
                     (1, 0), (1, 1), (1, 2), (1, 3)]
        cards = [self.today_sales_card, self.month_sales_card, self.profit_card,
                 self.today_expense_card, self.tank_count_card, self.lube_count_card,
                 self.staff_count_card, self.pending_payroll_card]
        for card, (r, c) in zip(cards, positions):
            self.cards_grid.addWidget(card, r, c)

        # Charts row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(12)

        self.trend_chart = ChartCard("Sales Trend (Last 7 Days)")
        self.payment_chart = ChartCard("Today's Payment Split")
        self.top_chart = ChartCard("Top Products Today")

        charts_layout.addWidget(self.trend_chart, 1)
        charts_layout.addWidget(self.payment_chart, 1)
        charts_layout.addWidget(self.top_chart, 1)

        layout.addSpacing(24)
        layout.addLayout(charts_layout)
        layout.addStretch()

        self.refresh()

    def refresh(self):
        conn = get_connection()

        today_sales = conn.execute(
            "SELECT COALESCE(SUM(grand_total),0) FROM sales WHERE sale_date=date('now')"
        ).fetchone()[0]
        self.today_sales_card.value_label.setText(curr(today_sales))

        month_sales = conn.execute(
            "SELECT COALESCE(SUM(grand_total),0) FROM sales WHERE strftime('%Y-%m', sale_date)=strftime('%Y-%m', 'now')"
        ).fetchone()[0]
        self.month_sales_card.value_label.setText(curr(month_sales))

        today_expense = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE expense_date=date('now')"
        ).fetchone()[0]
        self.today_expense_card.value_label.setText(curr(today_expense))

        staff_count = conn.execute(
            "SELECT COUNT(*) FROM employees WHERE is_active=1"
        ).fetchone()[0]
        self.staff_count_card.value_label.setText(str(staff_count))

        tank_count = conn.execute("SELECT COUNT(*) FROM tanks").fetchone()[0]
        self.tank_count_card.value_label.setText(str(tank_count))

        lube_count = conn.execute("SELECT COUNT(*) FROM lube_products").fetchone()[0]
        self.lube_count_card.value_label.setText(str(lube_count))

        pending = conn.execute(
            "SELECT COALESCE(SUM(net_salary),0) FROM payroll WHERE paid=0"
        ).fetchone()[0]
        self.pending_payroll_card.value_label.setText(curr(pending))

        cost_sold = conn.execute("""
            SELECT COALESCE(SUM(si.qty * pi.rate),0) FROM sale_items si
            JOIN sales s ON s.id = si.sale_id AND s.sale_date=date('now')
            JOIN purchase_items pi ON pi.fuel_type_id = si.pump_id
            WHERE si.item_type='fuel'
        """).fetchone()[0] or 0
        profit = today_sales - cost_sold - today_expense
        profit_color = "#3fb950" if profit >= 0 else "#f85149"
        self.profit_card.value_label.setStyleSheet(f"color: {profit_color}; font-size: 24px; font-weight: 700;")
        self.profit_card.value_label.setText(curr(profit))

        self._build_trend_chart(conn)
        self._build_payment_chart(conn)
        self._build_top_chart(conn)

        conn.close()

    def _build_trend_chart(self, conn):
        series = QLineSeries()
        series.setName("Sales")
        series.setColor(Qt.GlobalColor.cyan)

        rows = conn.execute("""
            SELECT sale_date, COALESCE(SUM(grand_total),0) as total
            FROM sales
            WHERE sale_date >= date('now', '-6 days')
            GROUP BY sale_date
            ORDER BY sale_date
        """).fetchall()

        dates = []
        for i, r in enumerate(rows):
            series.append(i, r["total"])
            dates.append(r["sale_date"][-5:])

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("")
        chart.setBackgroundBrush(Qt.GlobalColor.transparent)
        chart.setPlotAreaBackgroundBrush(Qt.GlobalColor.transparent)
        chart.legend().setLabelColor(Qt.GlobalColor.white)
        chart.legend().setVisible(False)

        axis_x = QBarCategoryAxis()
        axis_x.append(dates if dates else ["No data"])
        axis_x.setLabelsColor(Qt.GlobalColor.gray)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelsColor(Qt.GlobalColor.gray)
        axis_y.setLabelFormat("%.0f")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self.trend_chart.chart_view.setChart(chart)

    def _build_payment_chart(self, conn):
        series = QPieSeries()

        rows = conn.execute("""
            SELECT payment_mode, COALESCE(SUM(grand_total),0) as total
            FROM sales WHERE sale_date=date('now')
            GROUP BY payment_mode
        """).fetchall()

        colors_map = {"Cash": "#3fb950", "Card": "#58a6ff", "UPI": "#d29922", "Credit": "#f85149"}
        total = sum(r["total"] for r in rows) or 1

        for r in rows:
            pct = r["total"] / total * 100
            label = f"{r['payment_mode']} ({pct:.0f}%)"
            sl = series.append(label, r["total"])
            color = colors_map.get(r["payment_mode"], "#8b949e")
            sl.setColor(Qt.GlobalColor(0))
            sl.setBrush(Qt.GlobalColor(0))
            # Use QColor from PySide6
            from PySide6.QtGui import QColor
            sl.setBrush(QColor(color))

        if not rows:
            series.append("No sales", 1)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("")
        chart.setBackgroundBrush(Qt.GlobalColor.transparent)
        chart.legend().setLabelColor(Qt.GlobalColor.white)
        series.setLabelsVisible(True)
        for sl in series.slices():
            sl.setLabelColor(Qt.GlobalColor.white)

        self.payment_chart.chart_view.setChart(chart)

    def _build_top_chart(self, conn):
        rows = conn.execute("""
            SELECT COALESCE(f.name, lp.product_name) as item_name,
                   SUM(si.qty) as total_qty
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id AND s.sale_date=date('now')
            LEFT JOIN pumps p ON p.id = si.pump_id
            LEFT JOIN tanks t ON t.id = p.tank_id
            LEFT JOIN fuel_types f ON f.id = t.fuel_type_id
            LEFT JOIN lube_products lp ON lp.id = si.lube_product_id
            GROUP BY item_name
            ORDER BY total_qty DESC
            LIMIT 5
        """).fetchall()

        bar_set = QBarSet("Qty")
        bar_set.setColor(Qt.GlobalColor(0))
        from PySide6.QtGui import QColor
        bar_set.setBrush(QColor("#58a6ff"))

        categories = []
        for r in rows:
            bar_set.append(r["total_qty"])
            item_name = r["item_name"]
            name = (item_name[:12] + "...") if item_name and len(item_name) > 12 else (item_name or "N/A")
            categories.append(name)

        if not rows:
            bar_set.append(0)
            categories.append("No data")

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("")
        chart.setBackgroundBrush(Qt.GlobalColor.transparent)
        chart.legend().setVisible(False)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsColor(Qt.GlobalColor.gray)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelsColor(Qt.GlobalColor.gray)
        axis_y.setLabelFormat("%.0f")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self.top_chart.chart_view.setChart(chart)
