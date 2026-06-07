from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QGridLayout, QFrame, QPushButton)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QFont, QPainter, QDesktopServices
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

        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        quick_sale_btn = QPushButton(" Quick Sale")
        quick_sale_btn.setObjectName("successBtn")
        quick_sale_btn.setMinimumHeight(50)
        quick_sale_btn.setStyleSheet(
            "font-size: 15px; font-weight: bold; background-color: #238636; "
            "color: white; border-radius: 8px; padding: 10px 24px;"
        )
        quick_sale_btn.setToolTip("Record a cash sale quickly without meter readings or items")
        quick_sale_btn.clicked.connect(self._quick_sale)
        actions_layout.addWidget(quick_sale_btn)

        close_day_btn = QPushButton(" Close Day")
        close_day_btn.setObjectName("warningBtn")
        close_day_btn.setMinimumHeight(50)
        close_day_btn.setStyleSheet(
            "font-size: 15px; font-weight: bold; background-color: #d29922; "
            "color: #0d1117; border-radius: 8px; padding: 10px 24px;"
        )
        close_day_btn.setToolTip("View end-of-day summary with totals and print report")
        close_day_btn.clicked.connect(self._close_day)
        actions_layout.addWidget(close_day_btn)

        actions_layout.addStretch()
        layout.addSpacing(8)
        layout.addLayout(actions_layout)

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

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(30000)
        self._refresh_timer.timeout.connect(self.refresh)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._refresh_timer.stop()

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

    def _quick_sale(self):
        from ui.sales.quick_sale import QuickSaleDialog
        dlg = QuickSaleDialog(self)
        if dlg.exec():
            self.refresh()

    def _close_day(self):
        conn = get_connection()
        today = conn.execute(
            "SELECT COALESCE(SUM(grand_total),0) as sales, COUNT(*) as invoices FROM sales WHERE sale_date=date('now')"
        ).fetchone()
        expenses = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as t FROM expenses WHERE expense_date=date('now')"
        ).fetchone()["t"]
        payment_split = conn.execute("""
            SELECT payment_mode, COALESCE(SUM(grand_total),0) as total
            FROM sales WHERE sale_date=date('now')
            GROUP BY payment_mode
        """).fetchall()
        profit = today["sales"] - expenses
        conn.close()

        lines = [
            f"Date: {datetime.now().strftime('%d/%m/%Y')}",
            "",
            f"Total Sales:     {curr(today['sales'])}",
            f"Total Expenses:  {curr(expenses)}",
            f"Today's Profit:  {curr(profit)}",
            f"Invoices:        {today['invoices']}",
            "",
            "Payment Split:",
        ]
        for r in payment_split:
            lines.append(f"  {r['payment_mode']}: {curr(r['total'])}")

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
        dlg = QDialog(self)
        dlg.setWindowTitle("Day Closing Summary")
        dlg.setMinimumSize(400, 450)
        dlg.setModal(True)
        dl = QVBoxLayout(dlg)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText("\n".join(lines))
        text.setStyleSheet("font-size: 14px; padding: 16px; background-color: #161b22; color: #c9d1d9; border: none;")
        dl.addWidget(text)

        btn_row = QHBoxLayout()
        print_btn = QPushButton("Print Report")
        print_btn.clicked.connect(lambda: self._print_day_close(today, expenses, profit, payment_split))
        btn_row.addWidget(print_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)
        dl.addLayout(btn_row)
        dlg.exec()

    def _print_day_close(self, today, expenses, profit, payment_split):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from pathlib import Path

        filename = f"reports/dayclose_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = Path(__file__).resolve().parent.parent.parent / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(filepath), pagesize=A4)
        w, h = A4

        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, h - 50, settings.business_name())
        c.setFont("Helvetica", 12)
        c.drawString(50, h - 75, "Day Closing Report")
        c.drawString(50, h - 95, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
        c.line(50, h - 105, w - 50, h - 105)

        y = h - 140
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Summary")
        c.setFont("Helvetica", 13)
        y -= 30
        c.drawString(50, y, f"Total Sales:       {curr(today['sales'])}")
        c.drawRightString(w - 50, y, f"Invoices: {today['invoices']}")
        y -= 25
        c.drawString(50, y, f"Total Expenses:    {curr(expenses)}")
        y -= 25
        c.drawString(50, y, f"Today's Profit:    {curr(profit)}")

        y -= 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Payment Split")
        c.line(50, y - 5, w - 50, y - 5)
        c.setFont("Helvetica", 13)
        y -= 30
        for r in payment_split:
            c.drawString(50, y, f"{r['payment_mode']}:")
            c.drawRightString(w - 50, y, curr(r['total']))
            y -= 25

        c.save()
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(filepath)))
        QMessageBox.information(self, "Report Saved", f"Day close report saved to:\n{filename}")
