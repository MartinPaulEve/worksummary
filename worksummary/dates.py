from datetime import date, datetime, timedelta


def parse_iso_date(text: str) -> date:
    """Parse a date in strict YYYY-MM-DD format."""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise ValueError(f"date must be in YYYY-MM-DD format (got {text!r})") from exc


def today() -> date:
    """Return today's local date."""
    return date.today()


def past_week(end: date) -> list[date]:
    """Return the 7 dates ending at `end` (inclusive), in chronological order.

    i.e. `end - 6` … `end`.
    """
    return [end - timedelta(days=offset) for offset in range(6, -1, -1)]


def format_iso(d: date) -> str:
    """Format a date as ISO YYYY-MM-DD."""
    return d.isoformat()
