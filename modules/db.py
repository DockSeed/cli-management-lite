from __future__ import annotations

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent.parent / "database" / "inventory.db"
DB_FILE.parent.mkdir(exist_ok=True)  # Stelle sicher, dass der Ordner existiert

def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def export_db(target: str) -> None:
    """Export database to file."""
    import shutil
    shutil.copy2(DB_FILE, target)

def import_db(source: str) -> None:
    """Import database from file."""
    import shutil
    shutil.copy2(source, DB_FILE)
    # Verify database
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM items")
        cur.execute("SELECT COUNT(*) FROM categories")
    except sqlite3.Error as e:
        # Clean up corrupted file
        DB_FILE.unlink(missing_ok=True)
        raise ValueError(f"Ungültige Datenbankdatei: {e}")
    finally:
        conn.close()

def init_db() -> None:
    """Initialize the database."""
    from . import migrations
    conn = get_connection()
    try:
        migrations.run_migrations(conn)
    finally:
        conn.close()