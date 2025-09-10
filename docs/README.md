# Dokumentation

## Installation
Python 3.11 oder neuer wird benötigt. Die Pakete `textual` und `tabulate` werden bei Bedarf automatisch installiert oder können mit `pip install -r requirements.txt` vorab installiert werden.

## Nutzung

- `python main.py add` – neuen Artikel interaktiv anlegen
- `python main.py show` – Tabelle aller Artikel anzeigen
- `python main.py show-id <ID>` – Details zu einem Artikel anzeigen
- `python main.py update <ID>` – Artikel bearbeiten
- `python main.py remove <ID>` – Artikel löschen
- `python main.py --version` – Versionsnummer anzeigen
- `python main.py export [--file <pfad>]` – Datenbank exportieren (Standard: `inventory_backup.db`)
- `python main.py import --file <pfad>` – Datenbank importieren (überschreibt bestehende DB)

Die Daten werden in `database/inventory.db` gespeichert. Die Datenbank wird bei der ersten Ausführung automatisch erstellt.

**Hinweis:** Beim Import wird die vorhandene Datenbank überschrieben. Erstelle zuvor ein Backup, z. B. mit dem Befehl `export`.
