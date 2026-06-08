from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty
from kivy.clock import Clock

from libs.utils.theme import *
from libs.database.connection import get_connection
from libs.utils.formatting import curr


class StatCard(BoxLayout):
    icon = StringProperty("")
    card_title = StringProperty("")
    card_value = StringProperty("")
    trend_text = StringProperty("")
    trend_color = ListProperty([0.6, 0.6, 0.6, 1])
    accent = StringProperty("#58a6ff")
    accent_rgba = ListProperty([0.35, 0.65, 1, 1])
    value_color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(90)
        self.padding = [dp(12), dp(8)]
        self.spacing = dp(12)
        self.accent_rgba = self._color_for_accent(self.accent)

    @staticmethod
    def _color_for_accent(accent):
        colors = {
            "#58a6ff": [0.35, 0.65, 1, 1],
            "#3fb950": [0.25, 0.73, 0.32, 1],
            "#d29922": [0.82, 0.6, 0.13, 1],
            "#f85149": [0.97, 0.32, 0.29, 1],
        }
        return colors.get(accent, [0.35, 0.65, 1, 1])


class DashboardScreen(Screen):
    def on_enter(self):
        self.refresh()

    def refresh(self):
        try:
            conn = get_connection()

            today = conn.execute(
                "SELECT COALESCE(SUM(grand_total),0) FROM sales WHERE sale_date=date('now')"
            ).fetchone()[0]
            self.ids.today_sales_card.card_value = curr(today)

            yesterday = conn.execute(
                "SELECT COALESCE(SUM(grand_total),0) FROM sales WHERE sale_date=date('now','-1 day')"
            ).fetchone()[0]
            self._set_trend(self.ids.today_sales_card, today, yesterday)

            month = conn.execute(
                "SELECT COALESCE(SUM(grand_total),0) FROM sales WHERE strftime('%Y-%m', sale_date)=strftime('%Y-%m', 'now')"
            ).fetchone()[0]
            self.ids.month_sales_card.card_value = curr(month)

            today_exp = conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE expense_date=date('now')"
            ).fetchone()[0]
            self.ids.expenses_card.card_value = curr(today_exp)

            tank_count = conn.execute("SELECT COUNT(*) FROM tanks").fetchone()[0]
            self.ids.tank_card.card_value = str(tank_count)

            lube_count = conn.execute("SELECT COUNT(*) FROM lube_products").fetchone()[0]
            self.ids.lube_card.card_value = str(lube_count)

            staff_count = conn.execute(
                "SELECT COUNT(*) FROM employees WHERE is_active=1"
            ).fetchone()[0]
            self.ids.staff_card.card_value = str(staff_count)

            pending = conn.execute(
                "SELECT COALESCE(SUM(net_salary),0) FROM payroll WHERE paid=0"
            ).fetchone()[0]
            self.ids.payroll_card.card_value = curr(pending)

            profit = today - today_exp
            profit_color = VAL_PROFIT_GREEN if profit >= 0 else VAL_NEGATIVE
            self.ids.profit_card.card_value = curr(profit)
            self.ids.profit_card.value_color = profit_color

            yesterday_exp = conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE expense_date=date('now','-1 day')"
            ).fetchone()[0]
            yesterday_profit = yesterday - yesterday_exp
            self._set_trend(self.ids.profit_card, profit, yesterday_profit)

            conn.close()
        except Exception:
            pass

    @staticmethod
    def _set_trend(card, current, previous):
        if previous <= 0 and current > 0:
            card.trend_text = "↑ New"
            card.trend_color = VAL_POSITIVE
        elif current > previous:
            diff = current - previous
            card.trend_text = f"↑ {curr(diff)}"
            card.trend_color = VAL_POSITIVE
        elif current < previous:
            diff = previous - current
            card.trend_text = f"↓ {curr(diff)}"
            card.trend_color = VAL_NEGATIVE
        else:
            card.trend_text = "— Same"
            card.trend_color = TEXT_DIM

    def quick_sale(self):
        Clock.schedule_once(lambda *a: setattr(self.manager, 'current', "pos"))

    def close_day(self):
        conn = get_connection()
        today_data = conn.execute(
            "SELECT COALESCE(SUM(grand_total),0) as sales, COUNT(*) as invoices FROM sales WHERE sale_date=date('now')"
        ).fetchone()
        expenses = conn.execute(
            "SELECT COALESCE(SUM(amount),0) as t FROM expenses WHERE expense_date=date('now')"
        ).fetchone()["t"]
        payment_rows = conn.execute("""
            SELECT payment_mode, COALESCE(SUM(grand_total),0) as total
            FROM sales WHERE sale_date=date('now')
            GROUP BY payment_mode
        """).fetchall()
        conn.close()

        profit = today_data["sales"] - expenses

        lines = [f"Date: {datetime.now().strftime('%d/%m/%Y')}", ""]
        lines.append(f"Total Sales:     {curr(today_data['sales'])}")
        lines.append(f"Total Expenses:  {curr(expenses)}")
        lines.append(f"Today's Profit:  {curr(profit)}")
        lines.append(f"Invoices:        {today_data['invoices']}")
        lines.append("")
        lines.append("Payment Split:")
        for r in payment_rows:
            lines.append(f"  {r['payment_mode']}: {curr(r['total'])}")

        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        msg = "\n".join(lines)
        content.add_widget(Label(text=msg, color=TEXT_PRIMARY, font_size="13sp", halign="left"))
        close_btn = Button(
            text="Close", size_hint_y=None, height=dp(40),
            background_normal="", background_color=BTN_CANCEL, color=(1,1,1,1),
        )
        content.add_widget(close_btn)
        popup = Popup(title="Day Closing Summary", content=content, size_hint=(0.75, 0.6))
        close_btn.bind(on_press=lambda *a: popup.dismiss())
        popup.open()

    def go_back(self):
        Clock.schedule_once(lambda *a: setattr(self.manager, 'current', "main"))
