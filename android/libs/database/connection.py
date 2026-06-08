import sqlite3
from pathlib import Path
from utils.paths import data_dir

DB_DIR = data_dir()
DB_PATH = DB_DIR / "petrol_pump.db"


def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL").fetchone()
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    from database.schema import SCHEMA_SQL
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    # Migrations
    for col, typ in [("voided", "INTEGER DEFAULT 0"), ("voided_at", "TEXT"), ("void_reason", "TEXT")]:
        try:
            conn.execute(f"ALTER TABLE sales ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()
