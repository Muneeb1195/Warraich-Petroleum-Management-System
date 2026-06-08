from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy.metrics import dp

from libs.models.fuel import FuelType, Tank, Pump
from libs.models.lube import LubeProduct
from libs.database.connection import get_connection
from libs.utils.formatting import curr


class InventoryScreen(Screen):
    def on_enter(self):
        self._rebuild_tanks()
        self._rebuild_pumps()
        self._rebuild_lubes()

    def _rebuild_tanks(self):
        self.ids.tank_container.clear_widgets()
        tanks = Tank.get_with_fuel_type()
        if not tanks:
            self.ids.tank_container.add_widget(Label(
                text="No tanks configured. Tap + to add one.",
                color=(0.8, 0.6, 0.2, 1),
                size_hint_y=None, height=dp(40),
            ))
        else:
            for t in tanks:
                self.ids.tank_container.add_widget(TankRow(t, self))
        self.ids.tank_container.add_widget(Widget(size_hint_y=1))

    def _rebuild_pumps(self):
        self.ids.pump_container.clear_widgets()
        pumps = Pump.get_with_tank()
        if not pumps:
            self.ids.pump_container.add_widget(Label(
                text="No pumps configured. Tap + to add one.",
                color=(0.8, 0.6, 0.2, 1),
                size_hint_y=None, height=dp(40),
            ))
        else:
            for p in pumps:
                self.ids.pump_container.add_widget(PumpRow(p, self))
        self.ids.pump_container.add_widget(Widget(size_hint_y=1))

    def _rebuild_lubes(self):
        self.ids.lube_container.clear_widgets()
        lubes = LubeProduct.get_all("brand")
        if not lubes:
            self.ids.lube_container.add_widget(Label(
                text="No lubricants. Tap + to add one.",
                color=(0.8, 0.6, 0.2, 1),
                size_hint_y=None, height=dp(40),
            ))
        else:
            for l in lubes:
                self.ids.lube_container.add_widget(LubeRow(l, self))
        self.ids.lube_container.add_widget(Widget(size_hint_y=1))

    def filter_tanks(self, text):
        container = self.ids.tank_container
        text = text.lower()
        for child in container.children:
            if hasattr(child, "tank_data"):
                match = text in child.tank_data.get("name", "").lower() or \
                        text in child.tank_data.get("fuel_name", "").lower()
                child.opacity = 1 if match else 0.3
                child.disabled = not match

    def filter_pumps(self, text):
        container = self.ids.pump_container
        text = text.lower()
        for child in container.children:
            if hasattr(child, "pump_data"):
                match = text in child.pump_data.get("pump_no", "").lower() or \
                        text in child.pump_data.get("fuel_name", "").lower()
                child.opacity = 1 if match else 0.3
                child.disabled = not match

    def filter_lubes(self, text):
        container = self.ids.lube_container
        text = text.lower()
        for child in container.children:
            if hasattr(child, "lube_data"):
                match = text in child.lube_data.get("brand", "").lower() or \
                        text in child.lube_data.get("product_name", "").lower()
                child.opacity = 1 if match else 0.3
                child.disabled = not match

    def show_tank_form(self, tank=None):
        content = TankForm(tank, self)
        popup = Popup(
            title="Edit Tank" if tank else "Add Tank",
            content=content,
            size_hint=(0.85, 0.65),
        )
        content.popup = popup
        popup.open()

    def show_pump_form(self, pump=None):
        content = PumpForm(pump, self)
        popup = Popup(
            title="Edit Pump" if pump else "Add Pump",
            content=content,
            size_hint=(0.85, 0.6),
        )
        content.popup = popup
        popup.open()

    def show_lube_form(self, lube=None):
        content = LubeForm(lube, self)
        popup = Popup(
            title="Edit Lubricant" if lube else "Add Lubricant",
            content=content,
            size_hint=(0.9, 0.75),
        )
        content.popup = popup
        popup.open()

    def confirm_delete_tank(self, tank_id):
        self._confirm_delete("Delete this tank?", lambda: self._do_delete_tank(tank_id))

    def confirm_delete_pump(self, pump_id):
        self._confirm_delete("Delete this pump?", lambda: self._do_delete_pump(pump_id))

    def confirm_delete_lube(self, lube_id):
        self._confirm_delete("Delete this product?", lambda: self._do_delete_lube(lube_id))

    def _confirm_delete(self, msg, callback):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text=msg, color=(1, 1, 1, 1)))
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(10))
        yes_btn = Button(text="Yes", background_normal="", background_color=(0.6, 0.15, 0.15, 1), color=(1,1,1,1))
        no_btn = Button(text="No", background_normal="", background_color=(0.2, 0.2, 0.25, 1), color=(1,1,1,1))
        btn_row.add_widget(yes_btn)
        btn_row.add_widget(no_btn)
        content.add_widget(btn_row)
        popup = Popup(title="Confirm", content=content, size_hint=(0.6, 0.25))
        yes_btn.bind(on_press=lambda *a: [callback(), popup.dismiss()])
        no_btn.bind(on_press=lambda *a: popup.dismiss())
        popup.open()

    def _do_delete_tank(self, tank_id):
        Tank.delete(tank_id)
        self._rebuild_tanks()

    def _do_delete_pump(self, pump_id):
        Pump.delete(pump_id)
        self._rebuild_pumps()

    def _do_delete_lube(self, lube_id):
        LubeProduct.delete(lube_id)
        self._rebuild_lubes()

    def show_error(self, msg):
        popup = Popup(
            title="Error",
            content=Label(text=msg, color=(1, 0.3, 0.3, 1)),
            size_hint=(0.7, 0.3),
        )
        popup.open()

    def go_back(self):
        self.manager.current = "main"


