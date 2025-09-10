import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "database" / "inventory.db"

def main():
    print(f"DB path: {DB}")
    print(f"Exists: {DB.exists()}")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("PRAGMA user_version")
    print("user_version:", cur.fetchone()[0])
    print("tables:")
    for name, sql in cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'"):
        print(" -", name)
    try:
        cur.execute("PRAGMA table_info(items)")
        print("items columns:", [row[1] for row in cur.fetchall()])
    except Exception as e:
        print("items table error:", e)
    print("triggers:")
    for name, tbl in cur.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='trigger'"):
        print(" -", name, "on", tbl)
    conn.close()

if __name__ == "__main__":
    main()
