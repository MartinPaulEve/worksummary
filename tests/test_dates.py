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
