from pathlib import Path
import shutil
import sqlite3
import time

import logging

from .migrations import run_migrations

logging.basicConfig(level=logging.INFO)


# Pfad zur SQLite-Datenbank
DB_PATH = Path(__file__).resolve().parent / "inventory.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row access by name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Initialise the database and run migrations if necessary."""
    conn = get_connection()
    run_migrations(conn)
    conn.close()


def export_db(dest: str) -> None:
    """Export the current database file to ``dest``."""
    dest_path = Path(dest)
    shutil.copy(DB_PATH, dest_path)


def import_db(src: str) -> None:
    """Import a database from ``src`` replacing the current file.

    Validates that ``src`` is a SQLite database and restores the previous
    database on failure.
    """
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"Quelle {src} existiert nicht")

    # Validate SQLite file
    try:
        test_conn = sqlite3.connect(src_path)
        test_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        test_conn.close()
    except sqlite3.Error as exc:
        raise ValueError("Datei ist keine gültige SQLite-Datenbank") from exc

    backup_path = None
    if DB_PATH.exists():
        backup_path = DB_PATH.with_suffix(f".bak.{int(time.time())}")
        shutil.copy(DB_PATH, backup_path)
    try:
        shutil.copy(src_path, DB_PATH)
    except Exception as exc:
        if backup_path and backup_path.exists():
            shutil.copy(backup_path, DB_PATH)
        raise RuntimeError(f"Import fehlgeschlagen: {exc}") from exc
