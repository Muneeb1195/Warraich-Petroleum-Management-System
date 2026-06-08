from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.clock import Clock

from libs.utils.theme import *
from libs.database.settings import settings


class PinScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pin = ""
        self._mode = "enter"  # "enter" or "set" or "confirm"
        self._set_pin = ""

    def on_enter(self):
        if settings.has_pin():
            self._mode = "enter"
            self.ids.title.text = "Enter PIN"
        else:
            self._mode = "set"
            self._set_pin = ""
            self.ids.title.text = "Set a 4-digit PIN"
        self._pin = ""
        self._update_dots()

    def _update_dots(self):
        dots = ""
        for i in range(4):
            dots += "\u25CF" if i < len(self._pin) else "\u25CB"
            if i < 3:
                dots += "   "
        self.ids.dots.text = dots

    def press(self, digit):
        if len(self._pin) >= 4:
            return
        self._pin += str(digit)
        self._update_dots()
        if len(self._pin) == 4:
            Clock.schedule_once(self._check, 0.2)

    def backspace(self):
        if self._pin:
            self._pin = self._pin[:-1]
            self._update_dots()

    def _check(self, dt):
        if self._mode == "enter":
            if settings.verify_pin(self._pin):
                self.manager.current = "dashboard"
            else:
                self.ids.title.text = "Wrong PIN. Try again."
                self._pin = ""
                self._update_dots()
                Clock.schedule_once(lambda *a: self.ids.title.text or self._reset_title(), 1.5)
        elif self._mode == "set":
            self._set_pin = self._pin
            self._pin = ""
            self._update_dots()
            self._mode = "confirm"
            self.ids.title.text = "Confirm PIN"
        elif self._mode == "confirm":
            if self._pin == self._set_pin:
                settings.set_pin(self._pin)
                self.manager.current = "dashboard"
            else:
                self.ids.title.text = "PINs don't match. Try again."
                self._pin = ""
                self._set_pin = ""
                self._mode = "set"
                self._update_dots()
                Clock.schedule_once(lambda *a: self.ids.title.text or self._reset_title(), 1.5)

    def _reset_title(self):
        if self._mode == "enter":
            self.ids.title.text = "Enter PIN"
        else:
            self.ids.title.text = "Set a 4-digit PIN"
