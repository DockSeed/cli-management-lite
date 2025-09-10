import argparse
import sys

from modules.db import init_db, export_db, import_db
from modules import inventory, stock

VERSION = "0.1"


def add_command(_):
    inventory.add_item_interactive()


def show_command(_):
    inventory.show_all_items()


def show_id_command(args):
    inventory.show_item_by_id(args.id)


def update_command(args):
    inventory.update_item(args.id)


def remove_command(args):
    inventory.remove_item(args.id)


def export_command(args):
    export_db(args.file)
    print(f"Datenbank nach {args.file} exportiert")


def import_command(args):
    try:
        import_db(args.file)
        print(f"Datenbank aus {args.file} importiert")
    except Exception as exc:
        print(f"Fehler beim Import: {exc}")


def tui_command(args: argparse.Namespace) -> None:
    """Start TUI."""
    try:
        from modules import tui
        from modules.db import init_db
        from modules import stock
        
        # Initialize databases
        init_db()
        stock.init_db()
        
        # Start TUI
        tui.main()
    except ImportError as exc:
        print(f"TUI konnte nicht geladen werden: {exc}")
        return


def search_command(args):
    results = inventory.search_items(args.term)
    if not results:
        print("Keine Artikel gefunden.")
        return
    try:
        from tabulate import tabulate
    except ImportError:
        print(results)
        return
    print(tabulate(results, headers="keys", tablefmt="github"))


def advanced_search_command(args):
    """Advanced FTS search with examples."""
    if not args.query:
        print("FTS Search Examples:")
        print('  python main.py fts "exact phrase"')
        print("  python main.py fts 'ESP32 OR Arduino'")
        print("  python main.py fts 'mikro* AND sensor'")
        print("  python main.py fts 'NOT defekt'")
        return

    results = inventory.search_items_fts(args.query)
    if not results:
        print(f"No FTS results for: {args.query}")
        print("Trying fallback search...")
        results = inventory.search_items_like(args.query)

    if not results:
        print("No results found.")
        return

    try:
        from tabulate import tabulate
        print(f"Found {len(results)} results:")
        headers = list(results[0].keys())
        print(tabulate(results, headers=headers, tablefmt="github"))
    except ImportError:
        for item in results:
            print(f"ID {item['id']}: {item['name']} ({item['kategorie']})")


def filter_command(args):
    items = inventory.get_items_by_filter(args.category, args.status)
    if not items:
        print("Keine Artikel gefunden.")
        return
    try:
        from tabulate import tabulate
    except ImportError:
        print(items)
        return
    print(tabulate(items, headers="keys", tablefmt="github"))


def categories_list_command(_):
    cats = inventory.list_categories()
    if not cats:
        print("Keine Kategorien")
        return
    for cat in cats:
        print(f"{cat['id']}: {cat['name']}")


def categories_add_command(args):
    cat_id = inventory.add_category(args.name)
    print(f"Kategorie '{args.name}' angelegt (ID {cat_id})")


def stock_add_command(args):
    """Bestandsbewegung hinzufügen."""
    try:
        stock.add_movement(
            args.item_id,
            args.type,
            args.quantity,
            args.notes,
            args.reference_date
        )
        print(f"Bestandsbewegung für Artikel {args.item_id} hinzugefügt")
    except Exception as e:
        print(f"Fehler: {e}")


def stock_show_command(args):
    """Bestandsinformationen anzeigen."""
    try:
        # Hole Artikel- und Bestandsinformationen
        from modules import inventory
        item = inventory.get_item(args.item_id)
        if not item:
            print(f"Artikel {args.item_id} nicht gefunden")
            return

        info = stock.get_item_stock(args.item_id)
        print(f"\nArtikel: {item['name']} (ID: {args.item_id})")
        print(f"Kategorie: {item['kategorie']}")
        print(f"Status: {item['status']}")
        print(f"Shop: {item.get('shop', '-')}")
        print(f"\nBestandsinformationen:")
        print(f"Aktueller Bestand: {info['current_stock']}")
        print(f"Bestellt: {info['ordered_quantity']}")
        print(f"Verbaut: {info['used_quantity']}")
        print(f"Defekt: {info['defect_quantity']}")
        
        if info['movements']:
            print("\nLetzte Bewegungen:")
            try:
                from tabulate import tabulate
                print(tabulate(info['movements'], headers="keys", tablefmt="grid"))
            except ImportError:
                for m in info['movements']:
                    print(f"{m['movement_date']}: {m['movement_type']} {m['quantity']} {m['notes']}")
    except Exception as e:
        print(f"Fehler: {e}")


