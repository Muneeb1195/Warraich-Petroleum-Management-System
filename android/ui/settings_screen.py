import threading

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.metrics import dp

from libs.utils.theme import *
from libs.database.settings import settings
from libs.database import cloud_backup
from libs.database.backup import manual_backup, list_local_backups, restore_from_local


class SettingsScreen(Screen):
    def on_enter(self):
        self._load()
        self._refresh_drive_status()

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

    # --- Google Drive ---

    def _refresh_drive_status(self):
        connected = cloud_backup.is_connected()
        last = settings.last_cloud_backup()
        if connected:
            self.ids.drive_status.text = f"Connected | Last: {last}"
            self.ids.connect_btn.text = "Disconnect"
            self.ids.connect_btn.on_press = self.disconnect_drive
        else:
            self.ids.drive_status.text = "Not connected"
            self.ids.connect_btn.text = "Connect to Drive"
            self.ids.connect_btn.on_press = self.connect_drive

    def connect_drive(self):
        try:
            gauth, url, httpd = cloud_backup.start_auth_flow()
        except Exception as e:
            popup = Popup(title="Error", content=Label(text=str(e), color=TEXT_PRIMARY), size_hint=(0.7, 0.3))
            popup.open()
            return

        import webbrowser
        webbrowser.open(url)

        content = BoxLayout(orientation="vertical", spacing=dp(6), padding=[dp(12), dp(8)])
        steps = (
            "1. A browser window opened — sign in to\n"
            "   your Google account if asked.\n\n"
            "2. Tap \"Continue\" then \"Allow\" to grant\n"
            "   access to Google Drive.\n\n"
            "3. After allowing, the browser will show\n"
            "   a \"This site can't be reached\" page.\n\n"
            "4. Look at the address bar — you'll see\n"
            "   a URL containing code=XXXXXXX\n\n"
            "5. Copy that long code (after code=)\n"
            "   and paste it below, then tap Authenticate."
        )
        content.add_widget(Label(
            text=steps,
            color=TEXT_PRIMARY, halign="left",
            text_size=(dp(300), None),
            font_size="12sp",
        ))
        code_input = TextInput(
            hint_text="Paste the authorization code here",
            multiline=False, size_hint_y=None, height=dp(44),
            foreground_color=TEXT_PRIMARY,
            background_color=(0.15, 0.15, 0.18, 1),
        )
        content.add_widget(code_input)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(44))
        btn_row.add_widget(Button(
            text="Cancel", background_normal="", background_color=BTN_CANCEL, color=TEXT_PRIMARY,
            on_press=lambda *a: (httpd.server_close(), auth_popup.dismiss()),
        ))
        btn_row.add_widget(Button(
            text="Authenticate", background_normal="", background_color=BTN_PRIMARY, color=TEXT_PRIMARY,
            on_press=lambda *a: self._finish_auth(gauth, code_input.text, httpd, auth_popup),
        ))
        content.add_widget(btn_row)

        auth_popup = Popup(title="Google Drive — Authorize", content=content, size_hint=(0.9, 0.65), auto_dismiss=False)
        auth_popup.open()

    def _finish_auth(self, gauth, code, httpd, popup):
        code = code.strip()
        if not code:
            return
        try:
            httpd.server_close()
            cloud_backup.authenticate(gauth, code)
            settings.set_cloud_backup_enabled(True)
            popup.dismiss()
            self._refresh_drive_status()
            Popup(title="Connected", content=Label(text="Google Drive connected.", color=TEXT_PRIMARY), size_hint=(0.6, 0.25)).open()
        except Exception as e:
            Popup(title="Auth Failed", content=Label(text=str(e), color=TEXT_PRIMARY), size_hint=(0.7, 0.3)).open()

    def disconnect_drive(self):
        cloud_backup.disconnect()
        settings.set_cloud_backup_enabled(False)
        self._refresh_drive_status()
        Popup(title="Disconnected", content=Label(text="Google Drive disconnected.", color=TEXT_PRIMARY), size_hint=(0.6, 0.25)).open()

    def drive_backup_now(self):
        if not cloud_backup.is_connected():
            Popup(title="Not Connected", content=Label(text="Connect to Google Drive first.", color=TEXT_PRIMARY), size_hint=(0.6, 0.25)).open()
            return
        self.ids.drive_status.text = "Backing up..."
        def _run():
            manual_backup()
            Clock.schedule_once(lambda *a: self._refresh_drive_status())
            Clock.schedule_once(lambda *a: Popup(
                title="Backup Done", content=Label(text="Backup uploaded to Drive.", color=TEXT_PRIMARY), size_hint=(0.6, 0.25)
            ).open())
        threading.Thread(target=_run, daemon=True).start()

    # --- Restore ---

    def show_cloud_restore(self):
        if not cloud_backup.is_connected():
            Popup(title="Not Connected", content=Label(text="Connect to Google Drive first.", color=TEXT_PRIMARY), size_hint=(0.6, 0.25)).open()
            return
        self._fetch_and_show_drive_backups()

    def _fetch_and_show_drive_backups(self):
        loading = Popup(title="Loading", content=Label(text="Fetching backups...", color=TEXT_PRIMARY), size_hint=(0.6, 0.25))
        loading.open()
        def _run():
            try:
                backups = cloud_backup.list_drive_backups()
                err = None
            except Exception as e:
                backups = None
                err = str(e)
            Clock.schedule_once(lambda *a: loading.dismiss())
            Clock.schedule_once(lambda *a: self._show_drive_backup_list(backups) if backups is not None else
                                Popup(title="Error", content=Label(text=err, color=TEXT_PRIMARY), size_hint=(0.7, 0.3)).open())
        threading.Thread(target=_run, daemon=True).start()

    def _show_drive_backup_list(self, backups):
        if not backups:
            Popup(title="No Backups", content=Label(text="No backups found in Drive.", color=TEXT_PRIMARY), size_hint=(0.6, 0.25)).open()
            return
        layout = BoxLayout(orientation="vertical", spacing=dp(4))
        sv = ScrollView(size_hint=(1, 1))
        gl = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        gl.bind(minimum_height=gl.setter("height"))
        for name, fid in backups:
            btn = Button(
                text=name, size_hint_y=None, height=dp(40),
                background_normal="", background_color=BTN_SECONDARY, color=TEXT_PRIMARY,
                on_press=lambda *a, n=name, f=fid: self._download_and_restore(n, f, picker.dismiss),
            )
            gl.add_widget(btn)
        sv.add_widget(gl)
        layout.add_widget(sv)
        picker = Popup(title="Select Backup to Restore", content=layout, size_hint=(0.85, 0.6))
        picker.open()

    def _download_and_restore(self, name, file_id, dismiss_popup):
        dismiss_popup()
        loading = Popup(title="Restoring", content=Label(text="Downloading...", color=TEXT_PRIMARY), size_hint=(0.6, 0.25))
        loading.open()
        def _run():
            try:
                from libs.utils.paths import data_dir
                tmp = data_dir() / f"restore_{name}"
                ok, msg = cloud_backup.download_from_drive(file_id, tmp)
                if ok:
                    ok2, msg2 = restore_from_local(tmp)
                    tmp.unlink(missing_ok=True)
                    msg = msg2 if ok2 else msg2
                    ok = ok2
            except Exception as e:
                ok, msg = False, str(e)
            Clock.schedule_once(lambda *a: loading.dismiss())
            Clock.schedule_once(lambda *a: (
                Popup(title="Restored" if ok else "Failed",
                      content=Label(text=msg + ("\nRelaunch to apply." if ok else ""), color=TEXT_PRIMARY),
                      size_hint=(0.7, 0.25)).open()
            ))
        threading.Thread(target=_run, daemon=True).start()

    def show_local_restore(self):
        backups = list_local_backups()
        if not backups:
            Popup(title="No Backups", content=Label(text="No local backups found.", color=TEXT_PRIMARY), size_hint=(0.6, 0.25)).open()
            return
        layout = BoxLayout(orientation="vertical", spacing=dp(4))
        sv = ScrollView(size_hint=(1, 1))
        gl = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        gl.bind(minimum_height=gl.setter("height"))
        for p in backups:
            btn = Button(
                text=p.name, size_hint_y=None, height=dp(40),
                background_normal="", background_color=BTN_SECONDARY, color=TEXT_PRIMARY,
                on_press=lambda *a, bp=p: self._restore_local_file(bp, picker.dismiss),
            )
            gl.add_widget(btn)
        sv.add_widget(gl)
        layout.add_widget(sv)
        picker = Popup(title="Select Local Backup", content=layout, size_hint=(0.85, 0.6))
        picker.open()

    def _restore_local_file(self, backup_path, dismiss_popup):
        dismiss_popup()
        ok, msg = restore_from_local(backup_path)
        Popup(
            title="Restored" if ok else "Failed",
            content=Label(text=msg + ("\nRelaunch to apply." if ok else ""), color=TEXT_PRIMARY),
            size_hint=(0.7, 0.25),
        ).open()

    def go_back(self):
        self.manager.current = "main"
