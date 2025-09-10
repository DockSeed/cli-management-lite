"""Grundlegende Datenbankoperationen für das Warenwirtschaftssystem."""
from typing import Optional
from database.db import get_connection


def propose_id() -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM items ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    next_id = 1 if row is None else int(row["id"]) + 1
    return f"{next_id:06d}"


def add_item_interactive() -> None:
    conn = get_connection()
    next_id = propose_id()
    item_id = input(f"ID [{next_id}]: ") or next_id
    name = input("Name: ")
    kategorie = input("Kategorie: ")
    while True:
        try:
            anzahl = int(input("Anzahl: "))
            break
        except ValueError:
            print("Bitte eine ganze Zahl eingeben")
    status = input("Status (bestellt, eingetroffen, verbaut, defekt): ")
    eingesetzt = input("Eingesetzt (optional): ") or None
    notiz = input("Notiz (optional): ") or None
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO items (id, name, kategorie, anzahl, status, eingesetzt, notiz) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (item_id, name, kategorie, anzahl, status, eingesetzt, notiz),
    )
    conn.commit()
    conn.close()
    print("Artikel gespeichert.")


def show_all_items() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, kategorie, anzahl, status FROM items")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("Keine Artikel gefunden.")
        return
    widths = [6, 20, 15, 6, 10]
    headers = ("ID", "Name", "Kategorie", "Anz", "Status")
    line = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("-" * len(line))
    for r in rows:
        print(
            " | ".join(
                str(r[c]).ljust(w)
                for c, w in zip(("id", "name", "kategorie", "anzahl", "status"), widths)
            )
        )


def show_item_by_id(item_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE id=?", (f"{item_id:06d}",))
    row = cur.fetchone()
    conn.close()
    if row:
        for key in row.keys():
            print(f"{key}: {row[key]}")
    else:
        print("Artikel nicht gefunden.")


def update_item(item_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    item_id_str = f"{item_id:06d}"
    cur.execute("SELECT * FROM items WHERE id=?", (item_id_str,))
    row = cur.fetchone()
    if not row:
        print("Artikel nicht gefunden.")
        conn.close()
        return
    print("Leer lassen um Feld unverändert zu lassen.")
    name = input(f"Name [{row['name']}]: ") or row["name"]
    kategorie = input(f"Kategorie [{row['kategorie']}]: ") or row["kategorie"]
    while True:
        anzahl_input = input(f"Anzahl [{row['anzahl']}]: ")
        if not anzahl_input:
            anzahl = row["anzahl"]
            break
        try:
            anzahl = int(anzahl_input)
            break
        except ValueError:
            print("Bitte eine ganze Zahl eingeben")
    status = input(f"Status [{row['status']}]: ") or row["status"]
    eingesetzt = input(f"Eingesetzt [{row['eingesetzt'] or ''}]: ") or row["eingesetzt"]
    notiz = input(f"Notiz [{row['notiz'] or ''}]: ") or row["notiz"]
    cur.execute(
        "UPDATE items SET name=?, kategorie=?, anzahl=?, status=?, eingesetzt=?, notiz=? WHERE id=?",
        (name, kategorie, anzahl, status, eingesetzt, notiz, item_id_str),
    )
    conn.commit()
    conn.close()
    print("Artikel aktualisiert.")


def remove_item(item_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    item_id_str = f"{item_id:06d}"
    cur.execute("SELECT 1 FROM items WHERE id=?", (item_id_str,))
    row = cur.fetchone()
    if not row:
        print("Artikel nicht gefunden.")
        conn.close()
        return
    confirm = input(f"Artikel {item_id_str} wirklich löschen? (y/N) ")
    if confirm.lower() == "y":
        cur.execute("DELETE FROM items WHERE id=?", (item_id_str,))
        conn.commit()
        print("Artikel gelöscht.")
    else:
        print("Abgebrochen.")
    conn.close()
