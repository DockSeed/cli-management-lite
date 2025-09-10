import argparse
from database.db import init_db
from modules import inventory


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


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI Warenwirtschaftssystem")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("add", help="Neuen Artikel hinzufügen").set_defaults(func=add_command)
    subparsers.add_parser("show", help="Alle Artikel anzeigen").set_defaults(func=show_command)

    show_id_parser = subparsers.add_parser("show-id", help="Artikel per ID anzeigen")
    show_id_parser.add_argument("id", help="Artikel-ID")
    show_id_parser.set_defaults(func=show_id_command)

    update_parser = subparsers.add_parser("update", help="Artikel aktualisieren")
    update_parser.add_argument("id", help="Artikel-ID")
    update_parser.set_defaults(func=update_command)

    remove_parser = subparsers.add_parser("remove", help="Artikel löschen")
    remove_parser.add_argument("id", help="Artikel-ID")
    remove_parser.set_defaults(func=remove_command)

    args = parser.parse_args()
    if hasattr(args, "func"):
        init_db()
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
