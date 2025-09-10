# CLI Management Lite

Ein leichtgewichtiges Warenwirtschaftssystem (WWS) für Bastel- und Elektronikkomponenten. Die Anwendung läuft rein lokal und kann sowohl über die Kommandozeile als auch über eine Textoberfläche (TUI) bedient werden.

## Quickstart

```bash
git clone https://github.com/DockSeed/cli-management-lite.git
cd cli-management-lite
python main.py tui
```

Die benötigten Pakete `textual` und `tabulate` werden beim ersten Start automatisch installiert. Alternativ können sie auch über `pip install -r requirements.txt` vorab installiert werden.

## Nutzung

- `python main.py add` – neuen Artikel interaktiv anlegen
- `python main.py show` – Tabelle aller Artikel anzeigen
- `python main.py show-id <ID>` – Details zu einem Artikel anzeigen
- `python main.py update <ID>` – Artikel bearbeiten
- `python main.py remove <ID>` – Artikel löschen
- `python main.py tui` – Textoberfläche starten

## TUI

```
┌───────────────┬─────────────────────────────┐
│ Menü          │ Artikel-Details             │
│ > Add         │ ID: 3                       │
│   Update      │ Name: ESP32-WROOM           │
│   Remove      │ Kategorie: MCU              │
│   Show        │ Anzahl: 5                   │
│   Quit        │ Status: eingetroffen        │
│               │ Ort: Schublade A2           │
│ Artikel:      │ Notiz: AliExpress           │
│ [1] ESP32-S3  │ Bestellt: 2025-09-01        │
│ [2] DHT22     │ Eingetroffen: 2025-09-09    │
│ [3] ESP32-WR… │                             │
└───────────────┴─────────────────────────────┘
Status: [↑↓] Navigieren | [Tab] Wechseln | [Enter] Ausführen | [q] Beenden
```

Die TUI synchronisiert die Artikelliste mit der Detailansicht. Oberhalb der Tabelle befindet sich ein Suchfeld zur Live-Filterung. Navigation erfolgt mit den Pfeiltasten, `Tab` wechselt den Fokus, `Enter` führt Aktionen aus, `Ctrl+F` fokussiert die Suche, `q` beendet.

## Lizenz

MIT
