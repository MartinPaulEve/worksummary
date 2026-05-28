from datetime import date, datetime


def parse_iso_date(text: str) -> date:
    """Parse a date in strict YYYY-MM-DD format."""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise ValueError(f"date must be in YYYY-MM-DD format (got {text!r})") from exc


def today() -> date:
    """Return today's local date."""
    return date.today()


def format_iso(d: date) -> str:
    """Format a date as ISO YYYY-MM-DD."""
    return d.isoformat()
