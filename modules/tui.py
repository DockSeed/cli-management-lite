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
from .db import get_connection

class StockOverview(Static):
    """Bestandsübersicht für ausgewählten Artikel."""
    
    def compose(self) -> ComposeResult:
        """Display stock information."""
        with Vertical():
            yield Label("Keine Auswahl", id="no_selection")
            with Vertical(id="stock_info", classes="hidden"):
                yield Label("Artikelinfo", classes="heading")
                yield Label("", id="item_name")
                yield Label("", id="item_category")
                yield Label("", id="item_status")
                yield Label("", id="item_shop")
                yield Label("", id="current_stock")
                yield Label("", id="ordered")
                yield Label("", id="used")
                yield Label("", id="defect")
                yield Label("Letzte Bewegungen:")
                yield Static("", id="movements")

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
        
        self.query_one("#item_name").update(f"Name: {item['name']}")
        self.query_one("#item_category").update(f"Kategorie: {item.get('kategorie','-')}")
        self.query_one("#item_status").update(f"Status: {item.get('status','-')}")
        self.query_one("#item_shop").update(f"Shop: {item.get('shop','-') or '-'}")
        self.query_one("#current_stock").update(f"Aktuell: {info['current_stock']}")
        self.query_one("#ordered").update(f"Bestellt: {info['ordered_quantity']}")
        self.query_one("#used").update(f"Verbaut: {info['used_quantity']}")
        self.query_one("#defect").update(f"Defekt: {info['defect_quantity']}")
        # Bewegungen komprimiert darstellen (max 5)
        lines = []
        for m in info.get('movements', [])[:5]:
            mt = m.get('movement_type','')
            qty = m.get('quantity','')
            date = (m.get('reference_date') or m.get('movement_date') or '')
            note = m.get('notes') or ''
            if len(note) > 30:
                note = note[:27] + '...'
            lines.append(f"- {date} | {mt} {qty} {note}")
        self.query_one("#movements", Static).update("\n".join(lines) if lines else "-")


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
            yield Button("Kategorien verwalten", id="manage_categories")