class TankRow(BoxLayout):
    def __init__(self, tank, screen, **kwargs):
        super().__init__(**kwargs)
        self.tank_data = tank
        self.screen = screen
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(2)]

        for txt, sx in [
            (tank["name"], 0.2),
            (tank["fuel_name"], 0.15),
            (f"{tank['capacity']:,.0f} L", 0.15),
            (f"{tank['current_level']:,.0f} L", 0.15),
        ]:
            lbl = Label(text=txt, size_hint_x=sx, halign="left", color=(1,1,1,1), font_size="12sp")
            self.add_widget(lbl)

        btn_row = BoxLayout(orientation="horizontal", size_hint_x=0.25, spacing=dp(4))
        edit_btn = Button(text="Edit", font_size="11sp", background_normal="",
                          background_color=(0.2, 0.3, 0.5, 1), color=(1,1,1,1))
        edit_btn.bind(on_press=lambda *a: screen.show_tank_form(tank))
        del_btn = Button(text="Del", font_size="11sp", background_normal="",
                         background_color=(0.5, 0.15, 0.15, 1), color=(1,1,1,1))
        del_btn.bind(on_press=lambda *a: screen.confirm_delete_tank(tank["id"]))
        btn_row.add_widget(edit_btn)
        btn_row.add_widget(del_btn)
        self.add_widget(btn_row)


class PumpRow(BoxLayout):
    def __init__(self, pump, screen, **kwargs):
        super().__init__(**kwargs)
        self.pump_data = pump
        self.screen = screen
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(2)]

        for txt, sx in [
            (pump["pump_no"], 0.15),
            (pump.get("tank_name", ""), 0.15),
            (pump["fuel_name"], 0.15),
            (pump.get("description", ""), 0.25),
        ]:
            lbl = Label(text=txt, size_hint_x=sx, halign="left", color=(1,1,1,1), font_size="12sp")
            self.add_widget(lbl)

        btn_row = BoxLayout(orientation="horizontal", size_hint_x=0.2, spacing=dp(4))
        edit_btn = Button(text="Edit", font_size="11sp", background_normal="",
                          background_color=(0.2, 0.3, 0.5, 1), color=(1,1,1,1))
        edit_btn.bind(on_press=lambda *a: screen.show_pump_form(pump))
        del_btn = Button(text="Del", font_size="11sp", background_normal="",
                         background_color=(0.5, 0.15, 0.15, 1), color=(1,1,1,1))
        del_btn.bind(on_press=lambda *a: screen.confirm_delete_pump(pump["id"]))
        btn_row.add_widget(edit_btn)
        btn_row.add_widget(del_btn)
        self.add_widget(btn_row)


class LubeRow(BoxLayout):
    def __init__(self, lube, screen, **kwargs):
        super().__init__(**kwargs)
        self.lube_data = lube
        self.screen = screen
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(2)]

        info_text = f"{lube['stock_qty']:,.0f} {lube['unit']} | GST {lube.get('gst_rate', 18)}%"
        for txt, sx in [
            (lube["brand"], 0.18),
            (lube["product_name"], 0.22),
            (info_text, 0.22),
            (curr(lube["selling_price"]), 0.12),
        ]:
            lbl = Label(text=txt, size_hint_x=sx, halign="left", color=(1,1,1,1), font_size="11sp")
            self.add_widget(lbl)

        btn_row = BoxLayout(orientation="horizontal", size_hint_x=0.2, spacing=dp(4))
        edit_btn = Button(text="Edit", font_size="11sp", background_normal="",
                          background_color=(0.2, 0.3, 0.5, 1), color=(1,1,1,1))
        edit_btn.bind(on_press=lambda *a: screen.show_lube_form(lube))
        del_btn = Button(text="Del", font_size="11sp", background_normal="",
                         background_color=(0.5, 0.15, 0.15, 1), color=(1,1,1,1))
        del_btn.bind(on_press=lambda *a: screen.confirm_delete_lube(lube["id"]))
        btn_row.add_widget(edit_btn)
        btn_row.add_widget(del_btn)
        self.add_widget(btn_row)


