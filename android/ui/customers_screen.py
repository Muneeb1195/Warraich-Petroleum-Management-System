from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.metrics import dp

from libs.utils.theme import *
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
                color=TEXT_AMBER,
                size_hint_y=None, height=dp(40),
            ))
        else:
            for c in customers:
                container.add_widget(CustomerCard(c, self))
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
        content.add_widget(Label(text="Delete this customer?", color=TEXT_PRIMARY))
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(10))
        yes_btn = Button(text="Yes", background_normal="", background_color=BTN_DANGER, color=(1,1,1,1))
        no_btn = Button(text="No", background_normal="", background_color=BTN_NEUTRAL_DARK, color=(1,1,1,1))
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
            content=Label(text=msg, color=TEXT_ERROR),
            size_hint=(0.7, 0.3),
        )
        popup.open()

    def go_back(self):
        self.manager.current = "main"


class CustomerCard(BoxLayout):
    def __init__(self, cust, screen, **kwargs):
        super().__init__(**kwargs)
        self.cust_data = cust
        self.screen = screen
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(64)
        self.spacing = dp(2)
        self.padding = [dp(10), dp(6)]

        balance = cust.get("balance", 0)
        bal_color = VAL_NEGATIVE if balance > 0 else VAL_POSITIVE

        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
        top.add_widget(Label(
            text=cust["name"], bold=True, color=TEXT_PRIMARY,
            font_size="14sp", halign="left",
        ))
        top.add_widget(Label(
            text=curr(balance), color=bal_color,
            font_size="13sp", halign="right", size_hint_x=0.3,
        ))
        self.add_widget(top)

        bot = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        phone = cust.get("phone", "")
        gstin = cust.get("gstin", "")
        limit = cust["credit_limit"]
        bot.add_widget(Label(
            text=f"Ph: {phone}" if phone else "",
            color=TEXT_SECONDARY, font_size="11sp", halign="left", size_hint_x=0.3,
        ))
        bot.add_widget(Label(
            text=f"GST: {gstin}" if gstin else "",
            color=TEXT_SECONDARY, font_size="11sp", halign="left", size_hint_x=0.3,
        ))
        bot.add_widget(Label(
            text=f"Limit: {curr(limit)}", color=TEXT_DIM,
            font_size="11sp", halign="left", size_hint_x=0.2,
        ))
        btn_row = BoxLayout(orientation="horizontal", size_hint_x=0.2, spacing=dp(4))
        edit_btn = Button(text="Edit", font_size="10sp", background_normal="",
                          background_color=BTN_INFO, color=TEXT_PRIMARY)
        edit_btn.bind(on_press=lambda *a: screen.show_form(cust))
        del_btn = Button(text="Del", font_size="10sp", background_normal="",
                         background_color=BTN_DANGER_VARIANT, color=TEXT_PRIMARY)
        del_btn.bind(on_press=lambda *a: screen.confirm_delete(cust["id"]))
        btn_row.add_widget(edit_btn)
        btn_row.add_widget(del_btn)
        bot.add_widget(btn_row)
        self.add_widget(bot)


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
                          background_color=BTN_PRIMARY, color=(1,1,1,1))
        save_btn.bind(on_press=self._save)
        cancel_btn = Button(text="Cancel", background_normal="",
                            background_color=BTN_CANCEL, color=(1,1,1,1))
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
