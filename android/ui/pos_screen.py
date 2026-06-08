from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, ObjectProperty
from kivy.metrics import dp

from libs.models.sale import Sale
from libs.models.customer import Customer
from libs.models.fuel import Pump
from libs.models.lube import LubeProduct
from libs.database.settings import settings
from libs.utils.formatting import curr


class PumpCard(BoxLayout):
    pump_data = ObjectProperty(None)
    opening_text = ObjectProperty(None)
    closing_text = ObjectProperty(None)
    qty_label = ObjectProperty(None)

    def __init__(self, pump, **kwargs):
        super().__init__(**kwargs)
        self.pump_data = pump
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(60)
        self.spacing = dp(8)
        self.padding = [dp(8), dp(4)]

        fuel_name = pump["fuel_name"]
        rate = settings.fuel_rate(fuel_name.lower())

        name_lbl = Label(
            text=f"Pump {pump['pump_no']} - {fuel_name}",
            size_hint_x=0.3,
            halign="left",
            color=(1, 1, 1, 1),
            text_size=(None, None),
        )
        name_lbl.bind(size=lambda s, ws: setattr(s, "text_size", (s.width, None)))
        self.add_widget(name_lbl)

        rate_lbl = Label(
            text=f"{curr(rate)}/L",
            size_hint_x=0.12,
            color=(0.6, 0.6, 0.6, 1),
        )
        self.add_widget(rate_lbl)

        self.opening_text = TextInput(
            text="0",
            input_filter="float",
            multiline=False,
            size_hint_x=0.15,
            hint_text="Open",
            foreground_color=(1, 1, 1, 1),
            background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.opening_text)

        self.closing_text = TextInput(
            text="0",
            input_filter="float",
            multiline=False,
            size_hint_x=0.15,
            hint_text="Close",
            foreground_color=(1, 1, 1, 1),
            background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.closing_text)

        self.qty_label = Label(
            text="0.00 L",
            size_hint_x=0.1,
            color=(0.6, 1, 0.6, 1),
        )
        self.add_widget(self.qty_label)

        add_btn = Button(
            text="Add",
            size_hint_x=0.12,
            background_normal="",
            background_color=(0.15, 0.5, 0.15, 1),
            color=(1, 1, 1, 1),
        )
        add_btn.bind(on_press=self._on_add)
        self.add_widget(add_btn)

        self.opening_text.bind(text=self._update_qty)
        self.closing_text.bind(text=self._update_qty)

    def _get_qty(self):
        try:
            op = float(self.opening_text.text or "0")
            cl = float(self.closing_text.text or "0")
            return max(0, cl - op)
        except ValueError:
            return 0

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
            "opening": float(self.opening_text.text or "0"),
            "closing": float(self.closing_text.text or "0"),
            "qty": qty,
            "rate": rate,
            "amount": amount,
        }
        screen = self._get_pos_screen()
        if screen:
            screen.add_to_cart(item)

        self.opening_text.text = "0"
        self.closing_text.text = "0"

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
    qty_input = ObjectProperty(None)

    def __init__(self, lube, **kwargs):
        super().__init__(**kwargs)
        self.lube_data = lube
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(52)
        self.spacing = dp(6)
        self.padding = [dp(8), dp(4)]

        brand_lbl = Label(
            text=lube["brand"],
            size_hint_x=0.18,
            halign="left",
            color=(1, 1, 1, 1),
        )
        self.add_widget(brand_lbl)

        name_lbl = Label(
            text=lube["product_name"],
            size_hint_x=0.25,
            halign="left",
            color=(1, 1, 1, 1),
        )
        self.add_widget(name_lbl)

        price_lbl = Label(
            text=curr(lube["selling_price"]),
            size_hint_x=0.12,
            color=(0.6, 1, 0.6, 1),
        )
        self.add_widget(price_lbl)

        stock_lbl = Label(
            text=f"{lube['stock_qty']:,.2f} {lube['unit']}",
            size_hint_x=0.15,
            color=(0.6, 0.6, 0.6, 1),
        )
        self.add_widget(stock_lbl)

        self.qty_input = TextInput(
            text="1",
            input_filter="float",
            multiline=False,
            size_hint_x=0.12,
            foreground_color=(1, 1, 1, 1),
            background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.qty_input)

        add_btn = Button(
            text="Add",
            size_hint_x=0.12,
            background_normal="",
            background_color=(0.15, 0.5, 0.15, 1),
            color=(1, 1, 1, 1),
        )
        add_btn.bind(on_press=self._on_add)
        self.add_widget(add_btn)

    def _on_add(self, *args):
        try:
            qty = float(self.qty_input.text or "0")
        except ValueError:
            qty = 0
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
            size_hint_x=0.35,
            halign="left",
            color=(1, 1, 1, 1),
            font_size="12sp",
        )
        self.add_widget(name_lbl)

        qty_lbl = Label(
            text=f"{item['qty']:,.2f}",
            size_hint_x=0.15,
            color=(0.8, 0.8, 0.8, 1),
            font_size="12sp",
        )
        self.add_widget(qty_lbl)

        rate_lbl = Label(
            text=curr(item["rate"]),
            size_hint_x=0.15,
            color=(0.8, 0.8, 0.8, 1),
            font_size="12sp",
        )
        self.add_widget(rate_lbl)

        amt_lbl = Label(
            text=curr(item["amount"]),
            size_hint_x=0.2,
            color=(0.6, 1, 0.6, 1),
            font_size="12sp",
        )
        self.add_widget(amt_lbl)

        del_btn = Button(
            text="X",
            size_hint_x=0.1,
            background_normal="",
            background_color=(0.6, 0.15, 0.15, 1),
            color=(1, 1, 1, 1),
            font_size="12sp",
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

    def _rebuild_fuel_tab(self):
        container = self.ids.fuel_container
        container.clear_widgets()
        pumps = Pump.get_with_tank()
        if not pumps:
            container.add_widget(Label(
                text="No pumps configured. Add pumps in Inventory first.",
                color=(0.8, 0.6, 0.2, 1),
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
            height=dp(32),
            spacing=dp(6),
            padding=[dp(8), 0],
        )
        for txt, sx in [("Brand", 0.18), ("Product", 0.25), ("Price", 0.12), ("Stock", 0.15), ("Qty", 0.12), ("", 0.12)]:
            h = Label(
                text=txt,
                size_hint_x=sx,
                bold=True,
                color=(0.6, 0.6, 0.6, 1),
                font_size="11sp",
            )
            header.add_widget(h)
        container.add_widget(header)
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

    def _clear_cart(self):
        self.cart_items.clear()
        self._refresh_cart()

    def show_error(self, msg):
        popup = Popup(
            title="Error",
            content=Label(text=msg, color=(1, 0.3, 0.3, 1)),
            size_hint=(0.7, 0.3),
        )
        popup.open()

    def show_info(self, title, msg):
        popup = Popup(
            title=title,
            content=Label(text=msg, color=(1, 1, 1, 1)),
            size_hint=(0.8, 0.4),
        )
        popup.open()

    def _checkout(self):
        if not self.cart_items:
            self.show_error("Cart is empty.")
            return

        customer_label = self.ids.customer_spinner.text
        customer_id = self._customer_map.get(customer_label)
        payment_mode = self.ids.payment_spinner.text

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

        popup = Popup(
            title="Sale Complete",
            content=Label(text=msg, color=(1, 1, 1, 1)),
            size_hint=(0.8, 0.5),
        )
        popup.open()

        self._clear_cart()

    def go_back(self):
        self.manager.current = "main"
