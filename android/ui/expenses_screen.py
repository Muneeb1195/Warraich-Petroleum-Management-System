from datetime import date

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

from libs.models.expense import Expense, ExpenseCategory
from libs.database.connection import get_connection
from libs.utils.formatting import curr


class ExpenseScreen(Screen):
    def on_enter(self):
        self._rebuild()

    def _rebuild(self):
        container = self.ids.expense_container
        container.clear_widgets()
        expenses = Expense.get_with_category()
        if not expenses:
            container.add_widget(Label(
                text="No expenses recorded. Tap + to add one.",
                color=TEXT_AMBER,
                size_hint_y=None, height=dp(40),
            ))
        else:
            for e in expenses:
                container.add_widget(ExpenseCard(e, self))
        container.add_widget(Widget(size_hint_y=1))

    def filter(self, text):
        container = self.ids.expense_container
        text = text.lower()
        for child in container.children:
            if hasattr(child, "expense_data"):
                data = child.expense_data
                match = text in data.get("expense_date", "").lower() or \
                        text in data.get("category_name", "").lower() or \
                        text in data.get("description", "").lower()
                child.opacity = 1 if match else 0.3
                child.disabled = not match

    def show_form(self, expense=None):
        content = ExpenseForm(expense, self)
        popup = Popup(
            title="Edit Expense" if expense else "Add Expense",
            content=content,
            size_hint=(0.85, 0.65),
        )
        content.popup = popup
        popup.open()

    def confirm_delete(self, eid):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text="Delete this expense?", color=TEXT_PRIMARY))
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(10))
        yes_btn = Button(text="Yes", background_normal="", background_color=BTN_DANGER, color=(1,1,1,1))
        no_btn = Button(text="No", background_normal="", background_color=BTN_NEUTRAL_DARK, color=(1,1,1,1))
        btn_row.add_widget(yes_btn)
        btn_row.add_widget(no_btn)
        content.add_widget(btn_row)
        popup = Popup(title="Confirm", content=content, size_hint=(0.6, 0.25))
        yes_btn.bind(on_press=lambda *a: [Expense.delete(eid), self._rebuild(), popup.dismiss()])
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


class ExpenseCard(BoxLayout):
    def __init__(self, expense, screen, **kwargs):
        super().__init__(**kwargs)
        self.expense_data = expense
        self.screen = screen
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(64)
        self.spacing = dp(2)
        self.padding = [dp(10), dp(6)]

        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
        top.add_widget(Label(
            text=curr(expense["amount"]), bold=True, color=VAL_NEGATIVE,
            font_size="14sp", halign="left", size_hint_x=0.25,
        ))
        top.add_widget(Label(
            text=expense.get("expense_date", ""), color=TEXT_SECONDARY,
            font_size="12sp", halign="left", size_hint_x=0.3,
        ))
        top.add_widget(Label(
            text=expense.get("category_name", ""), color=TEXT_BLUE_HEADER,
            font_size="12sp", halign="right", size_hint_x=0.25,
        ))
        btn_row = BoxLayout(orientation="horizontal", size_hint_x=0.2, spacing=dp(4))
        edit_btn = Button(text="Edit", font_size="10sp", background_normal="",
                          background_color=BTN_INFO, color=TEXT_PRIMARY)
        edit_btn.bind(on_press=lambda *a: screen.show_form(expense))
        del_btn = Button(text="Del", font_size="10sp", background_normal="",
                         background_color=BTN_DANGER, color=TEXT_PRIMARY)
        del_btn.bind(on_press=lambda *a: screen.confirm_delete(expense["id"]))
        btn_row.add_widget(edit_btn)
        btn_row.add_widget(del_btn)
        top.add_widget(btn_row)
        self.add_widget(top)

        bot = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        desc = expense.get("description", "")
        bot.add_widget(Label(
            text=desc if desc else "No description",
            color=TEXT_DIM if desc else TEXT_VERSION,
            font_size="11sp", halign="left", italic=not desc,
        ))
        self.add_widget(bot)


