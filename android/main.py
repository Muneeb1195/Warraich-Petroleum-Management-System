import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "libs"))

import kivy
kivy.require("2.2.0")

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder

from libs.database.connection import init_db
from libs.database.backup import start_auto_backup
from ui.pos_screen import PosScreen
from ui.inventory_screen import InventoryScreen
from ui.customers_screen import CustomerScreen
from ui.expenses_screen import ExpenseScreen
from ui.reports_screen import ReportScreen
from ui.staff_screen import StaffScreen
from ui.dashboard_screen import DashboardScreen

Builder.load_file("ui/main_screen.kv")
Builder.load_file("ui/dashboard_screen.kv")
Builder.load_file("ui/pos_screen.kv")
Builder.load_file("ui/inventory_screen.kv")
Builder.load_file("ui/customers_screen.kv")
Builder.load_file("ui/expenses_screen.kv")
Builder.load_file("ui/reports_screen.kv")
Builder.load_file("ui/staff_screen.kv")


class MainScreen(Screen):
    pass


class WarraichPetroleumApp(App):
    def build(self):
        Window.softinput_mode = "below_target"
        init_db()
        start_auto_backup()
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(PosScreen(name="pos"))
        sm.add_widget(InventoryScreen(name="inventory"))
        sm.add_widget(CustomerScreen(name="customers"))
        sm.add_widget(ExpenseScreen(name="expenses"))
        sm.add_widget(ReportScreen(name="reports"))
        sm.add_widget(StaffScreen(name="staff"))
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.current = "dashboard"
        return sm

    def get_application_name(self):
        return "Warraich Petroleum"


if __name__ == "__main__":
    WarraichPetroleumApp().run()
