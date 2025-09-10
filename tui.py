from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label, Static, DataTable, Input, Button
from textual.screen import ModalScreen
from modules import inventory


class ItemForm(ModalScreen):
    """Eingabedialog für Artikel."""

    def __init__(self, item: dict | None = None):
        super().__init__()
        self.item = item or {}

    def compose(self) -> ComposeResult:
        yield Static("Artikel", classes="title")
        yield Input(value=self.item.get("id", inventory.propose_id()), placeholder="ID", id="id")
        yield Input(value=self.item.get("name", ""), placeholder="Name", id="name")
        yield Input(value=self.item.get("kategorie", ""), placeholder="Kategorie", id="kategorie")
        yield Input(value=str(self.item.get("anzahl", "")), placeholder="Anzahl", id="anzahl")
        yield Input(value=self.item.get("status", ""), placeholder="Status", id="status")
        yield Input(value=self.item.get("eingesetzt", "") or "", placeholder="Eingesetzt", id="eingesetzt")
        yield Input(value=self.item.get("notiz", "") or "", placeholder="Notiz", id="notiz")
        yield Button("Speichern", id="save")
        yield Button("Abbrechen", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            data = {widget.id: widget.value for widget in self.query(Input)}
            data["anzahl"] = int(data.get("anzahl") or 0)
            self.dismiss(data)
        else:
            self.dismiss(None)


class InventoryApp(App):
    """Einfache TUI für das Inventar."""

    CSS = """
    Screen { layout: grid; grid-size: 2 2; grid-rows: 1fr 6; grid-columns: 25 1fr; }
    #menu { grid-row: 1; grid-column: 1; }
    #detail { grid-row: 1; grid-column: 2; }
    #table { grid-row: 2; grid-column: 1 / span 2; height: 8; }
    #status { dock: bottom; height: 1; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("tab", "switch_focus", "Switch"),
    ]

    def compose(self) -> ComposeResult:
        menu = ListView(
            ListItem(Label("Add")),
            ListItem(Label("Update")),
            ListItem(Label("Remove")),
            ListItem(Label("Show")),
            ListItem(Label("Quit")),
            id="menu",
        )
        detail = Static("", id="detail")
        table = DataTable(id="table")
        status = Static("", id="status")
        yield menu
        yield detail
        yield table
        yield status

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Name", "Status")
        self.refresh_table()
        self.set_focus(self.query_one(ListView))

    def refresh_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear(True)
        for row in inventory.list_items():
            table.add_row(row["id"], row["name"], row["status"], key=row["id"])

    def show_details(self, item_id: str) -> None:
        detail = self.query_one("#detail", Static)
        item = inventory.get_item(item_id)
        if item:
            lines = [f"{k}: {v}" for k, v in item.items()]
            detail.update("\n".join(lines))
        else:
            detail.update("Artikel nicht gefunden")

    def action_switch_focus(self) -> None:
        menu = self.query_one(ListView)
        table = self.query_one(DataTable)
        if self.focused is menu:
            self.set_focus(table)
        else:
            self.set_focus(menu)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        choice = event.item.query_one(Label).renderable
        status = self.query_one("#status", Static)
        if choice == "Quit":
            self.exit()
        elif choice == "Add":
            data = await self.push_screen(ItemForm())
            if data:
                inventory.add_item(data)
                self.refresh_table()
                status.update("Artikel hinzugefügt")
        elif choice == "Update":
            table = self.query_one(DataTable)
            if table.cursor_row is None:
                status.update("Kein Artikel gewählt")
                return
            item_id = table.row_keys[table.cursor_row]
            item = inventory.get_item(item_id)
            data = await self.push_screen(ItemForm(item))
            if data:
                item_id = data.pop("id")
                inventory.update_item_fields(item_id, data)
                self.refresh_table()
                status.update("Artikel aktualisiert")
        elif choice == "Remove":
            table = self.query_one(DataTable)
            if table.cursor_row is None:
                status.update("Kein Artikel gewählt")
                return
            item_id = table.row_keys[table.cursor_row]
            inventory.remove_item_by_id(item_id)
            self.refresh_table()
            status.update("Artikel gelöscht")
        elif choice == "Show":
            table = self.query_one(DataTable)
            if table.cursor_row is None:
                status.update("Kein Artikel gewählt")
                return
            item_id = table.row_keys[table.cursor_row]
            self.show_details(item_id)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.show_details(event.row_key)


def main() -> None:
    app = InventoryApp()
    app.run()


if __name__ == "__main__":
    main()
