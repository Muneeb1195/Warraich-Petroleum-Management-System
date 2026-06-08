import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp

LOG_DIR = Path(os.environ.get("ANDROID_PRIVATE", "/tmp")) / "logs"
CRASH_MARKER = LOG_DIR / ".last_crash"
LOG_FILE = LOG_DIR / "app.log"
MAX_LOG_SIZE = 512 * 1024


def _ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_error(source, message):
    _ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] ERROR [{source}] {message}\n")
        if LOG_FILE.stat().st_size > MAX_LOG_SIZE:
            _rotate_logs()
    except Exception:
        pass


def _rotate_logs():
    try:
        backup = LOG_FILE.with_suffix(".log.1")
        if backup.exists():
            backup.unlink()
        LOG_FILE.rename(backup)
    except Exception:
        pass


def install_exception_hook():
    _ensure_log_dir()

    def hook(exc_type, exc_value, exc_tb):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            with open(LOG_FILE, "a") as f:
                f.write(f"[{timestamp}] CRASH [{exc_type.__name__}] {exc_value}\n{tb_str}\n")
            with open(CRASH_MARKER, "w") as f:
                f.write(f"{timestamp}\n{exc_type.__name__}: {exc_value}\n")
            if LOG_FILE.stat().st_size > MAX_LOG_SIZE:
                _rotate_logs()
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = hook


def show_crash_dialog_if_needed():
    if not CRASH_MARKER.exists():
        return
    try:
        detail = CRASH_MARKER.read_text().strip()
        CRASH_MARKER.unlink(missing_ok=True)
        Popup(
            title="Previous Crash",
            content=Label(
                text=f"The app crashed on last launch.\n\n{detail}\n\nCheck app.log for details.",
                color=(1, 1, 1, 1), font_size="12sp",
            ),
            size_hint=(0.85, 0.45),
        ).open()
    except Exception:
        pass
