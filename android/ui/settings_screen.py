from kivy.uix.screenmanager import Screen
from libs.utils.theme import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.metrics import dp
from libs.database.settings import settings
from libs.database.simple_backup import upload_db_async


class SettingsScreen(Screen):
    def on_enter(self):
        self._load()

    def _load(self):
        self.ids.biz_name.text = settings.business_name()
        self.ids.biz_address.text = settings.business_address()
        self.ids.biz_phone.text = settings.business_phone()
        self.ids.biz_gstin.text = settings.gstin()
        self.ids.petrol_rate.text = str(settings.fuel_rate("petrol"))
        self.ids.diesel_rate.text = str(settings.fuel_rate("diesel"))
        self.ids.default_gst.text = str(settings.default_gst_rate())
        self.ids.hsn_petrol.text = settings.hsn_code("petrol")
        self.ids.hsn_diesel.text = settings.hsn_code("diesel")
        self.ids.hsn_lube.text = settings.hsn_code("lube")
        self.ids.currency_symbol.text = settings.currency_symbol()
        date_fmt = settings.date_format()
        self.ids.date_format.text = date_fmt
        self.ids.backup_url.text = settings.backup_url()
        self.ids.backup_status.text = f"Last: {settings.last_cloud_backup()}"
        self.ids.printer_host.text = settings.printer_host()
        self.ids.printer_port.text = str(settings.printer_port())

    def save(self):
        settings.set_business_info(
            self.ids.biz_name.text.strip(),
            self.ids.biz_address.text.strip(),
            self.ids.biz_phone.text.strip(),
            self.ids.biz_gstin.text.strip(),
        )
        try:
            settings.set_fuel_rate("petrol", float(self.ids.petrol_rate.text or "0"))
        except ValueError:
            pass
        try:
            settings.set_fuel_rate("diesel", float(self.ids.diesel_rate.text or "0"))
        except ValueError:
            pass
        settings.set("GST", "default_rate", self.ids.default_gst.text or "18")
        settings.set("GST", "hsn_petrol", self.ids.hsn_petrol.text.strip())
        settings.set("GST", "hsn_diesel", self.ids.hsn_diesel.text.strip())
        settings.set("GST", "hsn_lube", self.ids.hsn_lube.text.strip())
        settings.set("Regional", "currency_symbol", self.ids.currency_symbol.text.strip() or "Rs.")
        settings.set("Regional", "date_format", self.ids.date_format.text.strip() or "DD/MM/YYYY")
        settings.set("Cloud", "backup_url", self.ids.backup_url.text.strip())
        host = self.ids.printer_host.text.strip()
        port = self.ids.printer_port.text.strip() or "9100"
        settings.set_printer(host, port)
        settings.save()

        popup = Popup(
            title="Saved",
            content=Label(text="Settings saved.", color=TEXT_PRIMARY),
            size_hint=(0.6, 0.25),
        )
        popup.open()

    def backup_now(self):
        self.ids.backup_status.text = "Uploading..."
        upload_db_async(callback=lambda ok, msg: self._on_backup_result(ok, msg))

    def _on_backup_result(self, ok, msg):
        self.ids.backup_status.text = f"Last: {settings.last_cloud_backup()}" if ok else f"Failed: {msg}"
        popup = Popup(
            title="Backup" if ok else "Backup Failed",
            content=Label(text=msg, color=TEXT_PRIMARY),
            size_hint=(0.7, 0.25),
        )
        popup.open()

    def go_back(self):
        self.manager.current = "main"