class ItemDialog(ModalScreen):
    """Dialog für Artikel erstellen/bearbeiten."""
    
    def __init__(self, item: dict | None = None) -> None:
        super().__init__()
        self.item = item or {}
    
    BINDINGS = [
        Binding("escape", "close_dialog", "Schließen")
    ]
    
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
            # Optional: neue Kategorie direkt anlegen
            yield Input(
                value="",
                placeholder="Neue Kategorie (optional)",
                id="new_category"
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
                yield Button("Schließen", id="close")

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
        elif event.button.id in {"close"}:
            self.dismiss(None)
        else:
            pass

    def action_close_dialog(self) -> None:
        self.dismiss(None)


class StockDialog(ModalScreen):
    """Dialog für Bestandsbewegungen."""
    
    def __init__(self, item_id: int) -> None:
        super().__init__()
        self.item_id = item_id
        self.item = inventory.get_item(item_id)
    
    BINDINGS = [
        Binding("escape", "close_dialog", "Schließen")
    ]
    
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
                yield Button("Schließen", id="close")
    
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
        elif event.button.id in {"close"}:
            self.dismiss(None)
        else:
            pass

    def action_close_dialog(self) -> None:
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
    
    #dialog Button {
        width: auto;
        min-width: 12;
        margin-bottom: 0;
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

    _help_open = False

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()
        yield QuickActions()
        
        table = DataTable(id="items")
        table.add_columns(
            "ID", "Name", "Kategorie", "Bestand", "Bestellt", "Status", "Shop"
        )
        yield table
        
        yield StockOverview()
        yield Footer()

    def on_mount(self) -> None:
        """Initialisierung nach dem Start."""
        self.refresh_table()
        self.refresh_categories()

    def action_toggle_help(self) -> None:
        """Zeige/Verberge eine einfache Hilfe-Ansicht."""
        if self._help_open:
            try:
                self.pop_screen()
            finally:
                self._help_open = False
            return

        class HelpScreen(ModalScreen):
            def compose(self) -> ComposeResult:
                with Vertical(id="dialog"):
                    yield Label("Hilfe / Tasten", classes="heading")
                    yield Label("F1: Hilfe ein/aus")
                    yield Label("N: Neu, E: Bearbeiten, D: Löschen, B: Bestand")
                    yield Label("Q: Beenden")
                    with Horizontal(classes="buttons"):
                        yield Button("Schließen", id="close", variant="primary")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "close":
                    self.dismiss(None)

        def _closed(_):
            self._help_open = False

        self._help_open = True
        self.push_screen(HelpScreen(), callback=_closed)

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
                str(stock_info['ordered_quantity']),
                item['status'],
                item.get('shop', '-') or '-',
            )
        # Select first row by default to make buttons work without manual selection
        try:
            table.cursor_type = "row"
            if table.row_count:
                table.move_cursor(row=0, column=0)
        except Exception:
            pass

    def refresh_categories(self) -> None:
        """Aktualisiere Kategorie-Filter."""
        categories = inventory.list_categories()
        cat_select = self.query_one("#category_filter")
        options = [("Alle", "")] + [(c["name"], str(c["id"])) for c in categories]
        try:
            # Select in Textual 6.x nutzt set_options anstelle eines options-Attributes
            cat_select.set_options(options)
        except Exception:
            pass

    def on_data_table_row_selected(self, event) -> None:
        """Reagiere auf Tabellenauswahl."""
        table = event.control
        if table.row_count and table.cursor_row is not None:
            item_id = int(table.get_row_at(table.cursor_row)[0])
            self.query_one(StockOverview).update_info(item_id)

    async def action_manage_categories(self) -> None:
        """Kategorieverwaltung anzeigen."""
        class CategoryDialog(ModalScreen[str | None]):
            def compose(self) -> ComposeResult:
                with Vertical(id="dialog"):
                    yield Label("Kategorien verwalten", classes="heading")
                    cats = inventory.list_categories()
                    options = [(c["name"], str(c["id"])) for c in cats]
                    yield Select(options=options, id="cat_select", prompt="Kategorie auswählen")
                    yield Label("Verknüpfte Artikel:")
                    yield Static("", id="cat_items")
                    with Horizontal(classes="buttons"):
                        yield Button("Kategorie löschen", id="delete_category", variant="error")
                        yield Button("Schließen", id="close")

            def on_mount(self) -> None:
                sel = self.query_one("#cat_select", Select)
                # Wenn noch keine Auswahl getroffen wurde, nimm die erste vorhandene Kategorie
                if sel.value == Select.BLANK:
                    cats = inventory.list_categories()
                    if cats:
                        sel.value = str(cats[0]["id"]) if isinstance(cats[0], dict) else str(cats[0][0])
                self.refresh_usage()

            def on_select_changed(self, event: Select.Changed) -> None:
                if event.select.id == "cat_select":
                    self.refresh_usage()

            def refresh_usage(self) -> None:
                sel = self.query_one("#cat_select", Select)
                value = sel.value
                # Keine Auswahl: Anzeige leeren und Löschen deaktivieren
                if (value is None) or (value == "") or (value == Select.BLANK):
                    self.query_one("#cat_items", Static).update("-")
                    del_btn = self.query_one("#delete_category", Button)
                    del_btn.disabled = True
                    return
                items = inventory.get_category_items(int(value))
                lines = [f"- {it['id']:06d} {it['name']}" for it in items[:10]]
                more = "" if len(items) <= 10 else f"\n(+{len(items)-10} weitere)"
                self.query_one("#cat_items", Static).update("\n".join(lines) + more if lines else "-")
                del_btn = self.query_one("#delete_category", Button)
                del_btn.disabled = len(items) > 0

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "close":
                    self.dismiss(None)
                elif event.button.id == "delete_category":
                    sel = self.query_one("#cat_select", Select)
                    if (sel.value is None) or (sel.value == "") or (sel.value == Select.BLANK):
                        self.dismiss(None)
                        return
                    try:
                        inventory.delete_category(int(sel.value))
                        self.dismiss("deleted")
                    except Exception as e:
                        self.app.notify(f"{e}", severity="error")
                        self.refresh_usage()

        def _after(result: str | None):
            if result == "deleted":
                self.notify("Kategorie gelöscht")
                self.refresh_categories()

        self.push_screen(CategoryDialog(), callback=_after)

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
        elif button_id == "manage_categories":
            await self.action_manage_categories()

    async def action_new_item(self) -> None:
        """Neuen Artikel anlegen."""
        dialog = ItemDialog()
        def _on_dismiss(result):
            if result:
                try:
                    # Neue Kategorie anlegen, falls angegeben
                    new_cat = (result.get("new_category") or "").strip()
                    if new_cat:
                        cat_id = inventory.add_category(new_cat)
                        result["category_id"] = str(cat_id)
                    result.pop("new_category", None)
                    item_id = inventory.add_item(result)
                    self.notify(f"Artikel {item_id} angelegt")
                    self.refresh_table()
                except Exception as e:
                    self.notify(f"Fehler: {str(e)}", severity="error")
        self.push_screen(dialog, callback=_on_dismiss)

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
        def _on_dismiss_edit(result, item_id=item_id):
            if result:
                try:
                    # Neue Kategorie anlegen, falls angegeben
                    new_cat = (result.get("new_category") or "").strip()
                    if new_cat:
                        cat_id = inventory.add_category(new_cat)
                        result["category_id"] = str(cat_id)
                    result.pop("new_category", None)
                    inventory.update_item_fields(item_id, result)
                    self.notify(f"Artikel {item_id} aktualisiert")
                    self.refresh_table()
                except Exception as e:
                    self.notify(f"Fehler: {str(e)}", severity="error")
        self.push_screen(dialog, callback=_on_dismiss_edit)

    async def action_delete_item(self) -> None:
        """Artikel löschen."""
        table = self.query_one(DataTable)
        if not table.row_count or table.cursor_row is None:
            self.notify("Kein Artikel ausgewählt", severity="warning")
            return
            
        item_id = int(table.get_row_at(table.cursor_row)[0])
        # Bestätigungsdialog anzeigen
        class ConfirmDialog(ModalScreen[bool]):
            def __init__(self, message: str):
                super().__init__()
                self.message = message
            def compose(self) -> ComposeResult:
                with Vertical(id="dialog"):
                    yield Label("Löschen bestätigen", classes="heading")
                    yield Label(self.message)
                    with Horizontal(classes="buttons"):
                        yield Button("Löschen", id="confirm", variant="error")
                        yield Button("Abbrechen", id="close")
            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "confirm":
                    self.dismiss(True)
                elif event.button.id == "close":
                    self.dismiss(False)

        def _on_confirm(result: bool | None):
            if not result:
                return
            try:
                inventory.remove_item_by_id(item_id)
                # Nach dem Löschen Sequenz so anpassen, dass gelöschte höchste ID wiederverwendet wird
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT MAX(id) FROM items")
                    max_id = cur.fetchone()[0]
                    if max_id is None:
                        cur.execute("DELETE FROM sqlite_sequence WHERE name='items'")
                    else:
                        cur.execute("UPDATE sqlite_sequence SET seq=? WHERE name='items'", (max_id,))
                    conn.commit()
                except Exception:
                    pass
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
                self.notify(f"Artikel {item_id} gelöscht")
                self.refresh_table()
            except Exception as e:
                self.notify(f"Fehler: {str(e)}", severity="error")

        self.push_screen(ConfirmDialog(f"Artikel {item_id:06d} wirklich löschen?"), callback=_on_confirm)

    async def action_stock_movement(self) -> None:
        """Bestandsbewegung hinzufügen."""
        table = self.query_one(DataTable)
        if not table.row_count or table.cursor_row is None:
            self.notify("Kein Artikel ausgewählt", severity="warning")
            return
            
        item_id = int(table.get_row_at(table.cursor_row)[0])
        dialog = StockDialog(item_id)
        def _on_dismiss_stock(result, item_id=item_id):
            if result:
                try:
                    stock.add_movement(**result)
                    self.notify("Bestandsbewegung hinzugefügt")
                    self.refresh_table()
                    self.query_one(StockOverview).update_info(item_id)
                except Exception as e:
                    self.notify(f"Fehler: {str(e)}", severity="error")
        self.push_screen(dialog, callback=_on_dismiss_stock)

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


