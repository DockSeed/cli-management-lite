from pathlib import Path
import shutil
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "inventory.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force: bool = False) -> None:
    if DB_PATH.exists():
        if not force:
            return
        confirm = input("Bestehende Datenbank überschreiben? (y/N) ")
        if confirm.lower() != "y":
            print("Abgebrochen.")
            return
        DB_PATH.unlink()
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


def export_db(dest: str) -> None:
    dest_path = Path(dest)
    shutil.copy(DB_PATH, dest_path)


def import_db(src: str) -> None:
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"Quelle {src} existiert nicht")
    if DB_PATH.exists():
        shutil.copy(DB_PATH, DB_PATH.with_suffix(".bak"))
    shutil.copy(src_path, DB_PATH)
