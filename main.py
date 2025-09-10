import argparse
import sys

from database.db import init_db, export_db, import_db
from modules import inventory

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


def tui_command(_):
    import importlib.util

    if importlib.util.find_spec("textual") is None:
        print(
            "Das Paket 'textual' ist nicht installiert. "
            "Installieren Sie es mit 'pip install textual'."
        )
        return

    try:
        import tui
    except ImportError as exc:
        print(f"TUI konnte nicht geladen werden: {exc}")
        return

    init_db()
    tui.main()


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


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI Warenwirtschaftssystem")
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("add", help="Neuen Artikel hinzufügen").set_defaults(func=add_command)
    subparsers.add_parser("show", help="Alle Artikel anzeigen").set_defaults(func=show_command)

    show_id_parser = subparsers.add_parser("show-id", help="Artikel per ID anzeigen")
    show_id_parser.add_argument("id", type=int, help="Artikel-ID")
    show_id_parser.set_defaults(func=show_id_command)

    update_parser = subparsers.add_parser("update", help="Artikel aktualisieren")
    update_parser.add_argument("id", type=int, help="Artikel-ID")
    update_parser.set_defaults(func=update_command)

    remove_parser = subparsers.add_parser("remove", help="Artikel löschen")
    remove_parser.add_argument("id", type=int, help="Artikel-ID")
    remove_parser.set_defaults(func=remove_command)

    export_parser = subparsers.add_parser("export", help="Datenbank exportieren")
    export_parser.add_argument("--file", default="inventory_backup.db", help="Zieldatei")
    export_parser.set_defaults(func=export_command)

    import_parser = subparsers.add_parser("import", help="Datenbank importieren")
    import_parser.add_argument("--file", required=True, help="Quelldatei")
    import_parser.set_defaults(func=import_command)

    tui_parser = subparsers.add_parser("tui", help="Textoberfläche starten")
    tui_parser.set_defaults(command="tui", func=tui_command)

    search_parser = subparsers.add_parser("search", help="Artikel suchen")
    search_parser.add_argument("term", help="Suchbegriff")
    search_parser.set_defaults(func=search_command)

    # Advanced FTS search
    fts_parser = subparsers.add_parser("fts", help="Advanced full-text search")
    fts_parser.add_argument("query", nargs="?", help="FTS query (use quotes for phrases)")
    fts_parser.set_defaults(func=advanced_search_command)

    filter_parser = subparsers.add_parser("filter", help="Artikel filtern")
    filter_parser.add_argument("--category", help="Nach Kategorie filtern")
    filter_parser.add_argument("--status", help="Nach Status filtern")
    filter_parser.set_defaults(func=filter_command)

    categories_parser = subparsers.add_parser("categories", help="Kategorien verwalten")
    cat_sub = categories_parser.add_subparsers(dest="cat_cmd")

    cat_list = cat_sub.add_parser("list", help="Kategorien auflisten")
    cat_list.set_defaults(func=categories_list_command)

    cat_add = cat_sub.add_parser("add", help="Kategorie hinzufügen")
    cat_add.add_argument("name", help="Kategoriename")
    cat_add.set_defaults(func=categories_add_command)

    args = parser.parse_args()
    if hasattr(args, "func"):
        if args.command != "tui":
            init_db()
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
