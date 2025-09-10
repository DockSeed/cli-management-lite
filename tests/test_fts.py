"""Tests for FTS search functionality."""

import os
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from database.db import DB_PATH, init_db, get_connection
from modules.inventory import search_items_fts


def setup_module(module):
    # Ensure a fresh database for testing
    if DB_PATH.exists():
        os.remove(DB_PATH)
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    # Insert test items
    cur.execute(
        "INSERT INTO items (name, kategorie, anzahl, status) VALUES (?, ?, ?, ?)",
        ("ESP32-WROOM", "MCU", 1, "bestellt"),
    )
    cur.execute(
        "INSERT INTO items (name, kategorie, anzahl, status) VALUES (?, ?, ?, ?)",
        ("Arduino Nano", "MCU", 1, "bestellt"),
    )
    conn.commit()
    conn.close()


def test_fts_basic_search():
    results = search_items_fts("ESP32")
    assert len(results) == 1

    results = search_items_fts("ESP32 OR Arduino")
    assert len(results) == 2

    results = search_items_fts('"Arduino Nano"')
    assert results[0]["name"] == "Arduino Nano"

