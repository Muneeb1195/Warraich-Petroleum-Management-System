from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty
from kivy.clock import Clock


class RefreshableScrollView(ScrollView):
    refresh_callback = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._refreshing = False
        self._start_y = 0
        self.effect_cls = "ScrollEffect"

    def on_touch_down(self, touch):
        if not touch.is_mouse_scrolling:
            self._start_y = touch.y
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if not self._refreshing and self.refresh_callback and self.scroll_y > 1.05:
            self._refreshing = True
            Clock.schedule_once(self._do_refresh, 0.3)
        return super().on_touch_up(touch)

    def _do_refresh(self, dt):
        try:
            if self.refresh_callback:
                self.refresh_callback()
        finally:
            Clock.schedule_once(self._reset, 0.5)

    def _reset(self, dt):
        self._refreshing = False
        self.scroll_y = 0
