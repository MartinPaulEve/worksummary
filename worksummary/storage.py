import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from worksummary import ids
from worksummary.dates import format_iso, parse_iso_date


@dataclass(frozen=True)
class Item:
    id: str
    work_date: date
    created_at: str
    description: str


def init_db(conn: sqlite3.Connection) -> None:
    """Create the items table if it doesn't exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id          TEXT PRIMARY KEY,
            work_date   TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            description TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_items_work_date ON items(work_date)")
    conn.commit()


def connect(path: Path | str) -> sqlite3.Connection:
    """Open (and initialise) the SQLite database at `path`."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    init_db(conn)
    return conn


def _row_to_item(row: tuple) -> Item:
    return Item(
        id=row[0],
        work_date=parse_iso_date(row[1]),
        created_at=row[2],
        description=row[3],
    )


def add_item(conn: sqlite3.Connection, work_date: date, description: str) -> Item:
    """Insert a new item and return it."""
    # Microsecond precision so rapid successive inserts retain insertion order.
    created_at = datetime.now().isoformat()
    item_id = ids.generate_id(description, created_at)
    conn.execute(
        "INSERT INTO items (id, work_date, created_at, description) VALUES (?, ?, ?, ?)",
        (item_id, format_iso(work_date), created_at, description),
    )
    conn.commit()
    return Item(
        id=item_id,
        work_date=work_date,
        created_at=created_at,
        description=description,
    )


def add_item_before(conn: sqlite3.Connection, target_id: str, description: str) -> Item:
    """Insert a new item positioned just before `target_id` in its day's list.

    The new item takes the target's work_date and gets a created_at
    timestamp between the target and the item that currently precedes it
    (or one second earlier than the target if it is first of the day).
    Raises KeyError if target_id is not found.
    """
    target = get_item(conn, target_id)
    if target is None:
        raise KeyError(target_id)

    todays_items = list_items(conn, target.work_date)
    target_idx = next(i for i, it in enumerate(todays_items) if it.id == target_id)
    target_ts = datetime.fromisoformat(target.created_at)

    if target_idx == 0:
        new_ts = target_ts - timedelta(seconds=1)
    else:
        prev_ts = datetime.fromisoformat(todays_items[target_idx - 1].created_at)
        new_ts = prev_ts + (target_ts - prev_ts) / 2
        if new_ts == prev_ts:
            # Target and predecessor are 1μs apart — datetime arithmetic
            # truncated. Fall back to one microsecond before target.
            new_ts = target_ts - timedelta(microseconds=1)

    created_at = new_ts.isoformat()
    item_id = ids.generate_id(description, created_at)
    conn.execute(
        "INSERT INTO items (id, work_date, created_at, description) VALUES (?, ?, ?, ?)",
        (item_id, format_iso(target.work_date), created_at, description),
    )
    conn.commit()
    return Item(
        id=item_id,
        work_date=target.work_date,
        created_at=created_at,
        description=description,
    )


def list_items(conn: sqlite3.Connection, work_date: date) -> list[Item]:
    """Return all items for the given date, ordered by creation time."""
    cursor = conn.execute(
        "SELECT id, work_date, created_at, description FROM items "
        "WHERE work_date = ? ORDER BY created_at ASC, id ASC",
        (format_iso(work_date),),
    )
    return [_row_to_item(row) for row in cursor.fetchall()]


def get_item(conn: sqlite3.Connection, item_id: str) -> Item | None:
    """Return a single item by id, or None if not found."""
    cursor = conn.execute(
        "SELECT id, work_date, created_at, description FROM items WHERE id = ?",
        (item_id,),
    )
    row = cursor.fetchone()
    return _row_to_item(row) if row else None


def remove_item(conn: sqlite3.Connection, item_id: str) -> None:
    """Delete an item by id. Raises KeyError if it doesn't exist."""
    cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    if cursor.rowcount == 0:
        raise KeyError(item_id)
    conn.commit()


def all_ids(conn: sqlite3.Connection) -> list[str]:
    """Return all item ids in the database."""
    cursor = conn.execute("SELECT id FROM items")
    return [row[0] for row in cursor.fetchall()]
