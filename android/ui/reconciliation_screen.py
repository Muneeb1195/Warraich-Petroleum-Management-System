from datetime import date, timedelta

from kivy.uix.screenmanager import Screen
from libs.utils.theme import *
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.metrics import dp

from libs.database.connection import get_connection
from libs.models.fuel import Pump
from libs.utils.formatting import curr
from libs.database.settings import settings


class PumpReadingRow(BoxLayout):
    def __init__(self, pump, opening, closing, **kwargs):
        super().__init__(**kwargs)
        self.pump_id = pump["id"]
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(4)
        self.padding = [dp(6), dp(2)]

        self.add_widget(Label(
            text=f"P{pump['pump_no']}-{pump['fuel_name']}",
            size_hint_x=0.3, halign="left", color=TEXT_PRIMARY, font_size="11sp",
        ))

        self.opening_input = TextInput(
            text=str(opening) if opening else "0",
            input_filter="float", multiline=False,
            size_hint_x=0.2, font_size="11sp",
            foreground_color=TEXT_PRIMARY, background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.opening_input)

        self.closing_input = TextInput(
            text=str(closing) if closing else "0",
            input_filter="float", multiline=False,
            size_hint_x=0.2, font_size="11sp",
            foreground_color=TEXT_PRIMARY, background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.closing_input)

        self.expected_label = Label(text="0", size_hint_x=0.15, color=TEXT_FIELD_LABEL, font_size="11sp")
        self.add_widget(self.expected_label)

        self.variance_label = Label(text="0", size_hint_x=0.15, color=VAL_POSITIVE, font_size="11sp")
        self.add_widget(self.variance_label)

    def update_variance(self, actual_sales):
        try:
            op = float(self.opening_input.text or "0")
            cl = float(self.closing_input.text or "0")
        except ValueError:
            op = 0
            cl = 0
        expected = max(0, cl - op)
        self.expected_label.text = f"{expected:.2f}"
        variance = expected - actual_sales
        color = [0.6, 1, 0.6, 1] if abs(variance) < 0.5 else [1, 0.4, 0.4, 1]
        self.variance_label.text = f"{variance:+.2f}"
        self.variance_label.color = color


class ReconciliationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reading_rows = []

    def on_enter(self):
        self.ids.date_input.text = date.today().isoformat()
        self._rebuild()

    def set_date_today(self):
        self.ids.date_input.text = date.today().isoformat()
        self.on_date_shift_change()

    def set_date_yesterday(self):
        from datetime import timedelta
        self.ids.date_input.text = (date.today() - timedelta(days=1)).isoformat()
        self.on_date_shift_change()

    def _rebuild(self):
        container = self.ids.readings_container
        container.clear_widgets()
        self.reading_rows = []

        header = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(28),
            spacing=dp(4), padding=[dp(6), 0],
        )
        for txt, sx in [("Pump", 0.3), ("Opening", 0.2), ("Closing", 0.2), ("Expected", 0.15), ("Variance", 0.15)]:
            header.add_widget(Label(
                text=txt, size_hint_x=sx, bold=True,
                color=TEXT_SECONDARY, font_size="10sp",
            ))
        container.add_widget(header)

        pumps = Pump.get_with_tank()
        if not pumps:
            container.add_widget(Label(
                text="No pumps found. Add pumps in Inventory first.",
                color=TEXT_AMBER, size_hint_y=None, height=dp(40),
            ))
            return

        sdate = self.ids.date_input.text.strip()
        shift = self.ids.shift_spinner.text

        conn = get_connection()
        existing = {}
        try:
            rows = conn.execute(
                "SELECT pump_id, opening_reading, closing_reading, is_closed FROM shift_readings WHERE date=? AND shift=?",
                (sdate, shift),
            ).fetchall()
            for r in rows:
                existing[r["pump_id"]] = r
        except Exception:
            pass
        finally:
            conn.close()

        for p in pumps:
            prev = existing.get(p["id"], {})
            opening = prev.get("opening_reading", 0) if prev else 0
            closing = prev.get("closing_reading", 0) if prev else 0
            row = PumpReadingRow(p, opening, closing)
            self.reading_rows.append(row)
            container.add_widget(row)

        container.add_widget(Widget(size_hint_y=1))

    def on_date_shift_change(self):
        self._rebuild()

    def start_shift(self):
        sdate = self.ids.date_input.text.strip()
        shift = self.ids.shift_spinner.text
        try:
            conn = get_connection()
            pumps = Pump.get_with_tank()
            count = 0
            for p in pumps:
                existing = conn.execute(
                    "SELECT id FROM shift_readings WHERE date=? AND shift=? AND pump_id=?",
                    (sdate, shift, p["id"]),
                ).fetchone()
                if not existing:
                    conn.execute(
                        "INSERT INTO shift_readings (date, shift, pump_id, opening_reading) VALUES (?,?,?,?)",
                        (sdate, shift, p["id"], 0),
                    )
                    count += 1
            conn.commit()
            conn.close()
        except Exception as e:
            Popup(
                title="Error",
                content=Label(text=f"Failed to start shift: {e}", color=TEXT_ERROR),
                size_hint=(0.7, 0.25),
            ).open()
            return
        Popup(
            title="Shift Started",
            content=Label(text=f"Shift '{shift}' initialized for {count} pumps.", color=TEXT_PRIMARY),
            size_hint=(0.7, 0.25),
        ).open()
        self._rebuild()

    def close_shift(self):
        sdate = self.ids.date_input.text.strip()
        shift = self.ids.shift_spinner.text

        confirm = Popup(
            title="Close Shift",
            content=BoxLayout(orientation="vertical", spacing=dp(8)),
            size_hint=(0.7, 0.3),
        )
        confirm.content.add_widget(Label(
            text=f"Close {shift} shift for {sdate}?\nThis will finalize all pump readings.",
            color=TEXT_PRIMARY, font_size="12sp",
        ))
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(40))
        btn_row.add_widget(Button(
            text="Cancel", background_normal="", background_color=BTN_CANCEL, color=TEXT_PRIMARY,
            on_press=confirm.dismiss,
        ))
        btn_row.add_widget(Button(
            text="Close", background_normal="", background_color=(0.4, 0.15, 0.15, 1), color=TEXT_PRIMARY,
            on_press=lambda *a: (confirm.dismiss(), self._do_close_shift(sdate, shift)),
        ))
        confirm.content.add_widget(btn_row)
        confirm.open()

    def _do_close_shift(self, sdate, shift):
        try:
            conn = get_connection()
            for row in self.reading_rows:
                try:
                    op = float(row.opening_input.text or "0")
                    cl = float(row.closing_input.text or "0")
                except ValueError:
                    continue
                existing = conn.execute(
                    "SELECT id FROM shift_readings WHERE date=? AND shift=? AND pump_id=?",
                    (sdate, shift, row.pump_id),
                ).fetchone()
                if existing:
                    conn.execute(
                        "UPDATE shift_readings SET opening_reading=?, closing_reading=?, is_closed=1 WHERE id=?",
                        (op, cl, existing["id"]),
                    )
                else:
                    conn.execute(
                        "INSERT INTO shift_readings (date, shift, pump_id, opening_reading, closing_reading, is_closed) VALUES (?,?,?,?,?,1)",
                        (sdate, shift, row.pump_id, op, cl),
                    )
            conn.commit()
            conn.close()
        except Exception as e:
            Popup(
                title="Error",
                content=Label(text=f"Failed to close shift: {e}", color=TEXT_ERROR),
                size_hint=(0.7, 0.25),
            ).open()
            return
        Popup(
            title="Shift Closed",
            content=Label(text=f"Shift '{shift}' readings saved.", color=TEXT_PRIMARY),
            size_hint=(0.7, 0.25),
        ).open()

    def reconcile(self):
        conn = get_connection()
        sdate = self.ids.date_input.text.strip()

        sales_map = {}
        try:
            rows = conn.execute("""
                SELECT si.pump_id, SUM(si.qty) as total_qty
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                WHERE si.item_type='fuel' AND s.sale_date=?
                GROUP BY si.pump_id
            """, (sdate,)).fetchall()
            for r in rows:
                sales_map[r["pump_id"]] = r["total_qty"]
        except Exception:
            pass

        lines = [f"Reconciliation - {sdate}", "=" * 30, ""]
        total_expected = 0
        total_sales = 0

        for row in self.reading_rows:
            try:
                op = float(row.opening_input.text or "0")
                cl = float(row.closing_input.text or "0")
            except ValueError:
                continue
            expected = max(0, cl - op)
            actual = sales_map.get(row.pump_id, 0)
            total_expected += expected
            total_sales += actual
            diff = expected - actual
            lines.append(f"Pump: Expected={expected:.2f}L, Sold={actual:.2f}L, Diff={diff:+.2f}L")

        lines.append("")
        lines.append(f"Total Expected: {total_expected:.2f}L")
        lines.append(f"Total Sold: {total_sales:.2f}L")
        lines.append(f"Variance: {total_expected - total_sales:+.2f}L")

        conn.close()

        msg = "\n".join(lines)
        Popup(
            title="Reconciliation",
            content=Label(text=msg, color=TEXT_PRIMARY, font_size="12sp"),
            size_hint=(0.85, 0.65),
        ).open()

    def go_back(self):
        self.manager.current = "main"
