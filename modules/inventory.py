"""Datenbankoperationen für das CLI-Warenwirtschaftssystem."""
from __future__ import annotations

from typing import Any, Optional

from .validators import ItemValidator

from database.db import get_connection


# --- Interaktive CLI-Funktionen -------------------------------------------------

def _prompt(prompt: str, validator) -> Any:
    """Prompt the user for input until ``validator`` accepts the value."""
    while True:
        value = input(prompt)
        try:
            return validator(value)
        except ValueError as exc:
            print(exc)


def add_item_interactive() -> None:
    """Interaktive Eingabe eines Artikels und Speicherung in der Datenbank."""
    conn = get_connection()
    name = _prompt("Name: ", ItemValidator.validate_name)
    kategorie = input("Kategorie: ")
    anzahl = _prompt("Anzahl: ", ItemValidator.validate_amount)
    status = _prompt(
        "Status (bestellt, eingetroffen, verbaut, defekt): ",
        ItemValidator.validate_status,
    )
    ort = input("Ort (optional): ") or None
    notiz = input("Notiz (optional): ") or None
    datum_bestellt = _prompt(
        "Datum bestellt (optional): ", ItemValidator.validate_date
    ) or None
    datum_eingetroffen = _prompt(
        "Datum eingetroffen (optional): ", ItemValidator.validate_date
    ) or None
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO items
            (name, kategorie, anzahl, status, ort, notiz, datum_bestellt, datum_eingetroffen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, kategorie, anzahl, status, ort, notiz, datum_bestellt, datum_eingetroffen),
    )
    conn.commit()
    conn.close()
    print("Artikel gespeichert.")


def show_all_items() -> None:
    """Gibt alle Artikel als ASCII-Tabelle aus."""
    try:
        from tabulate import tabulate
    except ImportError:
        print("Das Paket 'tabulate' ist nicht installiert. Bitte installieren und erneut versuchen.")
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, kategorie, anzahl, status FROM items")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("Keine Artikel gefunden.")
        return
    table = tabulate(rows, headers="keys", tablefmt="github")
    print(table)


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


def update_item(item_id: int) -> None:
    """Interaktives Bearbeiten eines Artikels."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE id=?", (item_id,))
    row = cur.fetchone()
    if not row:
        print("Artikel nicht gefunden.")
        conn.close()
        return
    print("Leer lassen, um Feld unverändert zu lassen.")
    name = _prompt(
        f"Name [{row['name']}]: ",
        lambda v: ItemValidator.validate_name(v or row["name"]),
    )
    kategorie = input(f"Kategorie [{row['kategorie']}]: ") or row["kategorie"]
    anzahl_input = input(f"Anzahl [{row['anzahl']}]: ")
    anzahl = (
        ItemValidator.validate_amount(anzahl_input)
        if anzahl_input
        else row["anzahl"]
    )
    status = _prompt(
        f"Status [{row['status']}]: ",
        lambda v: ItemValidator.validate_status(v or row["status"]),
    )
    ort = input(f"Ort [{row['ort'] or ''}]: ") or row["ort"]
    notiz = input(f"Notiz [{row['notiz'] or ''}]: ") or row["notiz"]
    datum_bestellt = _prompt(
        f"Bestellt [{row['datum_bestellt'] or ''}]: ",
        lambda v: ItemValidator.validate_date(v or row["datum_bestellt"] or "")
        or row["datum_bestellt"],
    )
    datum_eingetroffen = _prompt(
        f"Eingetroffen [{row['datum_eingetroffen'] or ''}]: ",
        lambda v: ItemValidator.validate_date(v or row["datum_eingetroffen"] or "")
        or row["datum_eingetroffen"],
    )
    cur.execute(
        """
        UPDATE items SET
            name=?, kategorie=?, anzahl=?, status=?, ort=?, notiz=?,
            datum_bestellt=?, datum_eingetroffen=?
        WHERE id=?
        """,
        (
            name,
            kategorie,
            anzahl,
            status,
            ort,
            notiz,
            datum_bestellt,
            datum_eingetroffen,
            item_id,
        ),
    )
    conn.commit()
    conn.close()
    print("Artikel aktualisiert.")


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

def list_items() -> list[Any]:
    """Gibt alle Artikel sortiert nach ID zurück."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items ORDER BY id")
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


def add_item(data: dict[str, Any]) -> int:
    """Fügt einen neuen Artikel hinzu und gibt die ID zurück."""
    validated = {
        "name": ItemValidator.validate_name(data["name"]),
        "kategorie": data["kategorie"],
        "anzahl": ItemValidator.validate_amount(str(data["anzahl"])),
        "status": ItemValidator.validate_status(data["status"]),
        "ort": data.get("ort"),
        "notiz": data.get("notiz"),
        "datum_bestellt": ItemValidator.validate_date(data.get("datum_bestellt", "")) or None,
        "datum_eingetroffen": ItemValidator.validate_date(
            data.get("datum_eingetroffen", "")
        ) or None,
    }
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO items
            (name, kategorie, anzahl, status, ort, notiz, datum_bestellt, datum_eingetroffen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            validated["name"],
            validated["kategorie"],
            validated["anzahl"],
            validated["status"],
            validated["ort"],
            validated["notiz"],
            validated["datum_bestellt"],
            validated["datum_eingetroffen"],
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_item_fields(item_id: int, data: dict[str, Any]) -> None:
    """Aktualisiert die angegebenen Felder eines Artikels."""
    if not data:
        return
    conn = get_connection()
    cur = conn.cursor()
    fields = []
    values: list[Any] = []
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
    """Suche in Name, Kategorie, Status, Notizen und Ort."""
    conn = get_connection()
    cur = conn.cursor()
    pattern = f"%{search_term}%"
    cur.execute(
        """
        SELECT * FROM items
        WHERE name LIKE ? OR kategorie LIKE ? OR status LIKE ?
           OR notiz LIKE ? OR ort LIKE ?
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


def get_categories() -> list[dict]:
    """Alle Kategorien laden (distinct Werte der Spalte ``kategorie``)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT kategorie AS name FROM items ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
