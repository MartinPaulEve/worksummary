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


def _bold(text: str) -> str:
    """Reference implementation of Unicode Mathematical Bold conversion for tests."""
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(chr(0x1D400 + ord(ch) - ord("A")))
        elif "a" <= ch <= "z":
            out.append(chr(0x1D41A + ord(ch) - ord("a")))
        elif "0" <= ch <= "9":
            out.append(chr(0x1D7CE + ord(ch) - ord("0")))
        else:
            out.append(ch)
    return "".join(out)


def test_format_summary_no_items():
    output = formatting.format_summary([], date(2026, 5, 28))
    assert output == "No work items recorded for 2026-05-28."


def test_format_summary_header_uses_unicode_bold_not_markdown():
    items = [make_item("a", "Did a thing")]
    output = formatting.format_summary(items, date(2026, 5, 28))
    # No literal asterisks should leak into the pasted output.
    assert "**" not in output
    # Header is Unicode-bold version of "Work — Thu 28 May 2026"
    expected_header = _bold("Work") + " — " + _bold("Thu 28 May 2026")
    assert output.startswith(expected_header)


def test_format_summary_no_urls_omits_references():
    items = [
        make_item("a", "Did a thing"),
        make_item("b", "Did another thing"),
    ]
    output = formatting.format_summary(items, date(2026, 5, 28))
    assert _bold("References") not in output
    assert "References" not in output  # extra safety: no plain "References" either
    assert "- Did a thing" in output
    assert "- Did another thing" in output


def test_format_summary_single_url_produces_reference():
    items = [make_item("a", "Fixed bug https://example.com/1")]
    output = formatting.format_summary(items, date(2026, 5, 28))
    assert "- Fixed bug [¹]" in output
    assert _bold("References") in output
    # References list keeps plain digits (ordered-list rendering in Teams).
    assert "1. https://example.com/1" in output


def test_format_summary_numbers_urls_globally_across_items():
    items = [
        make_item("a", "Reviewed https://a.com and https://b.com"),
        make_item("b", "Fixed https://c.com"),
        make_item("c", "Plain bullet"),
    ]
    output = formatting.format_summary(items, date(2026, 5, 28))
    assert "- Reviewed [¹] and [²]" in output
    assert "- Fixed [³]" in output
    assert "- Plain bullet" in output
    assert "1. https://a.com" in output
    assert "2. https://b.com" in output
    assert "3. https://c.com" in output


def test_format_summary_adjacent_urls_in_one_bullet():
    items = [make_item("a", "Reviewed https://a.com https://b.com today")]
    output = formatting.format_summary(items, date(2026, 5, 28))
    assert "- Reviewed [¹][²] today" in output


def test_format_summary_uses_correct_weekday():
    # 2026-05-29 is a Friday
    items = [make_item("a", "Did a thing")]
    output = formatting.format_summary(items, date(2026, 5, 29))
    assert _bold("Fri 29 May 2026") in output


def test_format_summary_header_contains_literal_bold_unicode():
    # Direct sanity check that the bold Unicode characters are actually present.
    items = [make_item("a", "Did a thing")]
    output = formatting.format_summary(items, date(2026, 5, 28))
    assert "𝐖" in output  # bold capital W
    assert "𝟐" in output  # bold digit 2


def test_format_ls_no_items():
    output = formatting.format_ls([], date(2026, 5, 28), use_color=False)
    assert output == "No work items recorded for 2026-05-28."


def test_format_ls_shows_full_hash_and_date_and_time_and_description():
    item = Item(
        id="a" * 40,
        work_date=date(2026, 5, 28),
        created_at="2026-05-28T11:42:00",
        description="Did a thing",
    )
    output = formatting.format_ls([item], date(2026, 5, 28), use_color=False)
    assert "a" * 40 in output
    assert "2026-05-28" in output
    assert "11:42" in output
    assert "Did a thing" in output


def test_format_ls_includes_each_items_own_date():
    # Confirms ls labels every row with the entry's work_date — useful when
    # browsing items that span multiple days.
    items = [
        Item(
            id="a" * 40,
            work_date=date(2026, 5, 27),
            created_at="2026-05-27T09:00:00",
            description="yesterday work",
        ),
        Item(
            id="b" * 40,
            work_date=date(2026, 5, 28),
            created_at="2026-05-28T14:00:00",
            description="today work",
        ),
    ]
    output = formatting.format_ls(items, date(2026, 5, 28), use_color=False)
    yesterday_line = next(line for line in output.splitlines() if "yesterday work" in line)
    today_line = next(line for line in output.splitlines() if "today work" in line)
    assert "2026-05-27" in yesterday_line
    assert "2026-05-28" in today_line


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
