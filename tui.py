from textual.app import App, ComposeResult
from textual.widgets import (
    ListView,
    ListItem,
    Label,
    Static,
    DataTable,
    Input,
    Button,
)
from textual.screen import ModalScreen
from modules import inventory


class ItemForm(ModalScreen):
    """Eingabedialog für Artikel."""

    def __init__(self, item: dict | None = None):
        super().__init__()
        self.item = item or {}

    def compose(self) -> ComposeResult:
        yield Static("Artikel", classes="title")
        if self.item:
            yield Static(f"ID: {self.item['id']}", id="id_label")
        yield Input(value=self.item.get("name", ""), placeholder="Name", id="name")
        yield Input(value=self.item.get("kategorie", ""), placeholder="Kategorie", id="kategorie")
        yield Input(value=str(self.item.get("anzahl", "")), placeholder="Anzahl", id="anzahl")
        yield Input(value=self.item.get("status", ""), placeholder="Status", id="status")
        yield Input(value=self.item.get("ort", "") or "", placeholder="Ort", id="ort")
        yield Input(value=self.item.get("notiz", "") or "", placeholder="Notiz", id="notiz")
        yield Input(
            value=self.item.get("datum_bestellt", "") or "",
            placeholder="Datum bestellt",
            id="datum_bestellt",
        )
        yield Input(
            value=self.item.get("datum_eingetroffen", "") or "",
            placeholder="Datum eingetroffen",
            id="datum_eingetroffen",
        )
        yield Button("Speichern", id="save")
        yield Button("Abbrechen", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            data = {widget.id: widget.value for widget in self.query(Input)}
            self.dismiss(data)
        else:
            self.dismiss(None)


class InventoryApp(App):
    """Einfache TUI für das Inventar."""

    CSS = """
    Screen { layout: grid; grid-size: 2 3; grid-rows: 1fr 3 6; grid-columns: 25 1fr; }
    #menu { grid-row: 1; grid-column: 1; }
    #detail { grid-row: 1; grid-column: 2; }
    #search { grid-row: 2; grid-column: 1 / span 2; }
    #table { grid-row: 3; grid-column: 1 / span 2; height: 8; }
    #status { dock: bottom; height: 1; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("tab", "switch_focus", "Switch"),
        ("ctrl+f", "focus_search", "Search"),
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
        search = Input(placeholder="Suche", id="search")
        table = DataTable(id="table")
        status = Static("", id="status")
        yield menu
        yield detail
        yield search
        yield table
        yield status

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Name", "Status")
        self.refresh_table()
        self.set_focus(self.query_one(ListView))

    def refresh_table(self, search: str = "") -> None:
        table = self.query_one(DataTable)
        table.clear(True)
        rows = (
            inventory.search_items(search) if search else inventory.list_items()
        )
        for row in rows:
            table.add_row(row["id"], row["name"], row["status"], key=row["id"])

    def action_focus_search(self) -> None:
        self.set_focus(self.query_one("#search", Input))

    def show_details(self, item_id: str) -> None:
        detail = self.query_one("#detail", Static)
        item = inventory.get_item(int(item_id))
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

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            self.refresh_table(event.value)

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
            item_id = int(table.row_keys[table.cursor_row])
            item = inventory.get_item(item_id)
            data = await self.push_screen(ItemForm(item))
            if data:
                inventory.update_item_fields(item_id, data)
                self.refresh_table()
                status.update("Artikel aktualisiert")
        elif choice == "Remove":
            table = self.query_one(DataTable)
            if table.cursor_row is None:
                status.update("Kein Artikel gewählt")
                return
            item_id = int(table.row_keys[table.cursor_row])
            inventory.remove_item_by_id(item_id)
            self.refresh_table()
            status.update("Artikel gelöscht")
        elif choice == "Show":
            table = self.query_one(DataTable)
            if table.cursor_row is None:
                status.update("Kein Artikel gewählt")
                return
            item_id = int(table.row_keys[table.cursor_row])
            self.show_details(item_id)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.show_details(int(event.row_key))


def main() -> None:
    app = InventoryApp()
    app.run()


if __name__ == "__main__":
    main()
