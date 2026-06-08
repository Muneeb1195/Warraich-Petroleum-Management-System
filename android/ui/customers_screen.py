from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.metrics import dp

from libs.models.customer import Customer
from libs.database.connection import get_connection
from libs.utils.formatting import curr


class CustomerScreen(Screen):
    def on_enter(self):
        self._rebuild()

    def _rebuild(self):
        container = self.ids.customer_container
        container.clear_widgets()
        customers = Customer.get_all("name")
        if not customers:
            container.add_widget(Label(
                text="No customers yet. Tap + to add one.",
                color=(0.8, 0.6, 0.2, 1),
                size_hint_y=None, height=dp(40),
            ))
        else:
            for c in customers:
                container.add_widget(CustomerRow(c, self))
        container.add_widget(Widget(size_hint_y=1))

    def filter(self, text):
        container = self.ids.customer_container
        text = text.lower()
        for child in container.children:
            if hasattr(child, "cust_data"):
                data = child.cust_data
                match = text in data["name"].lower() or \
                        text in data.get("phone", "").lower() or \
                        text in data.get("gstin", "").lower()
                child.opacity = 1 if match else 0.3
                child.disabled = not match

    def show_form(self, customer=None):
        content = CustomerForm(customer, self)
        popup = Popup(
            title="Edit Customer" if customer else "Add Customer",
            content=content,
            size_hint=(0.85, 0.7),
        )
        content.popup = popup
        popup.open()

    def confirm_delete(self, cid):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text="Delete this customer?", color=(1, 1, 1, 1)))
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(10))
        yes_btn = Button(text="Yes", background_normal="", background_color=(0.6, 0.15, 0.15, 1), color=(1,1,1,1))
        no_btn = Button(text="No", background_normal="", background_color=(0.2, 0.2, 0.25, 1), color=(1,1,1,1))
        btn_row.add_widget(yes_btn)
        btn_row.add_widget(no_btn)
        content.add_widget(btn_row)
        popup = Popup(title="Confirm", content=content, size_hint=(0.6, 0.25))
        yes_btn.bind(on_press=lambda *a: [Customer.delete(cid), self._rebuild(), popup.dismiss()])
        no_btn.bind(on_press=lambda *a: popup.dismiss())
        popup.open()

    def show_error(self, msg):
        popup = Popup(
            title="Error",
            content=Label(text=msg, color=(1, 0.3, 0.3, 1)),
            size_hint=(0.7, 0.3),
        )
        popup.open()

    def go_back(self):
        self.manager.current = "main"


class CustomerRow(BoxLayout):
    def __init__(self, cust, screen, **kwargs):
        super().__init__(**kwargs)
        self.cust_data = cust
        self.screen = screen
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(2)]

        balance = cust.get("balance", 0)
        balance_color = (1, 0.4, 0.4, 1) if balance > 0 else (0.6, 1, 0.6, 1)

        for txt, sx, color in [
            (cust["name"], 0.18, (1, 1, 1, 1)),
            (cust.get("phone", ""), 0.18, (1, 1, 1, 1)),
            (cust.get("gstin", ""), 0.2, (1, 1, 1, 1)),
            (curr(cust["credit_limit"]), 0.15, (1, 1, 1, 1)),
            (curr(balance), 0.15, balance_color),
        ]:
            lbl = Label(text=txt, size_hint_x=sx, halign="left", color=color, font_size="12sp")
            self.add_widget(lbl)

        btn_row = BoxLayout(orientation="horizontal", size_hint_x=0.14, spacing=dp(4))
        edit_btn = Button(text="Edit", font_size="11sp", background_normal="",
                          background_color=(0.2, 0.3, 0.5, 1), color=(1,1,1,1))
        edit_btn.bind(on_press=lambda *a: screen.show_form(cust))
        del_btn = Button(text="Del", font_size="11sp", background_normal="",
                         background_color=(0.5, 0.15, 0.15, 1), color=(1,1,1,1))
        del_btn.bind(on_press=lambda *a: screen.confirm_delete(cust["id"]))
        btn_row.add_widget(edit_btn)
        btn_row.add_widget(del_btn)
        self.add_widget(btn_row)


class CustomerForm(BoxLayout):
    def __init__(self, customer, screen, **kwargs):
        super().__init__(**kwargs)
        self.customer = customer
        self.screen = screen
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = [dp(12), dp(8)]

        self.name_input = TextInput(
            text=customer["name"] if customer else "",
            hint_text="Customer Name *",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.name_input)

        self.phone_input = TextInput(
            text=customer.get("phone", "") if customer else "",
            hint_text="Phone Number",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.phone_input)

        self.address_input = TextInput(
            text=customer.get("address", "") if customer else "",
            hint_text="Address",
            multiline=True,
            size_hint_y=None, height=dp(60),
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.address_input)

        self.gstin_input = TextInput(
            text=customer.get("gstin", "") if customer else "",
            hint_text="GSTIN",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.gstin_input)

        self.credit_input = TextInput(
            text=str(customer["credit_limit"]) if customer else "0",
            hint_text="Credit Limit",
            input_filter="float", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.credit_input)

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
            self.screen.show_error("Customer name is required.")
            return
        try:
            credit = float(self.credit_input.text or "0")
        except ValueError:
            credit = 0

        if self.customer:
            try:
                conn = get_connection()
                conn.execute(
                    "UPDATE customers SET name=?, phone=?, address=?, gstin=?, credit_limit=? WHERE id=?",
                    (name, self.phone_input.text, self.address_input.text,
                     self.gstin_input.text, credit, self.customer["id"]),
                )
                conn.commit()
                conn.close()
            except Exception as e:
                self.screen.show_error(f"DB error: {e}")
                return
        else:
            Customer.create(name, self.phone_input.text, self.address_input.text,
                            self.gstin_input.text, credit)

        self.popup.dismiss()
        self.screen._rebuild()
