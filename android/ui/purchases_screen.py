from datetime import date

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.metrics import dp

from libs.models.purchase import Purchase
from libs.models.supplier import Supplier
from libs.models.fuel import FuelType
from libs.models.lube import LubeProduct
from libs.utils.formatting import curr


class PurchaseRow(BoxLayout):
    def __init__(self, purchase, screen, **kwargs):
        super().__init__(**kwargs)
        self.purchase = purchase
        self.screen = screen
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(44)
        self.spacing = dp(4)
        self.padding = [dp(6), dp(4)]
        self.add_widget(Label(
            text=purchase["purchase_date"] or "",
            size_hint_x=0.2, color=(0.8, 0.8, 0.8, 1), font_size="11sp",
        ))
        self.add_widget(Label(
            text=purchase["supplier_name"],
            size_hint_x=0.24, halign="left", color=(1, 1, 1, 1), font_size="11sp",
        ))
        inv = purchase.get("invoice_no", "") or ""
        self.add_widget(Label(
            text=inv, size_hint_x=0.22, halign="left",
            color=(0.8, 0.8, 0.8, 1), font_size="11sp",
        ))
        self.add_widget(Label(
            text=curr(purchase.get("total_amount", 0)),
            size_hint_x=0.2, color=(0.6, 1, 0.6, 1), font_size="11sp",
        ))
        btn = Button(
            text="View", size_hint_x=0.14, font_size="10sp",
            background_normal="", background_color=(0.2, 0.2, 0.25, 1), color=(1, 1, 1, 1),
        )
        btn.bind(on_press=lambda *a: screen._view_purchase(purchase["id"]))
        self.add_widget(btn)


