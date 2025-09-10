"""Datenbankoperationen für das CLI-Warenwirtschaftssystem."""
from __future__ import annotations

from typing import Any, Optional
from datetime import datetime
from . import db
from .db import get_connection

class ItemValidator:
    @staticmethod
    def validate_amount(value: str) -> int:
        try:
            amount = int(value)
            if amount < 0:
                raise ValueError("Anzahl muss positiv sein")
            if amount > 999999:
                raise ValueError("Anzahl darf maximal 999999 sein")
            return amount
        except ValueError:
            raise ValueError("Ungültige Anzahl")

    @staticmethod
    def validate_name(value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Name darf nicht leer sein")
        return value.strip()

    @staticmethod
    def validate_status(value: str) -> str:
        if value not in VALID_STATUS:
            raise ValueError(f"Status muss einer von {VALID_STATUS} sein")
        return value

    @staticmethod
    def validate_date(value: str) -> str:
        if not value or value == "-":
            return ""
        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError("Datum muss Format YYYY-MM-DD oder DD.MM.YYYY haben")

VALID_STATUS = [
    'bestellt',
    'eingetroffen',
    'verbaut',
    'defekt',
    'nachbestellen'
]


# --- Interaktive CLI-Funktionen -------------------------------------------------

def _prompt(prompt: str, validator) -> Any:
    """Prompt the user for input until ``validator`` accepts the value."""
    while True:
        value = input(prompt)
        try:
            return validator(value)
        except ValueError as exc:
            print(exc)


def validate_int_input(prompt: str, default: int = 1, min_val: int = 1, max_val: int = 999999) -> int:
    """Validiere Ganzzahleneingabe mit Grenzen."""
    while True:
        try:
            value = input(prompt).strip()
            if not value:
                return default
            num = int(value)
            if num < min_val:
                print(f"Wert muss mindestens {min_val} sein")
                continue
            if num > max_val:
                print(f"Wert darf maximal {max_val} sein")
                continue
            return num
        except ValueError:
            print(f"Bitte eine ganze Zahl zwischen {min_val} und {max_val} eingeben")


def add_item_interactive() -> int:
    """Artikel interaktiv hinzufügen."""
    name = input("Name: ").strip()
    if not name:
        raise ValueError("Name ist pflicht")

    # Kategorien anzeigen
    print("\nVerfügbare Kategorien:")
    categories = list_categories()
    if not categories:
        add_category("Standard")
        categories = list_categories()
    
    for cat in categories:
        print(f"{cat['id']}: {cat['name']}")
    
    kategorie_input = input("\nKategorie: ").strip()
    if kategorie_input.isdigit():
        category_id = int(kategorie_input)
        # Hole Kategorie-Namen für das Insert
        for cat in categories:
            if cat['id'] == category_id:
                kategorie = cat['name']
                break
        else:
            kategorie = kategorie_input
            category_id = add_category(kategorie_input)
    else:
        # Neue Kategorie anlegen
        kategorie = kategorie_input
        category_id = add_category(kategorie_input)

    # Status als nummerierte Liste anzeigen
    print("\nVerfügbare Status:")
    for i, status in enumerate(VALID_STATUS, 1):
        print(f"{i}: {status}")
    
    while True:
        status_input = input("\nStatus (1-5): ").strip()
        if status_input.isdigit() and 1 <= int(status_input) <= len(VALID_STATUS):
            status = VALID_STATUS[int(status_input) - 1]
            break
        print(f"Bitte eine Zahl zwischen 1 und {len(VALID_STATUS)} eingeben")

    shop = input("Shop (optional): ").strip()
    notiz = input("Notiz (optional): ").strip()
    if notiz == "-":
        notiz = ""

    def get_date(prompt: str) -> str:
        while True:
            date = input(prompt).strip()
            if not date or date == "-":
                return ""
            try:
                for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                    try:
                        return datetime.strptime(date, fmt).strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                print("Datum muss Format YYYY-MM-DD oder DD.MM.YYYY haben (oder '-' für kein Datum)")
            except ValueError:
                if not date:
                    return ""
                print("Datum muss Format YYYY-MM-DD oder DD.MM.YYYY haben (oder '-' für kein Datum)")

    datum_bestellt = get_date("Datum bestellt (optional): ")
    datum_eingetroffen = get_date("Datum eingetroffen (optional): ")

    # Artikel anlegen
    item_id = add_item({
        "name": name,
        "kategorie": kategorie,
        "category_id": category_id,
        "status": status,
        "shop": shop,
        "notiz": notiz,
        "datum_bestellt": datum_bestellt,
        "datum_eingetroffen": datum_eingetroffen,
    })

    # Initialen Bestand anlegen
    anzahl = validate_int_input("Menge: ", default=1, min_val=1, max_val=999999)
    from . import stock
    movement_type = "bestellung" if status == "bestellt" else "eingang"
    stock.add_movement(
        item_id=item_id,
        movement_type=movement_type,
        quantity=anzahl,
        notes=f"Initiale Menge beim Anlegen",
        reference_date=datum_bestellt if movement_type == "bestellung" else datum_eingetroffen
    )

    return item_id


def show_all_items() -> None:
    """Alle Artikel anzeigen."""
    rows = list_items()
    if not rows:
        print("Keine Artikel vorhanden")
        return

    try:
        from tabulate import tabulate
        from . import stock

        # Formatierte Daten für die Tabelle vorbereiten
        formatted_rows = []
        for row in rows:
            # Konvertiere sqlite3.Row in dict für einfacheren Zugriff
            row_dict = dict(zip(row.keys(), row))
            
            # Hole Bestandsinfo
            stock_info = stock.get_item_stock(row_dict['id'])
            
            # Kürze lange Texte
            name = row_dict['name']
            if len(name) > 20:
                name = name[:17] + "..."
            
            notiz = row_dict.get('notiz', '-')
            if notiz and len(notiz) > 20:
                notiz = notiz[:17] + "..."

            formatted_rows.append({
                'ID': f"{row_dict['id']:06d}",
                'Name': name,
                'Kategorie': row_dict.get('kategorie', 'N/A'),
                'Bestand': stock_info['current_stock'],
                'Bestellt': stock_info['ordered_quantity'],
                'Status': row_dict['status'],
                'Shop': row_dict.get('shop', '-') or '-',
                'Notiz': notiz or '-'
            })

        print(tabulate(
            formatted_rows,
            headers="keys",
            tablefmt="grid",
            numalign="left",
            stralign="left",
            maxcolwidths=[8, 20, 15, 8, 8, 12, 15, 20]
        ))
    except ImportError:
        for row in rows:
            row_dict = dict(zip(row.keys(), row))
            stock_info = stock.get_item_stock(row_dict['id'])
            print(f"{row_dict['id']:6d} | {row_dict['name'][:20]} | {row_dict['kategorie']} | Bestand: {stock_info['current_stock']} | {row_dict['status']}")


def show_item_by_id(item_id: int) -> None:
    """Zeigt alle Informationen zu einem Artikel."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        for key in row.keys():
            print(f"{key}: {row[key]}")
    else:
        print("Artikel nicht gefunden.")


def get_status_from_input(current: str, valid_status: list) -> str:
    """Status mit Autofill-Funktion ermitteln."""
    while True:
        status = input(f"Status [{current}]: ").strip().lower()
        if not status:
            return current
        if status == "-":
            return current
        
        # Exakte Übereinstimmung
        for v in valid_status:
            if status == v.lower():
                return v
        
        # Prefix-Match (Autofill)
        matches = [v for v in valid_status if v.lower().startswith(status)]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            print(f"Mehrdeutig: {', '.join(matches)}")
        else:
            print(f"Status muss einer von {valid_status} sein (oder Anfangsbuchstaben)")


def update_item(item_id: int) -> None:
    """Artikel per ID aktualisieren."""
    item = get_item(item_id)
    if not item:
        print(f"Artikel {item_id} nicht gefunden")
        return

    try:
        conn = get_connection()
        cur = conn.cursor()
        
        print("Leer lassen oder '-' eingeben, um Feld unverändert zu lassen.")
        name = input(f"Name [{item['name']}]: ").strip()
        name = name if name and name != "-" else item['name']

        cur.execute("SELECT id, name FROM categories ORDER BY name")
        categories = {str(row[0]): row[1] for row in cur.fetchall()}
        if not categories:
            add_category("Standard")
            categories = {"1": "Standard"}
        
        print("\nVerfügbare Kategorien:")
        for cat_id, cat_name in categories.items():
            print(f"{cat_id}: {cat_name}")
        
        cat_input = input(f"\nKategorie [{item.get('kategorie', 'Standard')}]: ").strip()
        if cat_input and cat_input.isdigit() and cat_input in categories:
            category_id = int(cat_input)
        else:
            category_id = item.get('category_id')

        anzahl = input(f"Anzahl [{item['anzahl']}]: ").strip()
        try:
            anzahl = int(anzahl) if anzahl and anzahl != "-" else item['anzahl']
        except ValueError:
            print("Ungültige Anzahl, behalte alte Anzahl bei")
            anzahl = item['anzahl']

        status = get_status_from_input(item['status'], VALID_STATUS)

        shop = input(f"Shop [{item.get('shop', '')}]: ").strip()
        shop = shop if shop and shop != "-" else item.get('shop', '')

        def validate_date(date_str: str) -> str:
            if not date_str or date_str == "-":
                return ""
            try:
                for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                    try:
                        return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                raise ValueError
            except ValueError:
                print("Datum muss Format YYYY-MM-DD oder DD.MM.YYYY haben (oder '-' für kein Datum)")
                return None

        while True:
            datum_bestellt = input(f"Bestellt [{item.get('datum_bestellt', '')}]: ").strip()
            if not datum_bestellt or datum_bestellt == "-":
                datum_bestellt = item.get('datum_bestellt', '')
                break
            validated = validate_date(datum_bestellt)
            if validated is not None:
                datum_bestellt = validated
                break

        while True:
            datum_eingetroffen = input(f"Eingetroffen [{item.get('datum_eingetroffen', '')}]: ").strip()
            if not datum_eingetroffen or datum_eingetroffen == "-":
                datum_eingetroffen = item.get('datum_eingetroffen', '')
                break
            validated = validate_date(datum_eingetroffen)
            if validated is not None:
                datum_eingetroffen = validated
                break

        notiz = input(f"Notiz [{item.get('notiz', '')}]: ").strip()
        notiz = notiz if notiz and notiz != "-" else item.get('notiz', '')

        # Update durchführen
        cur.execute(
            """
            UPDATE items SET
                name = ?,
                category_id = ?,
                anzahl = ?,
                status = ?,
                shop = ?,
                notiz = ?,
                datum_bestellt = ?,
                datum_eingetroffen = ?
            WHERE id = ?
            """,
            (
                name,
                category_id,
                anzahl,
                status,
                shop,
                notiz,
                datum_bestellt,
                datum_eingetroffen,
                item_id,
            ),
        )
        conn.commit()
        print(f"Artikel {item_id} aktualisiert")

    except Exception as e:
        print(f"Fehler beim Aktualisieren: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()


def remove_item(item_id: int) -> None:
    """Löscht einen Artikel nach Bestätigung."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    if not row:
        print("Artikel nicht gefunden.")
        conn.close()
        return
    confirm = input(f"Artikel {item_id} wirklich löschen? (y/N) ")
    if confirm.lower() == "y":
        cur.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()
        print("Artikel gelöscht.")
    else:
        print("Abgebrochen.")
    conn.close()


# --- Backend-Funktionen für die TUI --------------------------------------------

def list_items(sort_by: str = "id", descending: bool = False) -> list[Any]:
    """Gibt alle Artikel sortiert nach ``sort_by`` zurück."""
    allowed = {"id", "name", "status", "kategorie", "anzahl"}
    if sort_by not in allowed:
        sort_by = "id"
    order = "DESC" if descending else "ASC"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM items ORDER BY {sort_by} {order}")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_item(item_id: int) -> Optional[dict[str, Any]]:
    """Liefert einen Artikel als Dictionary oder ``None``."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_item(data: dict) -> int:
    """Artikel hinzufügen."""
    if not data.get("status"):
        data["status"] = "bestellt"
    elif data["status"] not in VALID_STATUS:
        raise ValueError(f"Status muss einer von {VALID_STATUS} sein")

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Prüfe/Setze Kategorie
        if not data.get("category_id"):
            # Standardkategorie
            cur.execute("SELECT id FROM categories WHERE name='Standard'")
            result = cur.fetchone()
            if result:
                data["category_id"] = result[0]
            else:
                data["category_id"] = add_category("Standard")

        # Hole Kategorie-Namen wenn nicht vorhanden
        if not data.get("kategorie"):
            cur.execute("SELECT name FROM categories WHERE id = ?", (data["category_id"],))
            result = cur.fetchone()
            if result:
                data["kategorie"] = result[0]
            else:
                data["kategorie"] = "Standard"

        # Validiere Pflichtfelder
        if not data.get("name"):
            raise ValueError("Name ist pflicht")
            
        # Validiere Datumsformate
        for date_field in ["datum_bestellt", "datum_eingetroffen"]:
            if data.get(date_field) == "-":
                data[date_field] = ""
            elif data.get(date_field):
                try:
                    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                        try:
                            date = datetime.strptime(data[date_field], fmt)
                            data[date_field] = date.strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue
                    else:
                        raise ValueError
                except ValueError:
                    raise ValueError(f"Ungültiges Datumsformat für {date_field}")

        cur.execute(
            """
            INSERT INTO items (
                name, kategorie, category_id, status, shop,
                notiz, datum_bestellt, datum_eingetroffen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data["kategorie"],
                data["category_id"],
                data["status"],
                data.get("shop", ""),
                data.get("notiz", ""),
                data.get("datum_bestellt", ""),
                data.get("datum_eingetroffen", ""),
            ),
        )
        
        item_id = cur.lastrowid
        conn.commit()
        return item_id

    finally:
        conn.close()


