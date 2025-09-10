from __future__ import annotations

import sqlite3


def run_migrations(conn: sqlite3.Connection) -> None:
    """Run database migrations based on PRAGMA user_version.

    This uses an integer schema version stored in ``PRAGMA user_version``. New
    databases are created at the latest version. Older databases are upgraded
    step by step.
    """
    cur = conn.cursor()
    cur.execute("PRAGMA user_version")
    version = cur.fetchone()[0]

    if version < 1:
        _migrate_to_v1(cur)
        version = 1
        cur.execute("PRAGMA user_version = 1")

    if version < 2:
        _migrate_to_v2(conn)
        cur.execute("PRAGMA user_version = 2")
    if version < 3:
        _migrate_to_v3(conn)
        cur.execute("PRAGMA user_version = 3")
    conn.commit()


def _migrate_to_v1(cur: sqlite3.Cursor) -> None:
    """Initial schema with ``items`` table (version 1)."""
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


def _migrate_to_v2(conn: sqlite3.Connection) -> None:
    """Introduce ``categories`` table and ``category_id`` column."""
    cur = conn.cursor()
    # Create categories table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )
    # Add category_id column if it does not exist
    cur.execute("PRAGMA table_info(items)")
    columns = [row[1] for row in cur.fetchall()]
    if "category_id" not in columns:
        cur.execute(
            "ALTER TABLE items ADD COLUMN category_id INTEGER REFERENCES categories(id)"
        )
        # migrate existing category names
        cur.execute("SELECT DISTINCT kategorie FROM items")
        for (name,) in cur.fetchall():
            cur.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (name,),
            )
            cur.execute("SELECT id FROM categories WHERE name=?", (name,))
            cat_id = cur.fetchone()[0]
            cur.execute(
                "UPDATE items SET category_id=? WHERE kategorie=?",
                (cat_id, name),
            )

    conn.commit()


def _migrate_to_v3(conn: sqlite3.Connection) -> None:
    """Add FTS5 virtual table for full-text search."""
    cur = conn.cursor()

    # Create FTS virtual table
    cur.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
            name, kategorie, ort, notiz,
            content='items',
            content_rowid='id',
            tokenize='porter'
        )
        """
    )

    # Index existing data
    cur.execute(
        """
        INSERT INTO items_fts(rowid, name, kategorie, ort, notiz)
        SELECT id, name, kategorie, ort, notiz FROM items
        WHERE name IS NOT NULL
        """
    )

    # Create triggers to keep FTS in sync
    cur.execute(
        """
        CREATE TRIGGER items_fts_insert AFTER INSERT ON items BEGIN
            INSERT INTO items_fts(rowid, name, kategorie, ort, notiz)
            VALUES (NEW.id, NEW.name, NEW.kategorie, NEW.ort, NEW.notiz);
        END
        """
    )

    cur.execute(
        """
        CREATE TRIGGER items_fts_delete AFTER DELETE ON items BEGIN
            DELETE FROM items_fts WHERE rowid = OLD.id;
        END
        """
    )

    cur.execute(
        """
        CREATE TRIGGER items_fts_update AFTER UPDATE ON items BEGIN
            DELETE FROM items_fts WHERE rowid = OLD.id;
            INSERT INTO items_fts(rowid, name, kategorie, ort, notiz)
            VALUES (NEW.id, NEW.name, NEW.kategorie, NEW.ort, NEW.notiz);
        END
        """
    )

    conn.commit()
