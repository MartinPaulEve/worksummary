import re

import pytest
from click.testing import CliRunner

from worksummary import cli


@pytest.fixture
def runner(tmp_path, monkeypatch):
    """A CliRunner that points the CLI at a temp SQLite file."""
    db_file = tmp_path / "work.db"
    monkeypatch.setattr(cli.paths, "db_path", lambda: db_file)
    return CliRunner()


def _add(runner, *args):
    return runner.invoke(cli.cli, ["add", *args])


def _ls(runner, *args):
    return runner.invoke(cli.cli, ["ls", *args])


def _strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def _first_hash(ls_output: str) -> str:
    """Extract the full hash from the first ls line, stripping bracket decoration."""
    token = _strip_ansi(ls_output).strip().split()[0]
    return token.replace("[", "").replace("]", "")


def test_add_creates_item_and_confirms(runner):
    result = _add(runner, "Did a thing", "--date", "2026-05-28")
    assert result.exit_code == 0
    assert "Added" in result.output
    assert "2026-05-28" in result.output
    assert "Did a thing" in result.output


def test_add_rejects_invalid_date(runner):
    result = _add(runner, "Did a thing", "--date", "yesterday")
    assert result.exit_code != 0
    assert "YYYY-MM-DD" in result.output


def test_add_defaults_to_today(runner):
    result = _add(runner, "today thing")
    assert result.exit_code == 0
    result2 = _ls(runner)
    assert "today thing" in _strip_ansi(result2.output)


def test_ls_shows_items_for_date(runner):
    _add(runner, "A", "--date", "2026-05-28")
    _add(runner, "B", "--date", "2026-05-27")
    result = _ls(runner, "--date", "2026-05-28")
    assert result.exit_code == 0
    output = _strip_ansi(result.output)
    assert "A" in output
    assert "B" not in output


def test_ls_empty_date_friendly_message(runner):
    result = _ls(runner, "--date", "2026-05-28")
    assert result.exit_code == 0
    assert "No work items recorded for 2026-05-28" in result.output


def test_remove_by_prefix(runner):
    _add(runner, "to remove", "--date", "2026-05-28")
    hash_str = _first_hash(_ls(runner, "--date", "2026-05-28").output)
    result = runner.invoke(cli.cli, ["remove", hash_str[0]])
    assert result.exit_code == 0
    assert "Removed" in result.output

    ls_out = _ls(runner, "--date", "2026-05-28").output
    assert "No work items recorded" in ls_out


def test_remove_unknown_prefix_errors(runner):
    result = runner.invoke(cli.cli, ["remove", "zzzz"])
    assert result.exit_code != 0
    assert "no item matches" in result.output.lower() or "not found" in result.output.lower()


def test_remove_ambiguous_prefix_errors(runner, monkeypatch):
    # Deterministic hashes that share a first-char prefix.
    fixed_ids = iter(
        [
            "a" + "1" * 39,
            "a" + "2" * 39,
        ]
    )
    monkeypatch.setattr(cli.ids, "generate_id", lambda desc, ts: next(fixed_ids))

    _add(runner, "first")
    _add(runner, "second")

    result = runner.invoke(cli.cli, ["remove", "a"])
    assert result.exit_code != 0
    assert "ambiguous" in result.output.lower()


def test_replace_swaps_item(runner):
    _add(runner, "original", "--date", "2026-05-28")
    hash_str = _first_hash(_ls(runner, "--date", "2026-05-28").output)

    result = runner.invoke(cli.cli, ["replace", hash_str[0], "updated"])
    assert result.exit_code == 0
    assert "Replaced" in result.output

    final = _strip_ansi(_ls(runner, "--date", "2026-05-28").output)
    assert "original" not in final
    assert "updated" in final


def test_summary_outputs_teams_friendly_text(runner):
    _add(runner, "Did a thing https://example.com/1", "--date", "2026-05-28")
    _add(runner, "Did another thing", "--date", "2026-05-28")
    result = runner.invoke(cli.cli, ["summary", "--date", "2026-05-28"])
    assert result.exit_code == 0
    # Header uses Unicode bold (renders bold on paste; markdown ** does not).
    assert "𝐖𝐨𝐫𝐤" in result.output
    assert "𝐓𝐡𝐮 𝟐𝟖 𝐌𝐚𝐲 𝟐𝟎𝟐𝟔" in result.output
    assert "**" not in result.output  # no markdown asterisks leaking through
    assert "- Did a thing [¹]" in result.output
    assert "- Did another thing" in result.output
    assert "𝐑𝐞𝐟𝐞𝐫𝐞𝐧𝐜𝐞𝐬" in result.output
    assert "1. https://example.com/1" in result.output


def test_ls_prefix_is_globally_unique_so_remove_works(runner, monkeypatch):
    """The prefix shown by `ls --date X` must work with `remove`, even if
    another item on a different date shares leading hash characters."""
    fixed_ids = iter(
        [
            "a" + "1" * 39,  # added to 2026-05-27
            "a" + "2" * 39,  # added to 2026-05-28 (today's filter)
        ]
    )
    monkeypatch.setattr(cli.ids, "generate_id", lambda desc, ts: next(fixed_ids))

    _add(runner, "yesterday", "--date", "2026-05-27")
    _add(runner, "today", "--date", "2026-05-28")

    # `ls --date 2026-05-28` only shows the "today" item. The displayed
    # prefix must be globally unique — so removing it must succeed.
    ls_out = _strip_ansi(_ls(runner, "--date", "2026-05-28").output)
    assert "[a2]" in ls_out  # not just "[a]" — global prefix needs two chars

    result = runner.invoke(cli.cli, ["remove", "a2"])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_summary_empty_date(runner):
    result = runner.invoke(cli.cli, ["summary", "--date", "2026-05-28"])
    assert result.exit_code == 0
    assert "No work items recorded for 2026-05-28" in result.output
