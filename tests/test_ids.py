import pytest

from worksummary import ids


def test_generate_id_returns_40_char_hex():
    result = ids.generate_id("some description", "2026-05-28T11:42:00")
    assert len(result) == 40
    assert all(c in "0123456789abcdef" for c in result)


def test_generate_id_is_unique_for_identical_input():
    a = ids.generate_id("same", "2026-05-28T11:42:00")
    b = ids.generate_id("same", "2026-05-28T11:42:00")
    assert a != b


def test_shortest_unique_prefixes_empty():
    assert ids.shortest_unique_prefixes([]) == {}


def test_shortest_unique_prefixes_single():
    assert ids.shortest_unique_prefixes(["abc"]) == {"abc": 1}


def test_shortest_unique_prefixes_all_distinct_first_char():
    result = ids.shortest_unique_prefixes(["abc", "bcd", "cde"])
    assert result == {"abc": 1, "bcd": 1, "cde": 1}


def test_shortest_unique_prefixes_shared_prefix():
    result = ids.shortest_unique_prefixes(["aaa", "aab", "bbc"])
    assert result == {"aaa": 3, "aab": 3, "bbc": 1}


def test_shortest_unique_prefixes_two_share_one_doesnt():
    result = ids.shortest_unique_prefixes(
        [
            "640ab2bae07bedc4c163f679a746f7ab7fb5d1fa",
            "6ab2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
            "2e7a9c4d1e0f8b3a5c6d7e8f9a0b1c2d3e4f5a6b",
        ]
    )
    assert result["640ab2bae07bedc4c163f679a746f7ab7fb5d1fa"] == 2
    assert result["6ab2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"] == 2
    assert result["2e7a9c4d1e0f8b3a5c6d7e8f9a0b1c2d3e4f5a6b"] == 1


def test_resolve_unique_short_prefix():
    hashes = ["abc", "bcd"]
    assert ids.resolve("a", hashes) == "abc"
    assert ids.resolve("b", hashes) == "bcd"


def test_resolve_accepts_longer_than_minimum_prefix():
    hashes = ["abc", "bcd"]
    assert ids.resolve("ab", hashes) == "abc"
    assert ids.resolve("abc", hashes) == "abc"


def test_resolve_ambiguous_raises():
    hashes = ["abc", "abd", "xyz"]
    with pytest.raises(ids.AmbiguousIdError) as exc_info:
        ids.resolve("ab", hashes)
    assert set(exc_info.value.candidates) == {"abc", "abd"}
    assert exc_info.value.prefix == "ab"


def test_resolve_not_found_raises():
    with pytest.raises(ids.NotFoundError) as exc_info:
        ids.resolve("z", ["abc", "def"])
    assert exc_info.value.prefix == "z"


def test_resolve_prefix_longer_than_any_hash_not_found():
    with pytest.raises(ids.NotFoundError):
        ids.resolve("abcdef", ["abc", "abd"])