class TankForm(BoxLayout):
    def __init__(self, tank, screen, **kwargs):
        super().__init__(**kwargs)
        self.tank = tank
        self.screen = screen
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = [dp(12), dp(8)]

        self.name_input = TextInput(
            text=tank["name"] if tank else "",
            hint_text="Tank Name",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.name_input)

        self.fuel_spinner = Spinner(
            text="Select Fuel Type",
            size_hint_y=None, height=dp(40),
            background_color=(0.18, 0.18, 0.22, 1), color=(1,1,1,1),
        )
        self._fuel_map = {}
        fuels = FuelType.get_all()
        values = []
        for f in fuels:
            label = f["name"]
            values.append(label)
            self._fuel_map[label] = f["id"]
        self.fuel_spinner.values = values
        if tank:
            fuel = FuelType.get_by_id(tank["fuel_type_id"])
            if fuel:
                self.fuel_spinner.text = fuel["name"]
        if values:
            self.fuel_spinner.text = values[0]
        self.add_widget(self.fuel_spinner)

        self.capacity_input = TextInput(
            text=str(tank["capacity"]) if tank else "0",
            hint_text="Capacity (L)",
            input_filter="float", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.capacity_input)

        self.level_input = TextInput(
            text=str(tank["current_level"]) if tank else "0",
            hint_text="Current Level (L)",
            input_filter="float", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.level_input)

        self.add_widget(Widget())
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(10))
        save_btn = Button(text="Save", background_normal="",
                          background_color=(0.15, 0.5, 0.15, 1), color=(1,1,1,1))
        save_btn.bind(on_press=self._save)
        cancel_btn = Button(text="Cancel", background_normal="",
                            background_color=(0.3, 0.3, 0.35, 1), color=(1,1,1,1))
        cancel_btn.bind(on_press=lambda *a: self.popup.dismiss())
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        self.add_widget(btn_row)

    def _save(self, *args):
        name = self.name_input.text.strip()
        if not name:
            self.screen.show_error("Tank name is required.")
            return
        try:
            capacity = float(self.capacity_input.text or "0")
            level = float(self.level_input.text or "0")
        except ValueError:
            self.screen.show_error("Invalid number.")
            return
        fuel_type_id = self._fuel_map.get(self.fuel_spinner.text)
        if not fuel_type_id:
            self.screen.show_error("Select a fuel type.")
            return

        if self.tank:
            conn = get_connection()
            conn.execute(
                "UPDATE tanks SET name=?, fuel_type_id=?, capacity=?, current_level=? WHERE id=?",
                (name, fuel_type_id, capacity, level, self.tank["id"]),
            )
            conn.commit()
            conn.close()
        else:
            Tank.create(name, fuel_type_id, capacity, level)

        self.popup.dismiss()
        self.screen._rebuild_tanks()


