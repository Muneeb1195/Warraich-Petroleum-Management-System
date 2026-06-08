from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.metrics import dp
from kivy.clock import Clock

from libs.utils.theme import *
from libs.models.sale import Sale
from libs.models.customer import Customer
from libs.database.settings import settings
from libs.utils.printer import NetworkPrinter
from libs.models.fuel import Pump
from libs.models.lube import LubeProduct
from libs.database.settings import settings
from libs.utils.formatting import curr


class NumberPadPopup(Popup):
    def __init__(self, value="0", callback=None, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self._value = value
        self._build()

    def _build(self):
        self.title = "Enter value"
        self.size_hint = (0.7, 0.6)
        self.background = ""
        self.background_color = (0.09, 0.09, 0.12, 1)
        self.separator_height = 0

        root = BoxLayout(orientation="vertical", spacing=dp(4), padding=[dp(8), dp(4)])
        self.display = Label(
            text=self._value,
            size_hint_y=None, height=dp(48),
            font_size="26sp", bold=True,
            color=TEXT_PRIMARY, halign="center",
        )
        root.add_widget(self.display)

        grid = GridLayout(cols=3, spacing=dp(4), size_hint_y=None, height=dp(220))
        for row in [("7","8","9"), ("4","5","6"), ("1","2","3")]:
            for ch in row:
                btn = Button(
                    text=ch, font_size="18sp",
                    background_normal="", background_color=BTN_NAV, color=TEXT_PRIMARY,
                )
                btn.bind(on_press=lambda *a, c=ch: self._append(c))
                grid.add_widget(btn)
        # last row: 0, ., ⌫
        for ch, cls in [("0", BTN_NAV), (".", BTN_NAV), ("⌫", BTN_DANGER)]:
            btn = Button(
                text=ch, font_size="18sp",
                background_normal="", background_color=cls, color=TEXT_PRIMARY,
            )
            if ch == "⌫":
                btn.bind(on_press=lambda *a: self._backspace())
            else:
                btn.bind(on_press=lambda *a, c=ch: self._append(c))
            grid.add_widget(btn)
        root.add_widget(grid)

        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_row.add_widget(Button(
            text="Clear", font_size="14sp",
            background_normal="", background_color=BTN_CANCEL, color=TEXT_PRIMARY,
            on_press=lambda *a: self._clear(),
        ))
        btn_row.add_widget(Button(
            text="OK", font_size="14sp",
            background_normal="", background_color=BTN_PRIMARY, color=TEXT_PRIMARY,
            on_press=lambda *a: self._confirm(),
        ))
        root.add_widget(btn_row)
        self.content = root

    def _append(self, char):
        if char == "." and "." in self._value:
            return
        if self._value == "0" and char != ".":
            self._value = char
        else:
            self._value += char
        self.display.text = self._value

    def _backspace(self):
        self._value = self._value[:-1] or "0"
        self.display.text = self._value

    def _clear(self):
        self._value = "0"
        self.display.text = self._value

    def _confirm(self):
        if self.callback:
            self.callback(self._value)
        self.dismiss()


class PumpCard(BoxLayout):
    pump_data = ObjectProperty(None)
    opening_btn = ObjectProperty(None)
    closing_btn = ObjectProperty(None)
    qty_label = ObjectProperty(None)

    def __init__(self, pump, **kwargs):
        super().__init__(**kwargs)
        self.pump_data = pump
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(60)
        self.spacing = dp(6)
        self.padding = [dp(6), dp(4)]

        fuel_name = pump["fuel_name"]
        rate = settings.fuel_rate(fuel_name.lower())

        name_lbl = Label(
            text=f"P{pump['pump_no']}-{fuel_name}",
            size_hint_x=0.28,
            halign="left",
            color=TEXT_PRIMARY,
            font_size="12sp",
            text_size=(None, None),
        )
        name_lbl.bind(size=lambda s, ws: setattr(s, "text_size", (s.width, None)))
        self.add_widget(name_lbl)

        rate_lbl = Label(
            text=f"{curr(rate)}/L",
            size_hint_x=0.12,
            color=TEXT_SECONDARY,
            font_size="11sp",
        )
        self.add_widget(rate_lbl)

        self._opening = 0.0
        self._closing = 0.0

        self.opening_btn = Button(
            text="Open",
            size_hint_x=0.15,
            background_normal="",
            background_color=BTN_NAV,
            color=TEXT_SECONDARY,
            font_size="10sp",
        )
        self.opening_btn.bind(on_press=self._open_opening_pad)
        self.add_widget(self.opening_btn)

        self.closing_btn = Button(
            text="Close",
            size_hint_x=0.15,
            background_normal="",
            background_color=BTN_NAV,
            color=TEXT_SECONDARY,
            font_size="10sp",
        )
        self.closing_btn.bind(on_press=self._open_closing_pad)
        self.add_widget(self.closing_btn)

        self.qty_label = Label(
            text="0.00 L",
            size_hint_x=0.14,
            color=VAL_POSITIVE,
            font_size="11sp",
        )
        self.add_widget(self.qty_label)

        add_btn = Button(
            text="Add",
            size_hint_x=0.12,
            background_normal="",
            background_color=BTN_PRIMARY,
            color=TEXT_PRIMARY,
            font_size="11sp",
        )
        add_btn.bind(on_press=self._on_add)
        self.add_widget(add_btn)

    def _open_opening_pad(self, *args):
        pad = NumberPadPopup(
            value=str(self._opening),
            callback=self._set_opening,
        )
        pad.open()

    def _set_opening(self, val):
        v = float(val or "0")
        self._opening = v
        self.opening_btn.text = val
        self.opening_btn.color = TEXT_PRIMARY
        self.opening_btn.background_color = BTN_INFO
        self._update_qty()

    def _open_closing_pad(self, *args):
        pad = NumberPadPopup(
            value=str(self._closing),
            callback=self._set_closing,
        )
        pad.open()

    def _set_closing(self, val):
        v = float(val or "0")
        self._closing = v
        self.closing_btn.text = val
        self.closing_btn.color = TEXT_PRIMARY
        self.closing_btn.background_color = BTN_INFO
        self._update_qty()

    def _get_qty(self):
        return max(0, self._closing - self._opening)

    def _update_qty(self, *args):
        qty = self._get_qty()
        self.qty_label.text = f"{qty:.2f} L"

    def _on_add(self, *args):
        qty = self._get_qty()
        if qty <= 0:
            self._show_error("Closing reading must be greater than opening reading.")
            return
        rate = settings.fuel_rate(self.pump_data["fuel_name"].lower())
        if rate <= 0:
            self._show_error(f"Set {self.pump_data['fuel_name']} rate in Settings first.")
            return
        amount = qty * rate
        item = {
            "type": "fuel",
            "pump_id": self.pump_data["id"],
            "name": f"{self.pump_data['fuel_name']} - Pump {self.pump_data['pump_no']}",
            "opening": self._opening,
            "closing": self._closing,
            "qty": qty,
            "rate": rate,
            "amount": amount,
        }
        screen = self._get_pos_screen()
        if screen:
            screen.add_to_cart(item)

        self._opening = 0.0
        self._closing = 0.0
        self.opening_btn.text = "Open"
        self.opening_btn.color = TEXT_SECONDARY
        self.opening_btn.background_color = BTN_NAV
        self.closing_btn.text = "Close"
        self.closing_btn.color = TEXT_SECONDARY
        self.closing_btn.background_color = BTN_NAV
        self._update_qty()

    def _show_error(self, msg):
        screen = self._get_pos_screen()
        if screen:
            screen.show_error(msg)

    def _get_pos_screen(self):
        parent = self.parent
        while parent:
            if isinstance(parent, PosScreen):
                return parent
            parent = parent.parent
        return None


class LubeCard(BoxLayout):
    lube_data = ObjectProperty(None)
    qty_btn = ObjectProperty(None)

    def __init__(self, lube, **kwargs):
        super().__init__(**kwargs)
        self.lube_data = lube
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(52)
        self.spacing = dp(6)
        self.padding = [dp(6), dp(4)]

        brand_lbl = Label(
            text=lube["brand"],
            size_hint_x=0.18,
            halign="left",
            color=TEXT_PRIMARY,
            font_size="11sp",
        )
        self.add_widget(brand_lbl)

        name_lbl = Label(
            text=lube["product_name"],
            size_hint_x=0.25,
            halign="left",
            color=TEXT_PRIMARY,
            font_size="11sp",
        )
        self.add_widget(name_lbl)

        price_lbl = Label(
            text=curr(lube["selling_price"]),
            size_hint_x=0.12,
            color=VAL_POSITIVE,
            font_size="11sp",
        )
        self.add_widget(price_lbl)

        stock_lbl = Label(
            text=f"{lube['stock_qty']:,.2f} {lube['unit']}",
            size_hint_x=0.17,
            color=TEXT_SECONDARY,
            font_size="11sp",
        )
        self.add_widget(stock_lbl)

        self._qty = 1.0
        self.qty_btn = Button(
            text="1",
            size_hint_x=0.12,
            background_normal="",
            background_color=BTN_NAV,
            color=TEXT_SECONDARY,
            font_size="12sp",
        )
        self.qty_btn.bind(on_press=self._open_qty_pad)
        self.add_widget(self.qty_btn)

        add_btn = Button(
            text="Add",
            size_hint_x=0.12,
            background_normal="",
            background_color=BTN_PRIMARY,
            color=TEXT_PRIMARY,
            font_size="11sp",
        )
        add_btn.bind(on_press=self._on_add)
        self.add_widget(add_btn)

    def _open_qty_pad(self, *args):
        pad = NumberPadPopup(
            value=str(self._qty),
            callback=self._set_qty,
        )
        pad.open()

    def _set_qty(self, val):
        try:
            v = float(val or "0")
        except ValueError:
            v = 1
        if v <= 0:
            v = 1
        self._qty = v
        self.qty_btn.text = val
        self.qty_btn.color = TEXT_PRIMARY
        self.qty_btn.background_color = BTN_INFO

    def _on_add(self, *args):
        qty = self._qty
        if qty <= 0:
            return
        if qty > self.lube_data["stock_qty"]:
            self._show_error(f"Only {self.lube_data['stock_qty']:.2f} {self.lube_data['unit']} in stock.")
            return
        amount = qty * self.lube_data["selling_price"]
        item = {
            "type": "lube",
            "lube_id": self.lube_data["id"],
            "name": f"{self.lube_data['brand']} - {self.lube_data['product_name']}",
            "qty": qty,
            "rate": self.lube_data["selling_price"],
            "amount": amount,
        }
        screen = self._get_pos_screen()
        if screen:
            screen.add_to_cart(item)

    def _show_error(self, msg):
        screen = self._get_pos_screen()
        if screen:
            screen.show_error(msg)

    def _get_pos_screen(self):
        parent = self.parent
        while parent:
            if isinstance(parent, PosScreen):
                return parent
            parent = parent.parent
        return None


class CartItem(BoxLayout):
    idx = NumericProperty(0)
    item_data = ObjectProperty(None)

    def __init__(self, idx, item, **kwargs):
        super().__init__(**kwargs)
        self.idx = idx
        self.item_data = item
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(36)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(2)]

        name_lbl = Label(
            text=item["name"],
            size_hint_x=0.32,
            halign="left",
            color=TEXT_PRIMARY,
            font_size="10sp",
        )
        self.add_widget(name_lbl)

        qty_lbl = Label(
            text=f"{item['qty']:,.2f}",
            size_hint_x=0.16,
            color=TEXT_FIELD_LABEL,
            font_size="10sp",
        )
        self.add_widget(qty_lbl)

        rate_lbl = Label(
            text=curr(item["rate"]),
            size_hint_x=0.16,
            color=TEXT_FIELD_LABEL,
            font_size="10sp",
        )
        self.add_widget(rate_lbl)

        amt_lbl = Label(
            text=curr(item["amount"]),
            size_hint_x=0.2,
            color=VAL_POSITIVE,
            font_size="10sp",
        )
        self.add_widget(amt_lbl)

        del_btn = Button(
            text="X",
            size_hint_x=0.12,
            background_normal="",
            background_color=BTN_DANGER,
            color=TEXT_PRIMARY,
            font_size="10sp",
        )
        del_btn.bind(on_press=self._on_delete)
        self.add_widget(del_btn)

    def _on_delete(self, *args):
        screen = self._get_pos_screen()
        if screen:
            screen.remove_cart_item(self.idx)

    def _get_pos_screen(self):
        parent = self.parent
        while parent:
            if isinstance(parent, PosScreen):
                return parent
            parent = parent.parent
        return None


