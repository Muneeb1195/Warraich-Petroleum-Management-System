from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.graphics import RoundedRectangle, Color
from kivy.metrics import dp
from kivy.clock import Clock

from libs.utils.theme import *
from libs.models.sale import Sale
from libs.utils.formatting import curr


class SalesHistoryScreen(Screen):
    def on_enter(self):
        self._rebuild()

    def _rebuild(self):
        container = self.ids.sales_container
        container.clear_widgets()
        sales = Sale.get_all_summary(limit=200, include_voided=True)
        if not sales:
            container.add_widget(Label(
                text="No sales found.",
                color=TEXT_AMBER, size_hint_y=None, height=dp(40),
            ))
        else:
            for s in sales:
                container.add_widget(SaleCard(s, self))
        container.add_widget(Widget(size_hint_y=1))

    def show_void_popup(self, sale):
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        content.add_widget(Label(
            text=(f"Void invoice {sale['invoice_no']}?\n\n"
                  f"Customer: {sale.get('customer_name', 'Walk-in')}\n"
                  f"Date: {sale['sale_date']}\n"
                  f"Amount: {curr(sale['grand_total'])}\n\n"
                  f"This will restore stock and customer balance."),
            color=TEXT_PRIMARY, halign="center", text_size=(dp(260), None),
        ))
        reason_input = TextInput(
            hint_text="Reason for void (optional)",
            multiline=False, size_hint_y=None, height=dp(42),
            foreground_color=TEXT_PRIMARY,
            background_color=(0.15, 0.15, 0.18, 1),
        )
        content.add_widget(reason_input)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(40))
        btn_row.add_widget(Button(
            text="Cancel", background_normal="", background_color=BTN_CANCEL, color=TEXT_PRIMARY,
            on_press=lambda *a: void_popup.dismiss(),
        ))
        btn_row.add_widget(Button(
            text="Void Sale", background_normal="", background_color=BTN_DANGER, color=TEXT_PRIMARY,
            on_press=lambda *a: self._do_void(sale, reason_input.text.strip(), void_popup),
        ))
        content.add_widget(btn_row)
        void_popup = Popup(title="Confirm Void", content=content, size_hint=(0.85, 0.5), auto_dismiss=False)
        void_popup.open()

    def _do_void(self, sale, reason, popup):
        popup.dismiss()
        ok, msg = Sale.void(sale["id"], reason)
        Popup(
            title="Sale Voided" if ok else "Error",
            content=Label(text=msg, color=TEXT_PRIMARY),
            size_hint=(0.7, 0.25),
        ).open()
        if ok:
            self._rebuild()

    def go_back(self):
        Clock.schedule_once(lambda *a: setattr(self.manager, 'current', "main"))


class SaleCard(BoxLayout):
    def __init__(self, sale, screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(64)
        self.spacing = dp(2)
        self.padding = [dp(10), dp(4)]
        with self.canvas.before:
            Color(rgba=BG_CARD)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        self.bind(pos=self._update_bg, size=self._update_bg)
        is_voided = sale.get("voided")
        voided_label = " [VOIDED]" if is_voided else ""
        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32))
        top.add_widget(Label(
            text=f"{sale['invoice_no']}{voided_label}", bold=True,
            color=TEXT_DIM if is_voided else TEXT_PRIMARY,
            font_size="13sp", halign="left", size_hint_x=0.35,
        ))
        top.add_widget(Label(
            text=sale.get("customer_name", "Walk-in"),
            color=TEXT_DIM if is_voided else TEXT_PRIMARY,
            font_size="12sp", halign="left", size_hint_x=0.35,
        ))
        top.add_widget(Label(
            text=curr(sale["grand_total"]),
            color=TEXT_DIM if is_voided else TEXT_PRIMARY,
            font_size="13sp", halign="right", size_hint_x=0.2,
        ))
        top.add_widget(Label(
            text=sale["payment_mode"][0],
            color=TEXT_DIM if is_voided else TEXT_SECONDARY,
            font_size="12sp", halign="right", size_hint_x=0.1,
        ))
        self.add_widget(top)
        bot = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
        bot.add_widget(Label(
            text=sale["sale_date"],
            color=TEXT_DIM if is_voided else TEXT_SECONDARY,
            font_size="12sp", halign="left", size_hint_x=0.4,
        ))
        if not is_voided:
            void_btn = Button(
                text="Void", font_size="12sp", size_hint_x=0.15,
                background_normal="", background_color=BTN_DANGER, color=TEXT_PRIMARY,
            )
            void_btn.bind(on_press=lambda *a: screen.show_void_popup(sale))
            bot.add_widget(void_btn)
        else:
            bot.add_widget(Widget(size_hint_x=0.15))
        bot.add_widget(Widget(size_hint_x=0.45))
        self.add_widget(bot)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
