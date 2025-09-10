from textual.app import App, ComposeResult
from textual.widgets import (
    ListView,
    ListItem,
    Label,
    Static,
    DataTable,
    Input,
    Button,
    Select,
    Horizontal,
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

        # Fix category dropdown with proper error handling
        categories = inventory.list_categories()
        if not categories:
            inventory.add_category("Standard")
            categories = inventory.list_categories()

        options = [(c["name"], str(c["id"])) for c in categories]
        current_cat_id = self.item.get("category_id")

        if current_cat_id:
            default_value = str(current_cat_id)
        else:
            default_value = options[0][1] if options else None

        yield Select(options=options, value=default_value, id="category_id", allow_blank=False)
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
            widgets = list(self.query(Input)) + list(self.query(Select))
            data = {w.id: w.value for w in widgets}
            if data.get("category_id"):
                data["category_id"] = int(data["category_id"])
            self.dismiss(data)
        else:
            self.dismiss(None)


class InventoryApp(App):
    """Professional TUI für das Inventar."""

    CSS = """
    Screen { 
        layout: grid; 
        grid-size: 2 4; 
        grid-rows: 1fr 3 8 1; 
        grid-columns: 1fr 2fr; 
    }
    #menu { }
    #detail { }
    #search { column-span: 2; }
    #table { column-span: 2; }
    #status { column-span: 2; background: $primary 10%; }
    
    DataTable {
        width: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("tab", "switch_focus", "Switch"),
        ("ctrl+f", "focus_search", "Search"),
        ("f5", "refresh", "Refresh"),
        ("delete", "delete_item", "Delete"),
        ("ctrl+n", "new_item", "New"),
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
        search = Input(
            placeholder="Search: 'phrase', wildcard*, ESP32 OR Arduino, NOT defekt",
            id="search",
        )
        table = DataTable(id="table")
        status = Static("", id="status")
        yield menu
        yield detail
        yield search
        yield table
        yield status

    def on_mount(self) -> None:
        self.sort_by = "id"
        self.descending = False
        table = self.query_one(DataTable)

        table.add_columns("ID", "Name", "Category", "Count", "Status")
        self.refresh_table()
        self.update_status_bar()
        self.set_focus(self.query_one(ListView))

    def refresh_table(self, search: str = "") -> None:
        table = self.query_one(DataTable)
        table.clear()

        rows = (
            inventory.search_items(search)
            if search
            else inventory.list_items(self.sort_by, self.descending)
        )

        for row in rows:
            name = row["name"]
            if len(name) > 20:
                name = name[:17] + "..."

            table.add_row(
                f"{row['id']:06d}",
                name,
                row.get("kategorie", ""),
                str(row["anzahl"]),
                row["status"],
                key=str(row["id"])
            )

        self.update_status_bar(len(rows), search)

    def update_status_bar(self, item_count: int = None, search: str = ""):
        """Update status bar with helpful information."""
        status = self.query_one("#status", Static)

        if item_count is None:
            all_items = inventory.list_items()
            item_count = len(all_items)

        try:
            conn = inventory.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT status, COUNT(*) FROM items GROUP BY status")
            status_counts = dict(cur.fetchall())
            conn.close()
        except Exception:
            status_counts = {}

        if search:
            status_text = f"Found: {item_count} items"
            if any(op in search for op in ['"', '*', 'OR', 'AND', 'NOT']):
                status_text += " (FTS)"
        else:
            status_text = f"Items: {item_count}"
            if status_counts:
                counts = [f"{k}: {v}" for k, v in status_counts.items()]
                status_text += f" | {' | '.join(counts)}"

        status_text += " | Ctrl+F: Search | F5: Refresh | Ctrl+N: New"
        status.update(status_text)

    def action_focus_search(self) -> None:
        self.set_focus(self.query_one("#search", Input))

    def action_refresh(self) -> None:
        """Refresh the table contents."""
        search_term = self.query_one("#search", Input).value
        self.refresh_table(search_term)

    def action_delete_item(self) -> None:
        """Delete the currently selected item."""
        table = self.query_one(DataTable)
        status = self.query_one("#status", Static)

        if table.cursor_row is None:
            status.update("Kein Artikel gewählt zum Löschen")
            return

        row_key = table.get_row_at(table.cursor_row)[0]
        item_id = int(row_key.replace(",", "").strip())

        inventory.remove_item_by_id(item_id)
        search_term = self.query_one("#search", Input).value
        self.refresh_table(search_term)

    async def action_new_item(self) -> None:
        """Open the form to add a new item."""
        data = await self.push_screen(ItemForm())
        if data:
            try:
                inventory.add_item(data)
                search_term = self.query_one("#search", Input).value
                self.refresh_table(search_term)
            except Exception as e:
                status = self.query_one("#status", Static)
                status.update(f"Fehler beim Hinzufügen: {str(e)}")

    def show_details(self, item_id: str) -> None:
        detail = self.query_one("#detail", Static)
        item = inventory.get_item(int(item_id))
        if item:
            lines = [
                f"ID: {item['id']:06d}",
                f"Name: {item['name']}",
                f"Kategorie: {item.get('kategorie', 'N/A')}",
                f"Anzahl: {item['anzahl']}",
                f"Status: {item['status']}",
            ]
            if item.get('ort'):
                lines.append(f"Ort: {item['ort']}")
            if item.get('notiz'):
                lines.append(f"Notiz: {item['notiz']}")
            if item.get('datum_bestellt'):
                lines.append(f"Bestellt: {item['datum_bestellt']}")
            if item.get('datum_eingetroffen'):
                lines.append(f"Eingetroffen: {item['datum_eingetroffen']}")

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
            search_term = event.value.strip()
            self.refresh_table(search_term)

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column sorting."""
        column_map = {
            "ID": "id",
            "Name": "name", 
            "Category": "kategorie",
            "Count": "anzahl",
            "Status": "status"
        }

        column = column_map.get(str(event.column_label))
        if column:
            if getattr(self, "sort_by", "id") == column:
                self.descending = not getattr(self, "descending", False)
            else:
                self.sort_by = column
                self.descending = False
            search = self.query_one("#search", Input).value
            self.refresh_table(search)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        choice = str(event.item.children[0].renderable)

        if choice == "Quit":
            self.exit()
        elif choice == "Add":
            await self.action_new_item()
        elif choice == "Update":
            table = self.query_one(DataTable)
            if table.cursor_row is None:
                self.update_status_bar()
                return
            row_key = table.get_row_at(table.cursor_row)[0]
            item_id = int(row_key.replace(",", "").strip())
            item = inventory.get_item(item_id)
            data = await self.push_screen(ItemForm(item))
            if data:
                inventory.update_item_fields(item_id, data)
                search_term = self.query_one("#search", Input).value
                self.refresh_table(search_term)
        elif choice == "Remove":
            self.action_delete_item()
        elif choice == "Show":
            table = self.query_one(DataTable)
            if table.cursor_row is None:
                return
            row_key = table.get_row_at(table.cursor_row)[0]
            item_id = row_key.replace(",", "").strip()
            self.show_details(item_id)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Show details when row is selected."""
        self.show_details(str(event.row_key))


def main() -> None:
    app = InventoryApp()
    app.run()


if __name__ == "__main__":
    main()
