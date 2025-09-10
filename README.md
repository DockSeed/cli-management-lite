Projektname

CLI Warenwirtschaftssytem

Hintergrund

Das Team benötigt ein leichtgewichtiges Werkzeug, um Bastel- und Elektronikbauteile (z. B. ESP32-Boards, Sensoren) im Inventar zu verwalten.
Das Tool soll lokal laufen, ohne komplexe Server oder Web-GUIs. Es muss minimal, verständlich und erweiterbar sein.

Anforderungen:

Datenhaltung

Eine kleine SQLite-Datenbank (inventory.db innerhalb des Ordners Database)

Tabelle items mit Spalten:

id (6 Stellig fortlaufend, vorschlag wir gegeben kann aber überschrieben werden sofern gültiger eintrag. (vergabe eigener ID))

name (Text)

kategorie (Text) bzw warengruppe

anzahl (Zahl)

status (bestellt, eingetroffen, verbaut, defekt)

bei status verbaut, wo (welches Projekt) (Text, optional)

notiz (Text, optional)

Kommandozeilenbefehle:

wws-add: Neuen Artikel hinzufügen (Alle Felder sollen nacheinander ausgefüllt werden, überspringen mit Enter nur bei optionalen Angaben wie Notiz und Einsatz)

wws-show: Tabelle mit allen Artikeln anzeigen

wws-show-id 000001 Zeigt jeweilige id mit allen infos

wws-update: Bestehenden Artikel ändern (z. B. Status oder Anzahl)

wws-remove: Artikel löschen (Abfrage ob wirklich löschen)

Darstellung

Ausgabe im Terminal als einfache ASCII-Tabelle

Klarer Fokus auf Lesbarkeit

Technik

Sprache: Python

Standardbibliothek verwenden (keine externen Dependencies im MVP)

Plattform: Linux (Debian-basiert, CLI)

Nicht-Ziele (jetzt erstmal nicht)

Kein Web-Frontend

Keine Benutzerverwaltung

Keine komplexen Reportings

Kein Netzwerkzugriff