class ExpenseForm(BoxLayout):
    def __init__(self, expense, screen, **kwargs):
        super().__init__(**kwargs)
        self.expense = expense
        self.screen = screen
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = [dp(12), dp(8)]

        cat_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(6))
        self.category_spinner = Spinner(
            text="Select Category",
            size_hint_x=0.8,
            background_color=(0.18, 0.18, 0.22, 1), color=(1,1,1,1),
        )
        self._category_map = {}
        self._refresh_categories()
        if expense:
            for label, cid in self._category_map.items():
                if cid == expense["category_id"]:
                    self.category_spinner.text = label
                    break
        add_cat_btn = Button(
            text="+", size_hint_x=0.15,
            background_normal="", background_color=BTN_SECONDARY, color=(1,1,1,1),
        )
        add_cat_btn.bind(on_press=self._add_category)
        cat_row.add_widget(self.category_spinner)
        cat_row.add_widget(add_cat_btn)
        self.add_widget(cat_row)

        self.amount_input = TextInput(
            text=str(expense["amount"]) if expense else "",
            hint_text="Amount *",
            input_filter="float", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.amount_input)

        self.desc_input = TextInput(
            text=expense.get("description", "") if expense else "",
            hint_text="Description (optional)",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.desc_input)

        self.date_input = TextInput(
            text=expense["expense_date"] if expense else date.today().isoformat(),
            hint_text="Date (YYYY-MM-DD)",
            multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.date_input)

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

    def _refresh_categories(self):
        cats = ExpenseCategory.get_all("name")
        values = []
        self._category_map = {}
        for c in cats:
            values.append(c["name"])
            self._category_map[c["name"]] = c["id"]
        self.category_spinner.values = values
        if values and not self.expense:
            self.category_spinner.text = values[0]

    def _add_category(self, *args):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text="New Category Name:", color=(1,1,1,1), size_hint_y=None, height=dp(30)))
        name_input = TextInput(
            hint_text="e.g. Electricity", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        content.add_widget(name_input)
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(10))
        add_btn = Button(text="Add", background_normal="",
                         background_color=BTN_PRIMARY, color=(1,1,1,1))
        cancel_btn = Button(text="Cancel", background_normal="",
                            background_color=BTN_CANCEL, color=(1,1,1,1))
        btn_row.add_widget(add_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        popup = Popup(title="Add Category", content=content, size_hint=(0.7, 0.35))
        add_btn.bind(on_press=lambda *a: self._do_add_category(name_input.text.strip(), popup))
        cancel_btn.bind(on_press=lambda *a: popup.dismiss())
        popup.open()

    def _do_add_category(self, name, popup):
        if not name:
            return
        ExpenseCategory.create(name)
        self._refresh_categories()
        self.category_spinner.text = name
        popup.dismiss()

    def _save(self, *args):
        category_id = self._category_map.get(self.category_spinner.text)
        if not category_id:
            self.screen.show_error("Select a category.")
            return

        try:
            amount = float(self.amount_input.text or "0")
        except ValueError:
            amount = 0
        if amount <= 0:
            self.screen.show_error("Amount must be > 0.")
            return

        expense_date = self.date_input.text.strip()
        if not expense_date:
            expense_date = date.today().isoformat()

        if self.expense:
            try:
                conn = get_connection()
                conn.execute(
                    "UPDATE expenses SET category_id=?, amount=?, description=?, expense_date=? WHERE id=?",
                    (category_id, amount, self.desc_input.text, expense_date, self.expense["id"]),
                )
                conn.commit()
                conn.close()
            except Exception as e:
                self.screen.show_error(f"DB error: {e}")
                return
        else:
            Expense.create(category_id, amount, self.desc_input.text, expense_date)

        self.popup.dismiss()
        self.screen._rebuild()
