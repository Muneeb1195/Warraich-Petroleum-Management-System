from pathlib import Path
from datetime import datetime
import shutil
import threading
import time

from database.connection import DB_PATH
from database.settings import settings

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backup"


def manual_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"backup_{timestamp}.db"
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_file)
    return backup_file


def _auto_backup_worker():
    while True:
        try:
            interval_days = max(settings.backup_interval_days(), 1)
            backup_dir = Path(__file__).resolve().parent.parent / settings.get("Backup", "backup_dir", "backup/")
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"autobackup_{timestamp}.db"
            if DB_PATH.exists():
                shutil.copy2(DB_PATH, backup_file)
                old_backups = sorted(backup_dir.glob("autobackup_*.db"))
                while len(old_backups) > 10:
                    old_backups[0].unlink()
                    old_backups.pop(0)
        except Exception:
            pass
        time.sleep(interval_days * 86400)


def start_auto_backup():
    t = threading.Thread(target=_auto_backup_worker, daemon=True)
    t.start()
