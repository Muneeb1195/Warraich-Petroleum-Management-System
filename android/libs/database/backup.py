from pathlib import Path
from datetime import datetime
import shutil
import threading
import time

from database.connection import DB_PATH
from database.settings import settings
from utils.paths import data_dir

BACKUP_DIR = data_dir() / "backup"


def _try_cloud_upload(backup_path):
    try:
        from database.cloud_backup import upload_to_drive
        ok, result = upload_to_drive(backup_path)
        if ok:
            print(f"Cloud backup: {result}")
        else:
            print(f"Cloud backup failed: {result}")
    except Exception:
        pass


def manual_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"backup_{timestamp}.db"
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_file)
    if settings.cloud_backup_enabled():
        _try_cloud_upload(backup_file)
    old = sorted(BACKUP_DIR.glob("backup_*.db"))
    while len(old) > 10:
        old[0].unlink()
        old.pop(0)
    return backup_file


def list_local_backups():
    """Return sorted list of backup Paths, newest first."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(BACKUP_DIR.glob("backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def restore_from_local(backup_path):
    """Replace current DB with a local backup. Returns (ok, msg)."""
    p = Path(backup_path)
    if not p.exists():
        return False, "Backup file not found."
    try:
        shutil.copy2(str(p), str(DB_PATH))
        return True, "Local backup restored."
    except Exception as e:
        return False, str(e)


def _auto_backup_worker():
    while True:
        try:
            interval_days = max(settings.backup_interval_days(), 1)
            backup_dir = data_dir() / settings.get("Backup", "backup_dir", "backup/")
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"autobackup_{timestamp}.db"
            if DB_PATH.exists():
                shutil.copy2(DB_PATH, backup_file)
                if settings.cloud_backup_enabled():
                    _try_cloud_upload(backup_file)
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
