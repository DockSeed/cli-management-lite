import argparse
import importlib
import subprocess
import sys


def ensure_dependencies() -> None:
    """Install benötigte Pakete automatisch, falls sie fehlen."""
    for package in ("textual", "tabulate"):
        try:
            importlib.import_module(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])


ensure_dependencies()

from database.db import init_db, export_db, import_db
from modules import inventory
import tui

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
    import_db(args.file)
    print(f"Datenbank aus {args.file} importiert")


def tui_command(_):
    init_db()
    tui.main()


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

    args = parser.parse_args()
    if hasattr(args, "func"):
        if args.command != "tui":
            init_db()
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
