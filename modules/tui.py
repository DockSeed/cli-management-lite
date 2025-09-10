"""Textbasierte Benutzeroberfläche (TUI) für das Warenwirtschaftssystem."""
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    Static,
    Button,
    Input,
    Select,
    Label
)
from textual.screen import ModalScreen
from . import inventory, stock

class StockOverview(Static):
    """Bestandsübersicht für ausgewählten Artikel."""
    
    def compose(self) -> ComposeResult:
        """Display stock information."""
        with Vertical():
            yield Label("Keine Auswahl", id="no_selection")
            with Vertical(id="stock_info", classes="hidden"):
                yield Label("Bestandsinformationen", classes="heading")
                yield Label("", id="current_stock")
                yield Label("", id="ordered")
                yield Label("", id="used")
                yield Label("", id="defect")

    def update_info(self, item_id: int | None) -> None:
        """Aktualisiere Bestandsinformationen."""
        no_selection = self.query_one("#no_selection")
        stock_info = self.query_one("#stock_info")
        
        if item_id is None:
            no_selection.remove_class("hidden")
            stock_info.add_class("hidden")
            return
            
        info = stock.get_item_stock(item_id)
        item = inventory.get_item(item_id)
        
        if not item:
            return
            
        no_selection.add_class("hidden")
        stock_info.remove_class("hidden")
        
        self.query_one("#current_stock").update(f"Aktuell: {info['current_stock']}")
        self.query_one("#ordered").update(f"Bestellt: {info['ordered_quantity']}")
        self.query_one("#used").update(f"Verbaut: {info['used_quantity']}")
        self.query_one("#defect").update(f"Defekt: {info['defect_quantity']}")


class QuickActions(Static):
    """Schnellzugriff auf wichtige Funktionen."""
    
    def compose(self) -> ComposeResult:
        """Compose the quick actions panel."""
        with Vertical():
            yield Label("Aktionen", classes="heading")
            yield Button("Neu [N]", id="new", variant="primary")
            yield Button("Bearbeiten [E]", id="edit")
            yield Button("Löschen [D]", id="delete", variant="error")
            yield Button("Bestand [B]", id="stock")
            yield Label("Filter", classes="heading")
            yield Input(placeholder="Suche...", id="search")
            yield Select(
                options=[("Alle", "")],
                value="",
                id="category_filter",
                prompt="Kategorie..."
            )
            yield Select(
                options=[
                    ("Alle", ""),
                    ("Bestellt", "bestellt"),
                    ("Eingetroffen", "eingetroffen"),
                    ("Verbaut", "verbaut"),
                    ("Defekt", "defekt"),
                    ("Nachbestellen", "nachbestellen")
                ],
                value="",
                id="status_filter",
                prompt="Status..."
            )


