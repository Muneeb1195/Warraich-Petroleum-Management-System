import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "libs"))

import kivy
kivy.require("2.3.1")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty

from libs.database.connection import init_db
from libs.database.backup import start_auto_backup
from libs.utils.logger import install_exception_hook, show_crash_dialog_if_needed
from ui.pos_screen import PosScreen
from ui.inventory_screen import InventoryScreen
from ui.customers_screen import CustomerScreen
from ui.expenses_screen import ExpenseScreen
from ui.reports_screen import ReportScreen
from ui.staff_screen import StaffScreen
from ui.dashboard_screen import DashboardScreen
from ui.settings_screen import SettingsScreen
from ui.purchases_screen import PurchasesScreen
from ui.reconciliation_screen import ReconciliationScreen
from ui.sales_history_screen import SalesHistoryScreen
from ui.pin_screen import PinScreen

Builder.load_file("ui/main_screen.kv")
Builder.load_file("ui/sales_history_screen.kv")
Builder.load_file("ui/pin_screen.kv")
Builder.load_file("ui/dashboard_screen.kv")
Builder.load_file("ui/pos_screen.kv")
Builder.load_file("ui/inventory_screen.kv")
Builder.load_file("ui/customers_screen.kv")
Builder.load_file("ui/expenses_screen.kv")
Builder.load_file("ui/reports_screen.kv")
Builder.load_file("ui/staff_screen.kv")
Builder.load_file("ui/settings_screen.kv")
Builder.load_file("ui/purchases_screen.kv")
Builder.load_file("ui/reconciliation_screen.kv")


class MainScreen(Screen):
    drawer_open = BooleanProperty(True)
    active_screen = StringProperty("dashboard")

    def toggle_drawer(self):
        self.drawer_open = not self.drawer_open

    def go_to(self, name):
        self.active_screen = name
        self.manager.current = name

    def on_enter(self):
        pass


class WarraichPetroleumApp(App):
    def build(self):
        install_exception_hook()
        Window.softinput_mode = "below_target"
        init_db()
        start_auto_backup()
        Clock.schedule_once(lambda *a: show_crash_dialog_if_needed(), 1)
        sm = ScreenManager()
        sm.add_widget(PinScreen(name="pin"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(PosScreen(name="pos"))
        sm.add_widget(InventoryScreen(name="inventory"))
        sm.add_widget(CustomerScreen(name="customers"))
        sm.add_widget(ExpenseScreen(name="expenses"))
        sm.add_widget(ReportScreen(name="reports"))
        sm.add_widget(StaffScreen(name="staff"))
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(PurchasesScreen(name="purchases"))
        sm.add_widget(SalesHistoryScreen(name="sales_history"))
        sm.add_widget(ReconciliationScreen(name="reconciliation"))
        Clock.schedule_once(lambda *a: setattr(sm, 'current', 'pin'))
        return sm

    def get_application_name(self):
        return "Warraich Petroleum"


if __name__ == "__main__":
    WarraichPetroleumApp().run()