class PosScreen(Screen):
    _payment_mode = StringProperty("Cash")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cart_items = []
        self._last_sale_id = None
        self._last_inv_no = None

    def on_enter(self):
        self._rebuild_fuel_tab()
        self._rebuild_lube_tab()
        self._rebuild_customer_spinner()
        self.ids.gst_input.text = str(settings.default_gst_rate())
        self._refresh_cart()

    def set_payment_mode(self, mode):
        self._payment_mode = mode

    def _quick_sale(self, fuel_name, amount):
        rate = settings.fuel_rate(fuel_name)
        if rate <= 0:
            self.show_error(f"Set {fuel_name.title()} rate in Settings first.")
            return
        qty = amount / rate
        item = {
            "type": "fuel",
            "pump_id": 0,
            "name": f"{fuel_name.title()} ₹{amount}",
            "opening": 0,
            "closing": 0,
            "qty": round(qty, 2),
            "rate": rate,
            "amount": amount,
        }
        self.add_to_cart(item)

    def _rebuild_fuel_tab(self):
        container = self.ids.fuel_container
        container.clear_widgets()
        pumps = Pump.get_with_tank()

        fuel_types = {}
        for p in pumps:
            ft = p["fuel_name"].lower()
            if ft not in fuel_types:
                fuel_types[ft] = settings.fuel_rate(ft)

        if fuel_types:
            quick_row = BoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(36),
                spacing=dp(4), padding=[dp(4), 0],
            )
            for fuel_name in fuel_types:
                rate = fuel_types[fuel_name]
                if rate <= 0:
                    continue
                for amt in [200, 500, 1000]:
                    btn = Button(
                        text=f"{fuel_name.title()} ₹{amt}",
                        font_size="10sp",
                        background_normal="",
                        background_color=BTN_QUICK_SALE,
                        color=TEXT_PRIMARY,
                    )
                    btn.bind(on_press=lambda *a, fn=fuel_name, a2=amt: self._quick_sale(fn, a2))
                    quick_row.add_widget(btn)
            container.add_widget(quick_row)

        if not pumps:
            container.add_widget(Label(
                text="No pumps configured. Add pumps in Inventory first.",
                color=TEXT_AMBER,
                size_hint_y=None,
                height=dp(40),
            ))
        else:
            for p in pumps:
                container.add_widget(PumpCard(p))
        container.add_widget(Widget(size_hint_y=1))

    def _rebuild_lube_tab(self):
        container = self.ids.lube_container
        container.clear_widgets()
        lubes = LubeProduct.get_all("brand")
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28),
            spacing=dp(6),
            padding=[dp(8), 0],
        )
        for txt, sx in [("Brand", 0.18), ("Product", 0.25), ("Price", 0.12), ("Stock", 0.17), ("Qty", 0.12), ("", 0.12)]:
            h = Label(
                text=txt,
                size_hint_x=sx,
                bold=True,
                color=TEXT_SECONDARY,
                font_size="11sp",
            )
            header.add_widget(h)
        container.add_widget(header)
        if not lubes:
            container.add_widget(Label(
                text="No lubricants available. Add them in Inventory first.",
                color=TEXT_AMBER, size_hint_y=None, height=dp(40),
            ))
            container.add_widget(Widget(size_hint_y=1))
            return
        for l in lubes:
            container.add_widget(LubeCard(l))
        container.add_widget(Widget(size_hint_y=1))

    def _rebuild_customer_spinner(self):
        spinner = self.ids.customer_spinner
        spinner.values = ["Walk-in Customer"]
        self._customer_map = {"Walk-in Customer": None}
        customers = Customer.get_all("name")
        for c in customers:
            label = f"{c['name']} ({c['phone']})" if c["phone"] else c["name"]
            spinner.values.append(label)
            self._customer_map[label] = c["id"]
        spinner.text = "Walk-in Customer"

    def add_to_cart(self, item):
        self.cart_items.append(item)
        self._refresh_cart()

    def remove_cart_item(self, idx):
        if 0 <= idx < len(self.cart_items):
            self.cart_items.pop(idx)
            self._refresh_cart()

    def _refresh_cart(self):
        container = self.ids.cart_container
        container.clear_widgets()
        self.ids.cart_badge.text = f"Cart ({len(self.cart_items)})"
        taxable = 0
        for i, item in enumerate(self.cart_items):
            container.add_widget(CartItem(i, item))
            taxable += item["amount"]

        try:
            gst_rate = float(self.ids.gst_input.text or "0")
        except ValueError:
            gst_rate = 0

        half_gst = round(taxable * gst_rate / 100 / 2, 2)
        total = taxable + half_gst * 2
        gt = round(total)
        round_off = round(gt - total, 2)

        self.ids.taxable_label.text = curr(taxable)
        self.ids.cgst_label.text = curr(half_gst)
        self.ids.sgst_label.text = curr(half_gst)
        self.ids.total_label.text = curr(total)
        self.ids.round_off_label.text = curr(round_off)
        self.ids.grand_total_label.text = curr(gt)

        container.add_widget(Widget(size_hint_y=1))

    def on_gst_change(self):
        self._refresh_cart()

    def _clear_cart(self, silent=False):
        if not silent and self.cart_items:
            confirm = Popup(
                title="Clear Cart",
                content=Label(text="Clear entire cart?", color=TEXT_PRIMARY),
                size_hint=(0.6, 0.3),
            )
            btn_row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(40))
            btn_row.add_widget(Button(
                text="Cancel", background_normal="", background_color=BTN_CANCEL, color=TEXT_PRIMARY,
                on_press=confirm.dismiss,
            ))
            btn_row.add_widget(Button(
                text="Clear", background_normal="", background_color=BTN_DANGER_VARIANT, color=TEXT_PRIMARY,
                on_press=lambda *a: (confirm.dismiss(), self._do_clear_cart()),
            ))
            confirm.content = BoxLayout(orientation="vertical", spacing=dp(8))
            confirm.content.add_widget(Label(text="Clear entire cart?", color=TEXT_PRIMARY))
            confirm.content.add_widget(btn_row)
            confirm.open()
        else:
            self._do_clear_cart()

    def _do_clear_cart(self):
        self.cart_items.clear()
        self._refresh_cart()

    def show_error(self, msg):
        popup = Popup(
            title="Error",
            content=Label(text=msg, color=TEXT_ERROR),
            size_hint=(0.7, 0.3),
        )
        popup.open()

    def show_info(self, title, msg):
        popup = Popup(
            title=title,
            content=Label(text=msg, color=TEXT_PRIMARY),
            size_hint=(0.8, 0.4),
        )
        popup.open()

    def show_toast(self, msg):
        toast = Popup(
            title="",
            content=Label(text=msg, color=VAL_POSITIVE, font_size="14sp"),
            size_hint=(0.6, 0.15),
            background="",
            background_color=(0.09, 0.09, 0.12, 0.95),
            auto_dismiss=False,
        )
        toast.open()
        Clock.schedule_once(lambda *a: toast.dismiss(), 2)

    def _checkout(self):
        if not self.cart_items:
            self.show_error("Cart is empty.")
            return

        customer_label = self.ids.customer_spinner.text
        customer_id = self._customer_map.get(customer_label)
        payment_mode = self._payment_mode

        try:
            gst_rate = float(self.ids.gst_input.text or "0")
        except ValueError:
            gst_rate = 0

        sale_id, inv_no = Sale.create(
            customer_id=customer_id,
            payment_mode=payment_mode,
            gst_rate=gst_rate,
        )

        for item in self.cart_items:
            if item["type"] == "fuel":
                Sale.add_fuel_item(
                    sale_id, item["pump_id"],
                    item["opening"], item["closing"], item["rate"],
                )
            else:
                Sale.add_lube_item(sale_id, item["lube_id"], item["qty"], item["rate"])
                LubeProduct.adjust_stock(item["lube_id"], -item["qty"])

        totals = Sale.calculate_totals(sale_id)
        if not totals:
            self.show_error("Sale was created but totals could not be calculated.")
            return

        if payment_mode == "Credit" and customer_id:
            Customer.update_balance(customer_id, totals["grand_total"])

        self._last_sale_id = sale_id
        self._last_inv_no = inv_no

        msg = (
            f"Invoice: {inv_no}\n\n"
            f"Taxable: {curr(totals['taxable'])}\n"
            f"CGST: {curr(totals['cgst'])}\n"
            f"SGST: {curr(totals['sgst'])}\n"
            f"Grand Total: {curr(totals['grand_total'])}\n\n"
            f"Payment: {payment_mode}"
        )

        popup_content = BoxLayout(orientation="vertical", spacing=dp(8))
        popup_content.add_widget(Label(text=msg, color=TEXT_PRIMARY))
        top_btn_row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(40))
        top_btn_row.add_widget(Button(
            text="OK", background_normal="", background_color=BTN_CANCEL, color=TEXT_PRIMARY,
            on_press=lambda *a: popup.dismiss(),
        ))
        top_btn_row.add_widget(Button(
            text="Save PDF", background_normal="", background_color=BTN_INFO, color=TEXT_PRIMARY,
            on_press=lambda *a: (
                popup.dismiss(),
                self._save_pdf(inv_no, totals, payment_mode, customer_id),
            ),
        ))
        popup_content.add_widget(top_btn_row)
        bot_btn_row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(40))
        bot_btn_row.add_widget(Widget())
        bot_btn_row.add_widget(Button(
            text="Print Receipt", background_normal="", background_color=BTN_SECONDARY, color=TEXT_PRIMARY,
            on_press=lambda *a: (
                popup.dismiss(),
                self._print_receipt(inv_no, totals, payment_mode, customer_id),
            ),
        ))
        bot_btn_row.add_widget(Widget())
        popup_content.add_widget(bot_btn_row)

        popup = Popup(
            title="Sale Complete",
            content=popup_content,
            size_hint=(0.8, 0.5),
        )
        popup.open()

        self._clear_cart(silent=True)

    def _print_receipt(self, inv_no, totals, payment_mode, customer_id):
        host = settings.printer_host()
        if not host:
            self.show_error("No printer IP configured. Set it in Settings.")
            return
        port = settings.printer_port()

        from datetime import date
        sale_data = {
            "invoice": inv_no,
            "date": date.today().isoformat(),
            "payment_mode": payment_mode,
            "items": [],
            "taxable_display": f"Rs {totals['taxable']:,.2f}",
            "cgst_display": f"Rs {totals['cgst']:,.2f}",
            "sgst_display": f"Rs {totals['sgst']:,.2f}",
            "grand_total_display": f"Rs {totals['grand_total']:,.2f}",
        }
        for item in self.cart_items:
            sale_data["items"].append({
                "name": item.get("name", ""),
                "qty_display": f"{item.get('qty', 0):.1f}L" if item.get("type") == "fuel" else f"{item.get('qty', 0):.0f}",
                "rate_display": f"Rs {item.get('rate', 0):,.2f}",
                "amount_display": f"Rs {item.get('amount', 0):,.2f}",
            })

        business_info = {
            "name": settings.business_name(),
            "address": settings.business_address(),
            "phone": settings.business_phone(),
            "gstin": settings.gstin(),
        }

        try:
            printer = NetworkPrinter(host, port)
            printer.connect()
            printer.print_receipt(sale_data, business_info)
            printer.disconnect()
            self.show_error("Receipt printed.")
        except Exception as e:
            self.show_error(f"Print failed: {e}")

    def _save_pdf(self, inv_no, totals, payment_mode, customer_id=None):
        from libs.models.customer import Customer
        cname = ""
        if customer_id:
            c = Customer.get_by_id(customer_id)
            if c:
                cname = c.get("name", "")
        sale_data = {
            "invoice": inv_no,
            "items": [],
            "taxable_display": f"Rs {totals['taxable']:,.2f}",
            "cgst_display": f"Rs {totals['cgst']:,.2f}",
            "sgst_display": f"Rs {totals['sgst']:,.2f}",
            "grand_total_display": f"Rs {totals['grand_total']:,.2f}",
        }
        for item in self.cart_items:
            sale_data["items"].append({
                "name": item.get("name", ""),
                "qty_display": f"{item.get('qty', 0):.1f}L" if item.get("type") == "fuel" else f"{item.get('qty', 0):.0f}",
                "rate_display": f"Rs {item.get('rate', 0):,.2f}",
                "amount_display": f"Rs {item.get('amount', 0):,.2f}",
            })
        from libs.utils.invoice_pdf import generate_invoice
        try:
            path = generate_invoice(inv_no, sale_data["items"], sale_data, payment_mode, cname)
            self.show_error(f"Invoice saved:\n{path.name}")
        except Exception as e:
            self.show_error(f"Invoice failed: {e}")

    def go_back(self):
        self.manager.current = "main"
