import sqlite3
from datetime import date, datetime

import pytest

from worksummary import storage


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    storage.init_db(c)
    yield c
    c.close()


def test_init_db_creates_items_table(conn):
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
    assert cursor.fetchone() is not None


def test_init_db_is_idempotent(conn):
    storage.init_db(conn)


def test_add_item_returns_item_with_id(conn):
    item = storage.add_item(conn, date(2026, 5, 28), "Did a thing")
    assert isinstance(item.id, str)
    assert len(item.id) == 40
    assert item.work_date == date(2026, 5, 28)
    assert item.description == "Did a thing"
    assert item.created_at


def test_add_item_persists(conn):
    added = storage.add_item(conn, date(2026, 5, 28), "Did a thing")
    fetched = storage.get_item(conn, added.id)
    assert fetched.id == added.id
    assert fetched.description == "Did a thing"


def test_list_items_for_date(conn):
    storage.add_item(conn, date(2026, 5, 28), "today A")
    storage.add_item(conn, date(2026, 5, 27), "yesterday")
    storage.add_item(conn, date(2026, 5, 28), "today B")

    today_items = storage.list_items(conn, date(2026, 5, 28))
    assert len(today_items) == 2
    assert {i.description for i in today_items} == {"today A", "today B"}


def test_list_items_orders_by_created_at(conn):
    a = storage.add_item(conn, date(2026, 5, 28), "first")
    b = storage.add_item(conn, date(2026, 5, 28), "second")
    items = storage.list_items(conn, date(2026, 5, 28))
    assert [i.id for i in items] == [a.id, b.id]


def test_list_items_empty_for_unknown_date(conn):
    assert storage.list_items(conn, date(2026, 5, 28)) == []


def test_remove_item_deletes_row(conn):
    added = storage.add_item(conn, date(2026, 5, 28), "to remove")
    storage.remove_item(conn, added.id)
    assert storage.get_item(conn, added.id) is None


def test_remove_item_unknown_id_raises(conn):
    with pytest.raises(KeyError):
        storage.remove_item(conn, "0" * 40)


def test_get_item_unknown_returns_none(conn):
    assert storage.get_item(conn, "0" * 40) is None


def test_all_ids_returns_all_hashes(conn):
    a = storage.add_item(conn, date(2026, 5, 28), "A")
    b = storage.add_item(conn, date(2026, 5, 27), "B")
    assert set(storage.all_ids(conn)) == {a.id, b.id}


def test_all_ids_empty(conn):
    assert storage.all_ids(conn) == []


def test_add_item_before_inserts_with_earlier_timestamp(conn):
    target = storage.add_item(conn, date(2026, 5, 28), "target")
    new = storage.add_item_before(conn, target.id, "new")
    assert datetime.fromisoformat(new.created_at) < datetime.fromisoformat(target.created_at)


def test_add_item_before_appears_before_target_in_listing(conn):
    target = storage.add_item(conn, date(2026, 5, 28), "target")
    storage.add_item_before(conn, target.id, "new")
    items = storage.list_items(conn, date(2026, 5, 28))
    assert [i.description for i in items] == ["new", "target"]


def test_add_item_before_in_middle_of_list(conn):
    a = storage.add_item(conn, date(2026, 5, 28), "A")
    b = storage.add_item(conn, date(2026, 5, 28), "B")
    storage.add_item(conn, date(2026, 5, 28), "C")
    storage.add_item_before(conn, b.id, "new")
    items = storage.list_items(conn, date(2026, 5, 28))
    assert [i.description for i in items] == ["A", "new", "B", "C"]
    # And specifically the new item didn't displace A
    assert items[0].id == a.id


def test_add_item_before_takes_targets_work_date(conn):
    target = storage.add_item(conn, date(2026, 5, 27), "yesterday")
    new = storage.add_item_before(conn, target.id, "before yesterday")
    assert new.work_date == date(2026, 5, 27)


def test_add_item_before_unknown_target_raises(conn):
    with pytest.raises(KeyError):
        storage.add_item_before(conn, "0" * 40, "new")


def test_add_item_before_repeated_inserts_stay_ordered(conn):
    """Inserting before the same target twice should keep both before the target."""
    target = storage.add_item(conn, date(2026, 5, 28), "target")
    storage.add_item_before(conn, target.id, "first-insert")
    storage.add_item_before(conn, target.id, "second-insert")
    items = storage.list_items(conn, date(2026, 5, 28))
    descriptions = [i.description for i in items]
    # Both inserts come before target, regardless of which of them is first.
    assert descriptions[-1] == "target"
    assert set(descriptions[:2]) == {"first-insert", "second-insert"}