class PumpForm(BoxLayout):
    def __init__(self, pump, screen, **kwargs):
        super().__init__(**kwargs)
        self.pump = pump
        self.screen = screen
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = [dp(12), dp(8)]

        self.pump_no_input = TextInput(
            text=pump["pump_no"] if pump else "",
            hint_text="Pump Number",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.pump_no_input)

        self.tank_spinner = Spinner(
            text="Select Tank",
            size_hint_y=None, height=dp(40),
            background_color=(0.18, 0.18, 0.22, 1), color=(1,1,1,1),
        )
        self._tank_map = {}
        tanks = Tank.get_with_fuel_type()
        values = []
        for t in tanks:
            label = f"{t['name']} ({t['fuel_name']})"
            values.append(label)
            self._tank_map[label] = t["id"]
        self.tank_spinner.values = values
        if pump:
            for label, tid in self._tank_map.items():
                if tid == pump["tank_id"]:
                    self.tank_spinner.text = label
                    break
        if values and not pump:
            self.tank_spinner.text = values[0]
        self.add_widget(self.tank_spinner)

        self.desc_input = TextInput(
            text=pump.get("description", "") if pump else "",
            hint_text="Description (optional)",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.desc_input)

        self.add_widget(Widget())
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(10))
        save_btn = Button(text="Save", background_normal="",
                          background_color=(0.15, 0.5, 0.15, 1), color=(1,1,1,1))
        save_btn.bind(on_press=self._save)
        cancel_btn = Button(text="Cancel", background_normal="",
                            background_color=(0.3, 0.3, 0.35, 1), color=(1,1,1,1))
        cancel_btn.bind(on_press=lambda *a: self.popup.dismiss())
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        self.add_widget(btn_row)

    def _save(self, *args):
        pump_no = self.pump_no_input.text.strip()
        if not pump_no:
            self.screen.show_error("Pump number is required.")
            return
        tank_id = self._tank_map.get(self.tank_spinner.text)
        if not tank_id:
            self.screen.show_error("Select a tank.")
            return

        if self.pump:
            conn = get_connection()
            conn.execute(
                "UPDATE pumps SET pump_no=?, tank_id=?, description=? WHERE id=?",
                (pump_no, tank_id, self.desc_input.text, self.pump["id"]),
            )
            conn.commit()
            conn.close()
        else:
            Pump.create(pump_no, tank_id, self.desc_input.text)

        self.popup.dismiss()
        self.screen._rebuild_pumps()


class LubeForm(BoxLayout):
    def __init__(self, lube, screen, **kwargs):
        super().__init__(**kwargs)
        self.lube = lube
        self.screen = screen
        self.orientation = "vertical"
        self.spacing = dp(6)
        self.padding = [dp(12), dp(8)]

        self.brand_input = TextInput(
            text=lube["brand"] if lube else "",
            hint_text="Brand (e.g. Shell, Mobil)",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.brand_input)

        self.name_input = TextInput(
            text=lube["product_name"] if lube else "",
            hint_text="Product Name",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.name_input)

        self.unit_spinner = Spinner(
            text=lube["unit"] if lube else "Bottle",
            values=["Bottle", "Can", "Liter", "Pouch", "Box"],
            size_hint_y=None, height=dp(40),
            background_color=(0.18, 0.18, 0.22, 1), color=(1,1,1,1),
        )
        self.add_widget(self.unit_spinner)

        self.purchase_input = TextInput(
            text=str(lube["purchase_rate"]) if lube else "0",
            hint_text="Purchase Rate",
            input_filter="float", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.purchase_input)

        self.selling_input = TextInput(
            text=str(lube["selling_price"]) if lube else "0",
            hint_text="Selling Price",
            input_filter="float", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.selling_input)

        self.stock_input = TextInput(
            text=str(lube["stock_qty"]) if lube else "0",
            hint_text="Stock Quantity",
            input_filter="float", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.stock_input)

        self.hsn_input = TextInput(
            text=lube.get("hsn_code", "271019") if lube else "271019",
            hint_text="HSN Code",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.hsn_input)

        self.gst_input = TextInput(
            text=str(lube.get("gst_rate", 18)) if lube else "18",
            hint_text="GST Rate (%)",
            input_filter="float", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.gst_input)

        self.add_widget(Widget())
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(10))
        save_btn = Button(text="Save", background_normal="",
                          background_color=(0.15, 0.5, 0.15, 1), color=(1,1,1,1))
        save_btn.bind(on_press=self._save)
        cancel_btn = Button(text="Cancel", background_normal="",
                            background_color=(0.3, 0.3, 0.35, 1), color=(1,1,1,1))
        cancel_btn.bind(on_press=lambda *a: self.popup.dismiss())
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        self.add_widget(btn_row)

    def _save(self, *args):
        brand = self.brand_input.text.strip()
        name = self.name_input.text.strip()
        if not brand or not name:
            self.screen.show_error("Brand and Product Name are required.")
            return
        try:
            purchase = float(self.purchase_input.text or "0")
            selling = float(self.selling_input.text or "0")
            stock = float(self.stock_input.text or "0")
            gst = float(self.gst_input.text or "0")
        except ValueError:
            self.screen.show_error("Invalid number.")
            return

        if self.lube:
            LubeProduct.update(self.lube["id"],
                               brand=brand, product_name=name,
                               unit=self.unit_spinner.text,
                               purchase_rate=purchase, selling_price=selling,
                               stock_qty=stock, hsn_code=self.hsn_input.text,
                               gst_rate=gst)
        else:
            LubeProduct.create(brand, name, self.unit_spinner.text,
                                purchase, selling, stock,
                                self.hsn_input.text, gst)

        self.popup.dismiss()
        self.screen._rebuild_lubes()
