# worksummary

A command-line tool for logging daily work items and producing a Microsoft Teams-ready summary. Disclaimer/warning: produced with AI as a personal tool. Tested on Ubuntu Linux and nowhere else yet. Testing on Mac soon.

## Install

```bash
uv sync
uv run pre-commit install
```

The first `worksummary` invocation creates an SQLite database under `$XDG_DATA_HOME/worksummary/work.db` (or `~/.local/share/worksummary/work.db` if `XDG_DATA_HOME` is unset).

## Commands

```bash
# Add an item (defaults to today)
worksummary add "Fixed bug 128 https://github.com/example/repo/issues/128"
worksummary add "Reviewed yesterday's PR" --date 2026-05-27

# List items for a date (full hash with unique-prefix coloring)
worksummary ls
worksummary ls --date 2026-05-27

# Remove an item by id prefix (shortest unique prefix or any longer one)
worksummary remove 6
worksummary remove 640ab2

# Replace an item (delete + add on the same date)
worksummary replace 6 "Fixed bug 128 and added regression test"

# Render a Teams-ready summary
worksummary summary
worksummary summary --date 2026-05-27
```

## Output

`summary` produces markdown that renders cleanly when pasted into a Teams channel:

```
**Work — Thu 28 May 2026**

- Fixed bug 128 [1]
- Reviewed PR for new menu items [2][3]
- Pair-programmed on auth refactor

**References**
1. https://github.com/example/repo/issues/128
2. https://github.com/example/repo/pull/42
3. https://github.com/example/repo/issues/88
```

## Development

```bash
uv run pytest
uv run ruff check
uv run ruff format
```

See `docs/superpowers/specs/` for the design document and `docs/superpowers/plans/` for the implementation plan.