def update_item_fields(item_id: int, data: dict[str, Any]) -> None:
    """Aktualisiert die angegebenen Felder eines Artikels."""
    if not data:
        return
    conn = get_connection()
    cur = conn.cursor()
    fields = []
    values: list[Any] = []

    category_id = data.pop("category_id", None)
    if category_id is not None:
        category_id = int(category_id)
        cur.execute("SELECT name FROM categories WHERE id=?", (category_id,))
        row = cur.fetchone()
        if row:
            fields.append("category_id=?")
            values.append(category_id)
            fields.append("kategorie=?")
            values.append(row["name"])

    for key, value in data.items():
        if key == "anzahl" and value is not None:
            value = ItemValidator.validate_amount(str(value))
        elif key == "name" and value is not None:
            value = ItemValidator.validate_name(value)
        elif key == "status" and value is not None:
            value = ItemValidator.validate_status(value)
        elif key in {"datum_bestellt", "datum_eingetroffen"} and value is not None:
            value = ItemValidator.validate_date(value)
        fields.append(f"{key}=?")
        values.append(value)
    values.append(item_id)
    cur.execute(f"UPDATE items SET {', '.join(fields)} WHERE id=?", values)
    conn.commit()
    conn.close()


def remove_item_by_id(item_id: int) -> None:
    """Löscht einen Artikel anhand seiner ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def search_items(search_term: str) -> list[dict]:
    """Full-text search with FTS5 and LIKE fallback."""
    if not search_term.strip():
        return list_items()

    # Try FTS first
    fts_results = search_items_fts(search_term)
    if fts_results:
        return fts_results

    # Fallback to LIKE search
    return search_items_like(search_term)


def search_items_fts(search_term: str) -> list[dict]:
    """Advanced FTS5 search with ranking."""
    conn = get_connection()
    cur = conn.cursor()

    escaped_term = search_term.replace('"', '""')

    try:
        cur.execute(
            """
            SELECT items.*, items_fts.rank
            FROM items_fts 
            JOIN items ON items.id = items_fts.rowid
            WHERE items_fts MATCH ?
            ORDER BY items_fts.rank
            LIMIT 50
            """,
            (escaped_term,),
        )
        results = cur.fetchall()

        if not results and not any(op in search_term for op in ['"', '*', 'OR', 'AND']):
            wildcard_term = f"{escaped_term}*"
            cur.execute(
                """
                SELECT items.*, items_fts.rank
                FROM items_fts 
                JOIN items ON items.id = items_fts.rowid
                WHERE items_fts MATCH ?
                ORDER BY items_fts.rank
                LIMIT 50
                """,
                (wildcard_term,),
            )
            results = cur.fetchall()

    except Exception:
        results = []

    conn.close()
    return [dict(row) for row in results]


def search_items_like(search_term: str) -> list[dict]:
    """Fallback LIKE search (original implementation)."""
    conn = get_connection()
    cur = conn.cursor()
    pattern = f"%{search_term}%"
    cur.execute(
        """
        SELECT * FROM items
        WHERE name LIKE ? OR kategorie LIKE ? OR status LIKE ?
           OR notiz LIKE ? OR shop LIKE ?
        ORDER BY id
        """,
        (pattern, pattern, pattern, pattern, pattern),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_items_by_filter(kategorie: str | None = None, status: str | None = None) -> list[dict]:
    """Gefilterte Artikelliste"""
    conn = get_connection()
    cur = conn.cursor()
    where = []
    params: list[Any] = []
    if kategorie:
        where.append("kategorie = ?")
        params.append(kategorie)
    if status:
        where.append("status = ?")
        params.append(status)
    where_clause = " AND ".join(where)
    if where_clause:
        where_clause = "WHERE " + where_clause
    cur.execute(
        f"SELECT * FROM items {where_clause} ORDER BY id",
        params,
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_categories() -> list[dict]:
    """Alle Kategorien laden."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_category(name: str) -> int:
    """Neue Kategorie anlegen und ID zurückgeben."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    cat_id = cur.lastrowid
    conn.close()
    return cat_id
