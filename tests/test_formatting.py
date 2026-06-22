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


def _dated_item(d: date, desc: str) -> Item:
    return Item(
        id=desc.ljust(40, "0"),
        work_date=d,
        created_at=f"{d.isoformat()}T09:00:00",
        description=desc,
    )


def test_format_week_renders_one_summary_block_per_non_empty_day():
    days = [
        (date(2026, 5, 27), [_dated_item(date(2026, 5, 27), "Tuesday task")]),
        (date(2026, 5, 28), [_dated_item(date(2026, 5, 28), "Wednesday task")]),
    ]
    output = formatting.format_week(days)
    assert _bold("Wed 27 May 2026") in output
    assert _bold("Thu 28 May 2026") in output
    assert "- Tuesday task" in output
    assert "- Wednesday task" in output
    # The Tuesday block comes before the Wednesday block.
    assert output.index("Tuesday task") < output.index("Wednesday task")


def test_format_week_skips_days_with_no_items():
    days = [
        (date(2026, 5, 27), []),
        (date(2026, 5, 28), [_dated_item(date(2026, 5, 28), "Only this day")]),
    ]
    output = formatting.format_week(days)
    assert "- Only this day" in output
    # The empty day must not appear at all, not even as a "No work items" line.
    assert "2026-05-27" not in output
    assert "No work items" not in output


def test_format_week_separates_day_blocks_with_blank_line():
    days = [
        (date(2026, 5, 27), [_dated_item(date(2026, 5, 27), "Day one")]),
        (date(2026, 5, 28), [_dated_item(date(2026, 5, 28), "Day two")]),
    ]
    output = formatting.format_week(days)
    # Two independent summary blocks joined by a blank line.
    blocks = output.split("\n\n" + _bold("Work"))
    assert len(blocks) == 2


def test_format_week_all_days_empty_reports_range():
    days = [
        (date(2026, 5, 22), []),
        (date(2026, 5, 23), []),
        (date(2026, 5, 28), []),
    ]
    output = formatting.format_week(days)
    assert output == "No work items recorded for 2026-05-22 to 2026-05-28."


def test_format_ls_no_items():
    output = formatting.format_ls([], date(2026, 5, 28), [], use_color=False)
    assert output == "No work items recorded for 2026-05-28."


def test_format_ls_shows_full_hash_and_date_and_time_and_description():
    item = Item(
        id="a" * 40,
        work_date=date(2026, 5, 28),
        created_at="2026-05-28T11:42:00",
        description="Did a thing",
    )
    output = formatting.format_ls([item], date(2026, 5, 28), [item.id], use_color=False)
    # Brackets are decoration; the full hash chars must still appear
    output_no_brackets = output.replace("[", "").replace("]", "")
    assert "a" * 40 in output_no_brackets
    assert "2026-05-28" in output
    assert "11:42" in output
    assert "Did a thing" in output


def test_format_ls_includes_each_items_own_date():
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
    output = formatting.format_ls(items, date(2026, 5, 28), [i.id for i in items], use_color=False)
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
    output = formatting.format_ls(items, date(2026, 5, 28), [items[0].id], use_color=False)
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
    output = formatting.format_ls(items, date(2026, 5, 28), [items[0].id], use_color=True)
    assert "\x1b[" in output


def test_format_ls_colors_only_unique_prefix_inside_brackets():
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
    all_hashes = [i.id for i in items]
    output = formatting.format_ls(items, date(2026, 5, 28), all_hashes, use_color=True)
    stripped = re.sub(r"\x1b\[[0-9;]*m", "", output)
    # With ANSI removed, prefix is wrapped in literal [brackets]
    assert "[ab]" + "0" * 38 in stripped
    assert "[ac]" + "0" * 38 in stripped
    # Brackets themselves are NOT inside the red color codes
    assert "[\x1b[" in output  # opening bracket immediately precedes ANSI escape


def test_format_ls_wraps_prefix_in_square_brackets_when_uncolored():
    items = [
        Item(
            id="aeb1ed72145de30f2d920d63ae5d183cf9bcfc72",
            work_date=date(2026, 5, 28),
            created_at="2026-05-28T11:42:00",
            description="example",
        ),
        Item(
            id="aeb29c4d1e0f8b3a5c6d7e8f9a0b1c2d3e4f5a6b",
            work_date=date(2026, 5, 28),
            created_at="2026-05-28T11:43:00",
            description="other",
        ),
    ]
    all_hashes = [i.id for i in items]
    output = formatting.format_ls(items, date(2026, 5, 28), all_hashes, use_color=False)
    # The two items share "aeb" so the unique prefix is "aeb1" / "aeb2".
    assert "[aeb1]ed72145de30f2d920d63ae5d183cf9bcfc72" in output
    assert "[aeb2]9c4d1e0f8b3a5c6d7e8f9a0b1c2d3e4f5a6b" in output


def test_format_ls_prefix_unique_across_all_hashes_not_just_visible():
    """If only one item is visible but another globally shares its leading
    characters, the displayed prefix must reflect the global ambiguity so
    `remove <prefix>` actually works."""
    visible = [
        Item(
            id="a" + "0" * 39,
            work_date=date(2026, 5, 28),
            created_at="2026-05-28T11:42:00",
            description="visible",
        ),
    ]
    # Another item exists in the DB on a different date, also starting with 'a'.
    all_hashes = ["a" + "0" * 39, "a" + "1" * 39]
    output = formatting.format_ls(visible, date(2026, 5, 28), all_hashes, use_color=False)
    # Among just visible items, "a" alone would be unique — but globally we
    # need "a0". Verify the wider prefix is shown.
    assert "[a0]" + "0" * 38 in output
    # And the 1-char form must NOT appear.
    assert "[a]0" + "0" * 38 not in output