def stock_low_command(args):
    """Artikel mit niedrigem Bestand anzeigen."""
    try:
        items = stock.get_low_stock_items(args.threshold)
        if not items:
            print("Keine Artikel mit niedrigem Bestand gefunden")
            return
        
        print(f"\nArtikel mit Bestand <= {args.threshold}:")
        try:
            from tabulate import tabulate
            print(tabulate(items, headers="keys", tablefmt="grid"))
        except ImportError:
            for item in items:
                print(f"ID {item['item_id']}: {item['current_stock']}")
    except Exception as e:
        print(f"Fehler: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI Warenwirtschaftssystem",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command")

    # Artikel-Management
    add_cmd = subparsers.add_parser("add", help="Neuen Artikel hinzufügen")
    add_cmd.set_defaults(func=add_command)

    show_cmd = subparsers.add_parser("show", help="Alle Artikel anzeigen")
    show_cmd.set_defaults(func=show_command)

    show_id_cmd = subparsers.add_parser("show-id", help="Artikel per ID anzeigen")
    show_id_cmd.add_argument("id", type=int, help="Artikel-ID (6-stellig)")
    show_id_cmd.set_defaults(func=show_id_command)

    update_cmd = subparsers.add_parser("update", help="Artikel aktualisieren")
    update_cmd.add_argument("id", type=int, help="Artikel-ID (6-stellig)")
    update_cmd.set_defaults(func=update_command)

    remove_cmd = subparsers.add_parser("remove", help="Artikel löschen")
    remove_cmd.add_argument("id", type=int, help="Artikel-ID (6-stellig)")
    remove_cmd.set_defaults(func=remove_command)

    # Datenbank-Management
    export_cmd = subparsers.add_parser("export", help="Datenbank exportieren")
    export_cmd.add_argument("--file", default="inventory_backup.db", help="Zieldatei (.db)")
    export_cmd.set_defaults(func=export_command)

    import_cmd = subparsers.add_parser("import", help="Datenbank importieren")
    import_cmd.add_argument("--file", required=True, help="Quelldatei (.db)")
    import_cmd.set_defaults(func=import_command)

    # Suchen und Filtern
    search_cmd = subparsers.add_parser("search", help="Artikel suchen")
    search_cmd.add_argument("term", help="Suchbegriff")
    search_cmd.set_defaults(func=search_command)

    fts_cmd = subparsers.add_parser(
        "fts", 
        help="Erweiterte Volltextsuche",
        description="""Beispiele:
  python main.py fts "exakter begriff"
  python main.py fts 'ESP32 OR Arduino'
  python main.py fts 'mikro* AND sensor'
  python main.py fts 'NOT defekt'"""
    )
    fts_cmd.add_argument("query", nargs="?", help="Suchanfrage (mit Anführungszeichen für Phrasen)")
    fts_cmd.set_defaults(func=advanced_search_command)

    filter_cmd = subparsers.add_parser("filter", help="Artikel nach Kategorie/Status filtern")
    filter_cmd.add_argument("--category", help="Nach Kategorie filtern")
    filter_cmd.add_argument("--status", help="Nach Status filtern")
    filter_cmd.set_defaults(func=filter_command)

    # Kategorie-Management
    categories_cmd = subparsers.add_parser("categories", help="Kategorien verwalten")
    cat_sub = categories_cmd.add_subparsers(dest="cat_cmd")

    cat_list = cat_sub.add_parser("list", help="Kategorien auflisten")
    cat_list.set_defaults(func=categories_list_command)

    cat_add = cat_sub.add_parser("add", help="Kategorie hinzufügen")
    cat_add.add_argument("name", help="Kategoriename")
    cat_add.set_defaults(func=categories_add_command)

    # Bestandsverwaltung
    stock_cmd = subparsers.add_parser("stock", 
        help="Bestandsverwaltung",
        description="""Bestandsverwaltung für Artikel

Beispiele:
  Bestand hinzufügen:
    python main.py stock add 100000 eingang 5 --notes "Neue Lieferung" --reference-date 2024-01-15
  
  Artikel als verbaut markieren:
    python main.py stock add 100000 verbaut 2 --notes "Projekt XY"
  
  Bestellung aufgeben:
    python main.py stock add 100000 bestellung 10 --reference-date 2024-02-01
  
  Bestand anzeigen:
    python main.py stock show 100000
  
  Artikel mit niedrigem Bestand (unter 10):
    python main.py stock low --threshold 10""")
    stock_sub = stock_cmd.add_subparsers(dest="stock_cmd")

    stock_add = stock_sub.add_parser(
        "add", 
        help="Bestandsbewegung hinzufügen",
        description="Neue Bestandsbewegung für einen Artikel erfassen"
    )
    stock_add.add_argument("item_id", type=int, help="Artikel-ID (6-stellig)")
    stock_add.add_argument(
        "type", 
        choices=['eingang', 'ausgang', 'bestellung', 'storno', 'defekt', 'verbaut'],
        help="Art der Bewegung"
    )
    stock_add.add_argument("quantity", type=int, help="Menge (positiv)")
    stock_add.add_argument("--notes", help="Notizen zur Bewegung")
    stock_add.add_argument("--reference-date", help="Referenzdatum (YYYY-MM-DD)")
    stock_add.set_defaults(func=stock_add_command)

    stock_show = stock_sub.add_parser(
        "show", 
        help="Bestandsinformationen anzeigen",
        description="Zeigt aktuellen Bestand und Bewegungshistorie eines Artikels"
    )
    stock_show.add_argument("item_id", type=int, help="Artikel-ID (6-stellig)")
    stock_show.set_defaults(func=stock_show_command)

    stock_low = stock_sub.add_parser(
        "low", 
        help="Artikel mit niedrigem Bestand",
        description="Listet alle Artikel, deren Bestand unter dem Schwellenwert liegt"
    )
    stock_low.add_argument(
        "--threshold", 
        type=int, 
        default=5,
        help="Schwellenwert für niedrigen Bestand (Standard: 5)"
    )
    stock_low.set_defaults(func=stock_low_command)

    # TUI starten
    tui_cmd = subparsers.add_parser("tui", help="Textoberfläche starten")
    tui_cmd.set_defaults(command="tui", func=tui_command)

    args = parser.parse_args()
    if hasattr(args, "func"):
        if args.command != "tui":
            init_db()
            if args.command == "stock":
                stock.init_db()
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
