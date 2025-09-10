from __future__ import annotations

import sqlite3

def _migrate_to_v1(cur: sqlite3.Cursor) -> None:
    """Initial schema with ``items`` table (version 1)."""
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kategorie TEXT NOT NULL,
            anzahl INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            shop TEXT,
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

def _migrate_to_v3(conn: sqlite3.Connection) -> None:
    """Add FTS5 virtual table for full-text search."""
    cur = conn.cursor()
    # Create FTS virtual table
    cur.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
            name, kategorie, shop, notiz,
            content='items',
            content_rowid='id',
            tokenize='porter'
        )
        """
    )

    # Index existing data
    cur.execute(
        """
        INSERT INTO items_fts(rowid, name, kategorie, shop, notiz)
        SELECT id, name, kategorie, shop, notiz FROM items
        WHERE name IS NOT NULL
        """
    )

    # Create triggers to keep FTS in sync
    cur.execute(
        """
        CREATE TRIGGER items_fts_insert AFTER INSERT ON items BEGIN
            INSERT INTO items_fts(rowid, name, kategorie, shop, notiz)
            VALUES (NEW.id, NEW.name, NEW.kategorie, NEW.shop, NEW.notiz);
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
            INSERT INTO items_fts(rowid, name, kategorie, shop, notiz)
            VALUES (NEW.id, NEW.name, NEW.kategorie, NEW.shop, NEW.notiz);
        END
        """
    )

def _migrate_to_v4(conn: sqlite3.Connection) -> None:
    """Start item IDs at ``100000`` for professional six-digit numbering."""
    cur = conn.cursor()
    cur.execute("SELECT MAX(id) FROM items")
    max_id = cur.fetchone()[0]
    if max_id is None or max_id < 100000:
        cur.execute(
            """
            INSERT OR REPLACE INTO sqlite_sequence (name, seq)
            VALUES ('items', 99999)
            """
        )

def _migrate_to_v5(conn: sqlite3.Connection) -> None:
    """Rename 'ort' column to 'shop' and update FTS."""
    cur = conn.cursor()
    
    # Prüfe ob die Spalte 'ort' noch existiert und 'shop' noch nicht
    cur.execute("PRAGMA table_info(items)")
    columns = {row[1] for row in cur.fetchall()}
    
    if 'ort' in columns and 'shop' not in columns:
        # Erstelle temporäre Tabelle
        cur.execute(
            """
            CREATE TABLE items_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                kategorie TEXT NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                anzahl INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                shop TEXT,
                notiz TEXT,
                datum_bestellt TEXT,
                datum_eingetroffen TEXT
            )
            """
        )
        
        # Kopiere Daten und benenne dabei 'ort' zu 'shop' um
        cur.execute(
            """
            INSERT INTO items_new (
                id, name, kategorie, category_id, anzahl, status, shop, notiz,
                datum_bestellt, datum_eingetroffen
            )
            SELECT id, name, kategorie, category_id, anzahl, status, ort, notiz,
                   datum_bestellt, datum_eingetroffen
            FROM items
            """
        )
        
        # Lösche alte Tabelle und benenne neue um
        cur.execute("DROP TABLE items")
        cur.execute("ALTER TABLE items_new RENAME TO items")

def _migrate_to_v6(conn: sqlite3.Connection) -> None:
    """Add stock management tables."""
    cur = conn.cursor()
    
    # Create stock movements table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER REFERENCES items(id),
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            movement_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            reference_date TEXT,
            notes TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    
    # Create index for better performance
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_item ON stock_movements(item_id)")
    
    # Migrate existing stock data
    cur.execute("""
        INSERT INTO stock_movements (
            item_id, movement_type, quantity, reference_date, notes
        )
        SELECT 
            id,
            CASE 
                WHEN status IN ('verbaut', 'defekt') THEN 'ausgang'
                WHEN status = 'bestellt' THEN 'bestellung'
                ELSE 'eingang'
            END,
            anzahl,
            CASE 
                WHEN status = 'bestellt' THEN datum_bestellt
                ELSE datum_eingetroffen
            END,
            'Initial stock migration'
        FROM items
    """)

def run_migrations(conn: sqlite3.Connection) -> None:
    """Run database migrations based on PRAGMA user_version."""
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
    if version < 4:
        _migrate_to_v4(conn)
        cur.execute("PRAGMA user_version = 4")
    if version < 5:
        _migrate_to_v5(conn)
        cur.execute("PRAGMA user_version = 5")
    if version < 6:
        _migrate_to_v6(conn)
        cur.execute("PRAGMA user_version = 6")
    conn.commit()