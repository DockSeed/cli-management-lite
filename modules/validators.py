class ItemValidator:
    VALID_STATUSES = ["bestellt", "eingetroffen", "verbaut", "defekt"]
    MAX_NAME_LENGTH = 100
    MAX_LOCATION_LENGTH = 50

    @staticmethod
    def validate_amount(value: str) -> int:
        """Validate ``value`` as integer amount and return it."""
        try:
            amount = int(value)
            if amount < 0:
                raise ValueError("Anzahl muss positiv sein")
            if amount > 99999:
                raise ValueError("Anzahl zu groß (max 99999)")
            return amount
        except ValueError as e:
            raise ValueError(f"Ungültige Anzahl: {e}")

    @staticmethod
    def validate_status(status: str) -> str:
        """Ensure ``status`` is one of the allowed values."""
        if status not in ItemValidator.VALID_STATUSES:
            raise ValueError(
                f"Status muss einer von {ItemValidator.VALID_STATUSES} sein"
            )
        return status

    @staticmethod
    def validate_name(name: str) -> str:
        """Validate item name."""
        if not name.strip():
            raise ValueError("Name darf nicht leer sein")
        if len(name) > ItemValidator.MAX_NAME_LENGTH:
            raise ValueError(
                f"Name zu lang (max {ItemValidator.MAX_NAME_LENGTH} Zeichen)"
            )
        return name.strip()

    @staticmethod
    def validate_date(date_str: str) -> str:
        """Validate date in YYYY-MM-DD or DD.MM.YYYY format."""
        if not date_str:
            return ""
        import re

        iso_pattern = r"^\d{4}-\d{2}-\d{2}$"
        german_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
        if re.match(iso_pattern, date_str) or re.match(german_pattern, date_str):
            return date_str
        raise ValueError("Datum muss Format YYYY-MM-DD oder DD.MM.YYYY haben")