class PurchasesScreen(Screen):
    def on_enter(self):
        self._rebuild()

    def _rebuild(self):
        container = self.ids.purchases_container
        container.clear_widgets()
        header = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(28),
            spacing=dp(4), padding=[dp(6), 0],
        )
        for txt, sx in [("Date", 0.2), ("Supplier", 0.24), ("Invoice", 0.22), ("Total", 0.2), ("", 0.14)]:
            header.add_widget(Label(
                text=txt, size_hint_x=sx, bold=True,
                color=(0.6, 0.6, 0.6, 1), font_size="10sp",
            ))
        container.add_widget(header)
        purchases = Purchase.get_all_with_supplier()
        if not purchases:
            container.add_widget(Label(
                text="No purchases yet. Tap + to add one.",
                color=(0.8, 0.6, 0.2, 1), size_hint_y=None, height=dp(40),
            ))
        else:
            for p in purchases:
                container.add_widget(PurchaseRow(p, self))
        container.add_widget(Widget(size_hint_y=1))

    def show_form(self):
        content = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(10))
        content.add_widget(Label(
            text="New Purchase", size_hint_y=None, height=dp(30),
            font_size="16sp", bold=True, color=(1, 1, 1, 1),
        ))

        suppliers = Supplier.get_all("name")
        supplier_spinner = Spinner(
            text="Select Supplier" if not suppliers else suppliers[0]["name"],
            values=[s["name"] for s in suppliers],
            size_hint_y=None, height=dp(36),
            background_color=(0.18, 0.18, 0.22, 1), color=(1, 1, 1, 1),
        )
        content.add_widget(supplier_spinner)

        inv_input = TextInput(
            hint_text="Invoice No", multiline=False,
            size_hint_y=None, height=dp(36),
            foreground_color=(1, 1, 1, 1), background_color=(0.15, 0.15, 0.18, 1),
        )
        content.add_widget(inv_input)

        date_input = TextInput(
            text=date.today().isoformat(), multiline=False,
            size_hint_y=None, height=dp(36),
            foreground_color=(1, 1, 1, 1), background_color=(0.15, 0.15, 0.18, 1),
        )
        content.add_widget(date_input)

        items_label = Label(
            text="Items:", size_hint_y=None, height=dp(24),
            bold=True, color=(0.8, 0.8, 0.8, 1), font_size="12sp",
        )
        content.add_widget(items_label)

        items_container = BoxLayout(
            orientation="vertical", size_hint_y=None,
            height=dp(160), spacing=dp(4),
        )

        type_spinner = Spinner(
            text="Fuel", values=["Fuel", "Lube"],
            size_hint_y=None, height=dp(32),
            background_color=(0.18, 0.18, 0.22, 1), color=(1, 1, 1, 1), font_size="11sp",
        )
        item_spinner = Spinner(
            text="--Select--", values=["--Select--"],
            size_hint_y=None, height=dp(32),
            background_color=(0.18, 0.18, 0.22, 1), color=(1, 1, 1, 1), font_size="11sp",
        )

        def _update_items(*a):
            item_spinner.values = ["--Select--"]
            item_spinner.text = "--Select--"
            if type_spinner.text == "Fuel":
                fuels = FuelType.get_all()
                for f in fuels:
                    item_spinner.values.append(f"FUEL:{f['id']}:{f['name']}")
            else:
                lubes = LubeProduct.get_all("brand")
                for l in lubes:
                    item_spinner.values.append(f"LUBE:{l['id']}:{l['brand']} {l['product_name']}")
        type_spinner.bind(text=_update_items)
        _update_items()

        qty_input = TextInput(
            text="0", input_filter="float", multiline=False,
            hint_text="Qty", size_hint_y=None, height=dp(32),
            foreground_color=(1, 1, 1, 1), background_color=(0.15, 0.15, 0.18, 1),
            font_size="11sp",
        )
        rate_input = TextInput(
            text="0", input_filter="float", multiline=False,
            hint_text="Rate", size_hint_y=None, height=dp(32),
            foreground_color=(1, 1, 1, 1), background_color=(0.15, 0.15, 0.18, 1),
            font_size="11sp",
        )

        item_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32), spacing=dp(4))
        item_row.add_widget(type_spinner)
        item_row.add_widget(item_spinner)
        item_row.add_widget(qty_input)
        item_row.add_widget(rate_input)

        items_container.add_widget(item_row)

        added_items_container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        total_label = Label(text="Total: Rs 0", size_hint_y=None, height=dp(24), color=(0.6, 1, 0.6, 1))
        added_items = []

        def _add_item(*a):
            sel = item_spinner.text
            if sel == "--Select--":
                return
            parts = sel.split(":", 2)
            if len(parts) != 3:
                return
            itype, iid, iname = parts
            try:
                qty = float(qty_input.text or "0")
                rate = float(rate_input.text or "0")
            except ValueError:
                return
            if qty <= 0 or rate <= 0:
                return
            amount = qty * rate
            added_items.append({"type": itype, "id": int(iid), "name": iname, "qty": qty, "rate": rate, "amount": amount})
            added_items_container.clear_widgets()
            total = 0
            for ai in added_items:
                row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24), spacing=dp(4))
                row.add_widget(Label(text=ai["name"], size_hint_x=0.4, font_size="10sp", color=(1, 1, 1, 1)))
                row.add_widget(Label(text=f"{ai['qty']:,.2f}", size_hint_x=0.15, font_size="10sp", color=(0.8, 0.8, 0.8, 1)))
                row.add_widget(Label(text=curr(ai["rate"]), size_hint_x=0.15, font_size="10sp", color=(0.8, 0.8, 0.8, 1)))
                row.add_widget(Label(text=curr(ai["amount"]), size_hint_x=0.15, font_size="10sp", color=(0.6, 1, 0.6, 1)))
                added_items_container.add_widget(row)
                total += ai["amount"]
            total_label.text = f"Total: {curr(total)}"
            qty_input.text = "0"
            rate_input.text = "0"

        add_item_btn = Button(
            text="+ Add Item", size_hint_y=None, height=dp(30), font_size="11sp",
            background_normal="", background_color=(0.15, 0.4, 0.15, 1), color=(1, 1, 1, 1),
        )
        add_item_btn.bind(on_press=_add_item)
        items_container.add_widget(add_item_btn)
        items_container.add_widget(added_items_container)
        items_container.add_widget(total_label)
        content.add_widget(items_container)

        supplier_map = {}
        for s in suppliers:
            supplier_map[s["name"]] = s["id"]

        def _save(*a):
            sname = supplier_spinner.text
            if sname == "Select Supplier" or sname not in supplier_map:
                from kivy.uix.popup import Popup
                Popup(title="Error", content=Label(text="Select a supplier.", color=(1, 0.3, 0.3, 1)),
                      size_hint=(0.7, 0.25)).open()
                return
            if not added_items:
                Popup(title="Error", content=Label(text="Add at least one item.", color=(1, 0.3, 0.3, 1)),
                      size_hint=(0.7, 0.25)).open()
                return
            pid = Purchase.create(
                supplier_map[sname],
                invoice_no=inv_input.text.strip(),
                purchase_date=date_input.text.strip(),
            )
            for ai in added_items:
                if ai["type"] == "FUEL":
                    Purchase.add_item(pid, "fuel", fuel_type_id=ai["id"], qty=ai["qty"], rate=ai["rate"])
                else:
                    Purchase.add_item(pid, "lube", lube_product_id=ai["id"], qty=ai["qty"], rate=ai["rate"])
                    LubeProduct.adjust_stock(ai["id"], ai["qty"])
            Purchase.update_total(pid)
            popup.dismiss()
            self._rebuild()

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(10))
        save_btn = Button(
            text="Save Purchase", font_size="12sp",
            background_normal="", background_color=(0.15, 0.5, 0.15, 1), color=(1, 1, 1, 1),
        )
        save_btn.bind(on_press=_save)
        cancel_btn = Button(
            text="Cancel", font_size="12sp",
            background_normal="", background_color=(0.3, 0.3, 0.35, 1), color=(1, 1, 1, 1),
        )
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = Popup(title="", content=content, size_hint=(0.92, 0.85))
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _view_purchase(self, pid):
        purchase = Purchase.get_with_supplier(pid)
        items = Purchase.get_items(pid)
        if not purchase:
            return
        lines = [
            f"Date: {purchase['purchase_date']}",
            f"Supplier: {purchase['supplier_name']}",
            f"Invoice: {purchase.get('invoice_no', 'N/A')}",
            "",
            "Items:",
        ]
        total = 0
        for it in items:
            name = it.get("fuel_name") or it.get("lube_name") or "?"
            lines.append(f"  {name} x {it['qty']:,.2f} @ {curr(it['rate'])} = {curr(it['amount'])}")
            total += it["amount"]
        lines.append("")
        lines.append(f"Total: {curr(total)}")
        msg = "\n".join(lines)
        popup = Popup(
            title="Purchase Details",
            content=Label(text=msg, color=(1, 1, 1, 1), font_size="12sp"),
            size_hint=(0.85, 0.6),
        )
        popup.open()

    def go_back(self):
        self.manager.current = "main"
