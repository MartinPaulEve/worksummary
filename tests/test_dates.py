from datetime import date

import pytest

from worksummary import dates


def test_parse_iso_date_valid():
    assert dates.parse_iso_date("2026-05-28") == date(2026, 5, 28)


def test_parse_iso_date_rejects_natural_language():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        dates.parse_iso_date("yesterday")


def test_parse_iso_date_rejects_alternate_format():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        dates.parse_iso_date("28/05/2026")


def test_parse_iso_date_rejects_empty():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        dates.parse_iso_date("")


def test_today_returns_a_date():
    result = dates.today()
    assert isinstance(result, date)


def test_format_iso_round_trips():
    d = date(2026, 5, 28)
    assert dates.format_iso(d) == "2026-05-28"
    assert dates.parse_iso_date(dates.format_iso(d)) == d


def test_past_week_returns_seven_days_ending_at_end():
    result = dates.past_week(date(2026, 5, 28))
    assert result == [
        date(2026, 5, 22),
        date(2026, 5, 23),
        date(2026, 5, 24),
        date(2026, 5, 25),
        date(2026, 5, 26),
        date(2026, 5, 27),
        date(2026, 5, 28),
    ]


def test_past_week_is_chronological_and_includes_end():
    result = dates.past_week(date(2026, 1, 3))
    assert len(result) == 7
    assert result == sorted(result)
    assert result[-1] == date(2026, 1, 3)
    # Spans across a month boundary correctly.
    assert result[0] == date(2025, 12, 28)
