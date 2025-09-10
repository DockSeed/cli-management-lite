from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "inventory.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            kategorie TEXT NOT NULL,
            anzahl INTEGER NOT NULL,
            status TEXT NOT NULL,
            eingesetzt TEXT,
            notiz TEXT
        )
        """
    )
    conn.commit()
    conn.close()
