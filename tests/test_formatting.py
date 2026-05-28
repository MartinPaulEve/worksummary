from datetime import date

from worksummary import formatting
from worksummary.storage import Item


def make_item(id_: str, desc: str, created_at: str = "2026-05-28T11:42:00") -> Item:
    return Item(
        id=id_.ljust(40, "0"),
        work_date=date(2026, 5, 28),
        created_at=created_at,
        description=desc,
    )


def test_format_summary_no_items():
    output = formatting.format_summary([], date(2026, 5, 28))
    assert output == "No work items recorded for 2026-05-28."


def test_format_summary_header():
    items = [make_item("a", "Did a thing")]
    output = formatting.format_summary(items, date(2026, 5, 28))
    assert output.startswith("**Work — Thu 28 May 2026**")


def test_format_summary_no_urls_omits_references():
    items = [
        make_item("a", "Did a thing"),
        make_item("b", "Did another thing"),
    ]
    output = formatting.format_summary(items, date(2026, 5, 28))
    assert "**References**" not in output
    assert "- Did a thing" in output
    assert "- Did another thing" in output


def test_format_summary_single_url_produces_reference():
    items = [make_item("a", "Fixed bug https://example.com/1")]
    output = formatting.format_summary(items, date(2026, 5, 28))
    assert "- Fixed bug [1]" in output
    assert "**References**" in output
    assert "1. https://example.com/1" in output


def test_format_summary_numbers_urls_globally_across_items():
    items = [
        make_item("a", "Reviewed https://a.com and https://b.com"),
        make_item("b", "Fixed https://c.com"),
        make_item("c", "Plain bullet"),
    ]
    output = formatting.format_summary(items, date(2026, 5, 28))
    assert "- Reviewed [1] and [2]" in output
    assert "- Fixed [3]" in output
    assert "- Plain bullet" in output
    assert "1. https://a.com" in output
    assert "2. https://b.com" in output
    assert "3. https://c.com" in output


def test_format_summary_adjacent_urls_in_one_bullet():
    items = [make_item("a", "Reviewed https://a.com https://b.com today")]
    output = formatting.format_summary(items, date(2026, 5, 28))
    assert "- Reviewed [1][2] today" in output


def test_format_summary_uses_correct_weekday():
    # 2026-05-29 is a Friday
    items = [make_item("a", "Did a thing")]
    output = formatting.format_summary(items, date(2026, 5, 29))
    assert "Fri 29 May 2026" in output


def test_format_ls_no_items():
    output = formatting.format_ls([], date(2026, 5, 28), use_color=False)
    assert output == "No work items recorded for 2026-05-28."


def test_format_ls_shows_full_hash_and_time_and_description():
    item = Item(
        id="a" * 40,
        work_date=date(2026, 5, 28),
        created_at="2026-05-28T11:42:00",
        description="Did a thing",
    )
    output = formatting.format_ls([item], date(2026, 5, 28), use_color=False)
    assert "a" * 40 in output
    assert "11:42" in output
    assert "Did a thing" in output


def test_format_ls_uncolored_returns_plain_text():
    items = [
        Item(
            id="a" * 40,
            work_date=date(2026, 5, 28),
            created_at="2026-05-28T11:42:00",
            description="Plain",
        )
    ]
    output = formatting.format_ls(items, date(2026, 5, 28), use_color=False)
    assert "\x1b[" not in output


def test_format_ls_colored_includes_ansi_escape():
    items = [
        Item(
            id="a" * 40,
            work_date=date(2026, 5, 28),
            created_at="2026-05-28T11:42:00",
            description="Coloured",
        )
    ]
    output = formatting.format_ls(items, date(2026, 5, 28), use_color=True)
    assert "\x1b[" in output


def test_format_ls_colors_only_unique_prefix():
    import re

    items = [
        Item(
            id="ab" + "0" * 38,
            work_date=date(2026, 5, 28),
            created_at="2026-05-28T11:42:00",
            description="first",
        ),
        Item(
            id="ac" + "0" * 38,
            work_date=date(2026, 5, 28),
            created_at="2026-05-28T11:43:00",
            description="second",
        ),
    ]
    output = formatting.format_ls(items, date(2026, 5, 28), use_color=True)
    # The colored prefix interrupts the hash with ANSI escapes; strip them
    # to verify the full hash is present once color codes are removed.
    stripped = re.sub(r"\x1b\[[0-9;]*m", "", output)
    assert "\x1b[" in output
    assert "ab" + "0" * 38 in stripped
    assert "ac" + "0" * 38 in stripped
    # The first two characters of each id should appear as colored prefixes
    # in the raw output, immediately followed by the rest of the hash.
    assert "ab\x1b[0m" + "0" * 38 in output
    assert "ac\x1b[0m" + "0" * 38 in output
