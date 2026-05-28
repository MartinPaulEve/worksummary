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
    ls_out = _strip_ansi(_ls(runner, "--date", "2026-05-28").output)
    hash_str = ls_out.strip().split()[0]
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
    ls_out = _strip_ansi(_ls(runner, "--date", "2026-05-28").output)
    hash_str = ls_out.strip().split()[0]

    result = runner.invoke(cli.cli, ["replace", hash_str[0], "updated"])
    assert result.exit_code == 0
    assert "Replaced" in result.output

    final = _strip_ansi(_ls(runner, "--date", "2026-05-28").output)
    assert "original" not in final
    assert "updated" in final


def test_summary_outputs_teams_markdown(runner):
    _add(runner, "Did a thing https://example.com/1", "--date", "2026-05-28")
    _add(runner, "Did another thing", "--date", "2026-05-28")
    result = runner.invoke(cli.cli, ["summary", "--date", "2026-05-28"])
    assert result.exit_code == 0
    assert "**Work — Thu 28 May 2026**" in result.output
    assert "- Did a thing [1]" in result.output
    assert "- Did another thing" in result.output
    assert "**References**" in result.output
    assert "1. https://example.com/1" in result.output


def test_summary_empty_date(runner):
    result = runner.invoke(cli.cli, ["summary", "--date", "2026-05-28"])
    assert result.exit_code == 0
    assert "No work items recorded for 2026-05-28" in result.output