class ItemDialog(ModalScreen):
    """Dialog für Artikel erstellen/bearbeiten."""
    
    def __init__(self, item: dict | None = None) -> None:
        super().__init__()
        self.item = item or {}
    
    def compose(self) -> ComposeResult:
        """Compose the dialog form."""
        with Vertical(id="dialog"):
            yield Label(
                "Artikel bearbeiten" if self.item else "Neuer Artikel",
                classes="heading"
            )
            yield Input(
                value=self.item.get("name", ""),
                placeholder="Name*",
                id="name"
            )
            
            categories = inventory.list_categories()
            if not categories:
                inventory.add_category("Standard")
                categories = inventory.list_categories()
            
            cat_options = [(c["name"], str(c["id"])) for c in categories]
            current_cat = str(self.item.get("category_id", "")) if self.item else str(categories[0]["id"])
            yield Select(
                options=cat_options,
                value=current_cat,
                id="category_id",
                prompt="Kategorie auswählen"
            )
            
            status_options = [(s.capitalize(), s) for s in inventory.VALID_STATUS]
            yield Select(
                options=status_options,
                value=self.item.get("status", "bestellt"),
                id="status",
                prompt="Status auswählen"
            )
            
            yield Input(
                value=self.item.get("shop", ""),
                placeholder="Shop (optional)",
                id="shop"
            )
            
            yield Input(
                value=self.item.get("notiz", ""),
                placeholder="Notiz (optional)",
                id="notiz"
            )
            
            with Horizontal(classes="buttons"):
                yield Button("Speichern", variant="primary", id="save")
                yield Button("Abbrechen", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save":
            values = {}
            for widget in self.query(Input):
                values[widget.id] = widget.value.strip()
            for widget in self.query(Select):
                values[widget.id] = widget.value
            
            if not values.get("name"):
                self.notify("Name ist erforderlich", severity="error")
                return
                
            self.dismiss(values)
        else:
            self.dismiss(None)


class StockDialog(ModalScreen):
    """Dialog für Bestandsbewegungen."""
    
    def __init__(self, item_id: int) -> None:
        super().__init__()
        self.item_id = item_id
        self.item = inventory.get_item(item_id)
    
    def compose(self) -> ComposeResult:
        """Compose the stock movement form."""
        with Vertical(id="dialog"):
            yield Label(f"Bestandsbewegung für {self.item['name']}", classes="heading")
            
            yield Select(
                options=[
                    ("Eingang", "eingang"),
                    ("Ausgang", "ausgang"),
                    ("Bestellung", "bestellung"),
                    ("Storno", "storno"),
                    ("Defekt", "defekt"),
                    ("Verbaut", "verbaut")
                ],
                id="movement_type",
                prompt="Art der Bewegung"
            )
            
            yield Input(
                placeholder="Menge*",
                id="quantity"
            )
            
            yield Input(
                placeholder="Notiz",
                id="notes"
            )
            
            yield Input(
                placeholder="Referenzdatum (YYYY-MM-DD)",
                id="reference_date"
            )
            
            with Horizontal(classes="buttons"):
                yield Button("Speichern", variant="primary", id="save")
                yield Button("Abbrechen", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save":
            values = {
                "item_id": self.item_id
            }
            for widget in self.query(Input):
                values[widget.id] = widget.value.strip()
            for widget in self.query(Select):
                values[widget.id] = widget.value
            
            try:
                values["quantity"] = int(values.get("quantity", "0"))
                if values["quantity"] <= 0:
                    raise ValueError()
            except ValueError:
                self.notify("Ungültige Menge", severity="error")
                return
                
            if not values.get("movement_type"):
                self.notify("Bewegungsart ist erforderlich", severity="error")
                return
                
            self.dismiss(values)
        else:
            self.dismiss(None)


class InventoryApp(App):
    """Hauptanwendung."""
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 3;
        grid-columns: 1fr 4fr 1fr;
        padding: 1;
    }
    
    QuickActions {
        border: solid $primary;
        height: 100%;
        padding: 1;
    }
    
    #items {
        height: 100%;
        border: solid $primary;
        padding: 1;
    }
    
    StockOverview {
        border: solid $primary;
        height: 100%;
        padding: 1;
    }
    
    .heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    .hidden {
        display: none;
    }
    
    Button {
        width: 100%;
        margin-bottom: 1;
    }
    
    Input, Select {
        margin-bottom: 1;
    }
    
    #dialog {
        grid-size: 1;
        padding: 1;
        width: 60;
        height: auto;
        border: solid $primary;
        background: $surface;
    }

    .buttons {
        width: 100%;
        height: 3;
        align: center middle;
        margin-top: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Beenden"),
        Binding("n", "new_item", "Neu"),
        Binding("e", "edit_item", "Bearbeiten"),
        Binding("d", "delete_item", "Löschen"),
        Binding("b", "stock_movement", "Bestand"),
        Binding("f1", "toggle_help", "Hilfe"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()
        yield QuickActions()
        
        table = DataTable(id="items")
        table.add_columns(
            "ID", "Name", "Kategorie", "Bestand", "Status", "Shop"
        )
        yield table
        
        yield StockOverview()
        yield Footer()

    def on_mount(self) -> None:
        """Initialisierung nach dem Start."""
        self.refresh_table()
        self.refresh_categories()

    def refresh_table(self) -> None:
        """Aktualisiere die Artikeltabelle."""
        table = self.query_one(DataTable)
        table.clear()
        
        items = inventory.list_items()
        for row in items:
            # Convert Row to dict
            item = dict(zip(row.keys(), row))
            stock_info = stock.get_item_stock(item["id"])
            table.add_row(
                f"{item['id']:06d}",
                item['name'],
                item.get('kategorie', 'N/A'),
                str(stock_info['current_stock']),
                item['status'],
                item.get('shop', '-') or '-',
            )

    def refresh_categories(self) -> None:
        """Aktualisiere Kategorie-Filter."""
        categories = inventory.list_categories()
        cat_select = self.query_one("#category_filter")
        options = [("Alle", "")] + [(c["name"], str(c["id"])) for c in categories]
        cat_select.options = options

    def on_data_table_row_selected(self, event) -> None:
        """Reagiere auf Tabellenauswahl."""
        table = event.control
        if table.row_count and table.cursor_row is not None:
            item_id = int(table.get_row_at(table.cursor_row)[0])
            self.query_one(StockOverview).update_info(item_id)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Reagiere auf Buttonklicks."""
        button_id = event.button.id
        if button_id == "new":
            await self.action_new_item()
        elif button_id == "edit":
            await self.action_edit_item()
        elif button_id == "delete":
            await self.action_delete_item()
        elif button_id == "stock":
            await self.action_stock_movement()

    async def action_new_item(self) -> None:
        """Neuen Artikel anlegen."""
        dialog = ItemDialog()
        result = await self.push_screen(dialog)
        if result:
            try:
                item_id = inventory.add_item(result)
                self.notify(f"Artikel {item_id} angelegt")
                self.refresh_table()
            except Exception as e:
                self.notify(f"Fehler: {str(e)}", severity="error")

    async def action_edit_item(self) -> None:
        """Artikel bearbeiten."""
        table = self.query_one(DataTable)
        if not table.row_count or table.cursor_row is None:
            self.notify("Kein Artikel ausgewählt", severity="warning")
            return
            
        item_id = int(table.get_row_at(table.cursor_row)[0])
        item = inventory.get_item(item_id)
        if not item:
            self.notify("Artikel nicht gefunden", severity="error")
            return
            
        dialog = ItemDialog(item)
        result = await self.push_screen(dialog)
        if result:
            try:
                inventory.update_item_fields(item_id, result)
                self.notify(f"Artikel {item_id} aktualisiert")
                self.refresh_table()
            except Exception as e:
                self.notify(f"Fehler: {str(e)}", severity="error")

    async def action_delete_item(self) -> None:
        """Artikel löschen."""
        table = self.query_one(DataTable)
        if not table.row_count or table.cursor_row is None:
            self.notify("Kein Artikel ausgewählt", severity="warning")
            return
            
        item_id = int(table.get_row_at(table.cursor_row)[0])
        try:
            inventory.remove_item_by_id(item_id)
            self.notify(f"Artikel {item_id} gelöscht")
            self.refresh_table()
        except Exception as e:
            self.notify(f"Fehler: {str(e)}", severity="error")

    async def action_stock_movement(self) -> None:
        """Bestandsbewegung hinzufügen."""
        table = self.query_one(DataTable)
        if not table.row_count or table.cursor_row is None:
            self.notify("Kein Artikel ausgewählt", severity="warning")
            return
            
        item_id = int(table.get_row_at(table.cursor_row)[0])
        dialog = StockDialog(item_id)
        result = await self.push_screen(dialog)
        if result:
            try:
                stock.add_movement(**result)
                self.notify("Bestandsbewegung hinzugefügt")
                self.refresh_table()
                self.query_one(StockOverview).update_info(item_id)
            except Exception as e:
                self.notify(f"Fehler: {str(e)}", severity="error")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle Sucheingabe."""
        if event.input.id == "search":
            self.refresh_table()  # TODO: Implement search filter

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle Filter-Änderungen."""
        if event.select.id in ["category_filter", "status_filter"]:
            self.refresh_table()  # TODO: Implement filters


def main() -> None:
    """Start the TUI application."""
    app = InventoryApp()
    app.run()