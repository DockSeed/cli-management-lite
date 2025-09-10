"""Datenbankoperationen für das CLI-Warenwirtschaftssystem."""
from __future__ import annotations

from typing import Any, Optional

from database.db import get_connection


# --- Interaktive CLI-Funktionen -------------------------------------------------

def add_item_interactive() -> None:
    """Interaktive Eingabe eines Artikels und Speicherung in der Datenbank."""
    conn = get_connection()
    name = input("Name: ")
    kategorie = input("Kategorie: ")
    anzahl = int(input("Anzahl: "))
    status = input("Status (bestellt, eingetroffen, verbaut, defekt): ")
    ort = input("Ort (optional): ") or None
    notiz = input("Notiz (optional): ") or None
    datum_bestellt = input("Datum bestellt (optional): ") or None
    datum_eingetroffen = input("Datum eingetroffen (optional): ") or None
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
    from tabulate import tabulate

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
    name = input(f"Name [{row['name']}]: ") or row["name"]
    kategorie = input(f"Kategorie [{row['kategorie']}]: ") or row["kategorie"]
    anzahl_input = input(f"Anzahl [{row['anzahl']}]: ")
    anzahl = int(anzahl_input) if anzahl_input else row["anzahl"]
    status = input(f"Status [{row['status']}]: ") or row["status"]
    ort = input(f"Ort [{row['ort'] or ''}]: ") or row["ort"]
    notiz = input(f"Notiz [{row['notiz'] or ''}]: ") or row["notiz"]
    datum_bestellt = input(f"Bestellt [{row['datum_bestellt'] or ''}]: ") or row["datum_bestellt"]
    datum_eingetroffen = input(
        f"Eingetroffen [{row['datum_eingetroffen'] or ''}]: "
    ) or row["datum_eingetroffen"]
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO items
            (name, kategorie, anzahl, status, ort, notiz, datum_bestellt, datum_eingetroffen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["name"],
            data["kategorie"],
            int(data["anzahl"]),
            data["status"],
            data.get("ort"),
            data.get("notiz"),
            data.get("datum_bestellt"),
            data.get("datum_eingetroffen"),
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
            value = int(value)
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
