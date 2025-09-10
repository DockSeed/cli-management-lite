import sqlite3
from datetime import datetime
from pathlib import Path

DB_FILE = Path(__file__).parent.parent / "database" / "stock.db"
DB_FILE.parent.mkdir(exist_ok=True)  # Stelle sicher, dass der Ordner existiert

def get_connection() -> sqlite3.Connection:
    """Datenbankverbindung herstellen."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialisiere die Bestandsdatenbank."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Bewegungsarten
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movement_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    """)
    
    # Standard-Bewegungsarten einfügen
    movement_types = [
        ('eingang', 'Wareneingang'),
        ('ausgang', 'Warenausgang'),
        ('bestellung', 'Neue Bestellung'),
        ('storno', 'Stornierung'),
        ('defekt', 'Als defekt markiert'),
        ('verbaut', 'In Projekt verbaut')
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO movement_types (name, description) VALUES (?, ?)",
        movement_types
    )
    
    # Bestandsbewegungen
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            movement_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            reference_date TEXT,
            notes TEXT,
            FOREIGN KEY (movement_type) REFERENCES movement_types(name)
        )
    """)
    
    conn.commit()
    conn.close()

def add_movement(item_id: int, movement_type: str, quantity: int, notes: str = "", reference_date: str = "") -> int:
    """Neue Bestandsbewegung hinzufügen."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Prüfe ob Bewegungsart existiert
        cur.execute("SELECT 1 FROM movement_types WHERE name = ?", (movement_type,))
        if not cur.fetchone():
            raise ValueError(f"Ungültige Bewegungsart: {movement_type}")
        
        # Füge Bewegung hinzu
        cur.execute(
            """
            INSERT INTO stock_movements (
                item_id, movement_type, quantity, notes, reference_date
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (item_id, movement_type, quantity, notes, reference_date)
        )
        movement_id = cur.lastrowid
        conn.commit()
        return movement_id
    
    finally:
        conn.close()

def get_item_stock(item_id: int) -> dict:
    """Hole aktuellen Bestand und Bewegungen eines Artikels."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Berechne aktuellen Bestand
        cur.execute("""
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN movement_type = 'eingang' THEN quantity
                        WHEN movement_type IN ('ausgang', 'storno', 'defekt', 'verbaut') THEN -quantity
                        ELSE 0
                    END
                ), 0) as current_stock,
                COALESCE(SUM(
                    CASE WHEN movement_type = 'bestellung' THEN quantity ELSE 0 END
                ), 0) as ordered_quantity,
                COALESCE(SUM(
                    CASE WHEN movement_type = 'verbaut' THEN quantity ELSE 0 END
                ), 0) as used_quantity,
                COALESCE(SUM(
                    CASE WHEN movement_type = 'defekt' THEN quantity ELSE 0 END
                ), 0) as defect_quantity
            FROM stock_movements
            WHERE item_id = ?
        """, (item_id,))
        stock_info = dict(cur.fetchone())
        
        # Hole letzte Bewegungen
        cur.execute("""
            SELECT 
                movement_type, quantity, movement_date, reference_date, notes
            FROM stock_movements
            WHERE item_id = ?
            ORDER BY movement_date DESC
            LIMIT 10
        """, (item_id,))
        stock_info['movements'] = [dict(row) for row in cur.fetchall()]
        
        return stock_info
    
    finally:
        conn.close()

def get_low_stock_items(threshold: int = 5) -> list:
    """Finde Artikel mit niedrigem Bestand."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                item_id,
                COALESCE(SUM(
                    CASE 
                        WHEN movement_type = 'eingang' THEN quantity
                        WHEN movement_type IN ('ausgang', 'storno', 'defekt', 'verbaut') THEN -quantity
                        ELSE 0
                    END
                ), 0) as current_stock
            FROM stock_movements
            GROUP BY item_id
            HAVING current_stock <= ?
        """, (threshold,))
        
        return [dict(row) for row in cur.fetchall()]
    
    finally:
        conn.close()


def delete_movements_for_item(item_id: int) -> None:
    """Entfernt alle Bewegungen für einen Artikel (bei Löschung des Artikels)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM stock_movements WHERE item_id = ?", (item_id,))
        conn.commit()
    finally:
        conn.close()
