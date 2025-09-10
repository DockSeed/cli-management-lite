from pathlib import Path
import shutil
import sqlite3


# Pfad zur SQLite-Datenbank
DB_PATH = Path(__file__).resolve().parent / "inventory.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row access by name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialise the database and create the ``items`` table if necessary."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kategorie TEXT NOT NULL,
            anzahl INTEGER NOT NULL,
            status TEXT NOT NULL,
            ort TEXT,
            notiz TEXT,
            datum_bestellt TEXT,
            datum_eingetroffen TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def export_db(dest: str) -> None:
    """Export the current database file to ``dest``."""
    dest_path = Path(dest)
    shutil.copy(DB_PATH, dest_path)


def import_db(src: str) -> None:
    """Import a database from ``src`` replacing the current file.

    The existing database is backed up with the suffix ``.bak`` before it is
    replaced.
    """
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"Quelle {src} existiert nicht")
    if DB_PATH.exists():
        shutil.copy(DB_PATH, DB_PATH.with_suffix(".bak"))
    shutil.copy(src_path, DB_PATH)
