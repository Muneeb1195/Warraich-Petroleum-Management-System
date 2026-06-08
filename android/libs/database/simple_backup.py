import threading
from datetime import datetime
from pathlib import Path

from database.connection import DB_PATH
from database.settings import settings


def upload_db():
    """Upload the SQLite DB file to the configured backup URL via HTTP POST."""
    url = settings.backup_url()
    if not url:
        return False, "No backup URL configured. Set it in Settings."

    if not DB_PATH.exists():
        return False, "Database file not found."

    try:
        import requests
        with open(DB_PATH, "rb") as f:
            resp = requests.post(url, files={"db": f}, timeout=30)
        if resp.ok:
            settings.set("Cloud", "last_cloud_backup", datetime.now().isoformat())
            settings.save()
            return True, "Backup uploaded successfully."
        return False, f"Upload failed: HTTP {resp.status_code}"
    except ImportError:
        return False, "requests library not available."
    except Exception as e:
        return False, str(e)


def upload_db_async(callback=None):
    """Upload DB in a background thread."""

    def _run():
        ok, msg = upload_db()
        if callback:
            callback(ok, msg)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
