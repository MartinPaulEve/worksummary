# worksummary — Design

**Date:** 2026-05-28
**Status:** Draft for review

## Purpose

A personal command-line tool for logging work items done during the day and producing a formatted summary suitable for pasting into a Microsoft Teams channel.

The user runs short commands throughout the day to record what they did, then runs `worksummary summary` (typically at end-of-day or in a standup) to get a Teams-ready bulleted list.

## Goals

- Friction-free capture: `worksummary add "..."` should be the only thing standing between a thought and a logged item.
- Lossless URL handling: URLs pasted into descriptions are preserved and rendered cleanly in Teams output.
- Easy retrospective edits: items can be added to past or future dates, removed, or replaced.
- Identifiers that are stable but ergonomic: full SHA-1 hashes underneath, shortest-unique prefixes for human use.

## Non-goals

- Multi-user / shared storage.
- Sync across machines (single local SQLite file).
- Categorisation, tagging, projects, search.
- Rich-text descriptions beyond plain text with embedded URLs.
- Time tracking (duration of work).

## Architecture

A single Click-based CLI Python package named `worksummary`, packaged with `uv` and `pyproject.toml`. Storage is local SQLite via stdlib `sqlite3`.

### Module layout

```
worksummary/
  __init__.py
  __version__.py
  cli.py            # Click command definitions; thin shell over services
  storage.py        # DB connection, schema migration, CRUD operations
  ids.py            # Hash generation, prefix resolution, shortest-unique-prefix computation
  dates.py          # ISO date parsing, today/specific-date helpers
  urls.py           # URL extraction from description text
  formatting.py     # Teams summary renderer, `ls` colored renderer
  paths.py          # XDG path resolution for DB location
tests/
  test_storage.py
  test_ids.py
  test_dates.py
  test_urls.py
  test_formatting.py
  test_cli.py       # Click CliRunner-based integration tests
pyproject.toml
__version__.py      # Top-level version file (mirrors package version for commitizen)
README.md
.github/workflows/version-release.yml
.pre-commit-config.yaml
```

### Boundaries

- `cli.py` only parses arguments and calls into the other modules. No SQL, no formatting, no business logic.
- `storage.py` is the sole holder of SQL. Every query lives here. Returns plain Python data (dataclasses or dicts), not raw rows.
- `ids.py`, `dates.py`, `urls.py`, `formatting.py`, `paths.py` are pure (no I/O except `paths.py` resolving env vars). They take inputs and return outputs — easy to test.
- This separation means each module can be reasoned about and tested independently.

## Data model

A single SQLite table:

```sql
CREATE TABLE items (
  id          TEXT PRIMARY KEY,    -- 40-char SHA-1 hex
  work_date   TEXT NOT NULL,       -- ISO YYYY-MM-DD; the day the work belongs to
  created_at  TEXT NOT NULL,       -- ISO timestamp; when the row was added
  description TEXT NOT NULL        -- raw user text, URLs embedded inline
);
CREATE INDEX idx_items_work_date ON items(work_date);
```

### ID generation

Each item's `id` is the SHA-1 of:
```
description + "\0" + created_at + "\0" + os.urandom(16).hex()
```
Random salt guarantees uniqueness even for identical descriptions added at the same instant.

### URL storage

URLs are stored inline in `description`, not in a separate column or table. The renderer extracts them at output time with a regex. Rationale:

- Editing/replacing an item keeps the URLs coupled to the text — no risk of orphaned URL rows.
- The user wrote the URLs into the description naturally; we don't change what they typed.
- Extraction at render time is cheap.

## ID prefix resolution

The user types the shortest prefix that uniquely identifies an item. The `ls` command shows them which prefix is currently unique. Note that the user should be able to use a more specific ID if they wish. That is if the shortest prefix for an item is 64, but the user gives 6401 or even the whole hash, that should also work. They can be more specific than the shortest unique prefix if they want.

### `shortest_unique_prefixes(hashes: list[str]) -> dict[str, int]`

Returns a dict mapping each full hash to the minimum prefix length that uniquely identifies it among the input set.

Algorithm: for each hash, find the smallest `k` such that no other hash in the set shares the same first `k` characters. The minimum value of `k` is 1.

### `resolve(prefix: str, hashes: Iterable[str]) -> str`

- Returns the single full hash starting with `prefix`.
- Raises `AmbiguousIdError(prefix, candidates)` if more than one matches; the error includes the candidate hashes (and their unique prefixes) so the CLI can show a helpful message.
- Raises `NotFoundError(prefix)` if zero match.

The CLI calls `resolve()` against the set of *all* hashes in the DB (or could scope to a date if performance ever mattered — it won't for a personal log).

## Commands

```
worksummary add "text" [--date YYYY-MM-DD]
worksummary ls [--date YYYY-MM-DD]
worksummary remove <id-prefix>
worksummary replace <id-prefix> "new text"
worksummary summary [--date YYYY-MM-DD]
```

Date defaults to today (local time) where omitted. `--date` accepts ISO `YYYY-MM-DD` only.

### `add`

Inserts a new item. Prints a confirmation line including the new item's shortest unique prefix and the work date.

```
$ worksummary add "Fixed bug 128 https://github.com/MESH-Research/knowledge-commons-profiles/issues/597"
Added [a3] on 2026-05-28: Fixed bug 128 https://github.com/MESH-Research/knowledge-commons-profiles/issues/597
```

### `ls`

Lists items for the given date (default today). Each item shows the full 40-character hash with the shortest unique prefix colored red, so the user can see at a glance how many leading characters they need to type for `remove`/`replace`.

```
$ worksummary ls
[6]40ab2bae07bedc4c163f679a746f7ab7fb5d1fa  11:42  Fixed bug 128 https://github.com/MESH-Research/knowledge-commons-profiles/issues/597
[2]e7a9c4d1e0f8b3a5c6d7e8f9a0b1c2d3e4f5a6b7  12:01  Updated documentation
[a]3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b  14:15  Pair-programmed on auth refactor
```

(Brackets above stand in for red ANSI coloring — in the terminal, just the bracketed character(s) appear red.)

Columns: full 40-char hash with unique-prefix portion in red, creation time (HH:MM), description. All hashes are the same length, so no padding is needed. If two items share leading characters, the colored portion grows accordingly (e.g. if two hashes both start with `6`, the first might show `64` red and the second `6a` red).

Coloring uses Click's `style()` so it auto-disables when stdout isn't a TTY (e.g. when piped to a file).

### `remove`

Removes the item identified by the prefix. Prints a confirmation. Errors if the prefix is ambiguous or unknown.

```
$ worksummary remove 6
Removed: Fixed bug 128 https://github.com/MESH-Research/knowledge-commons-profiles/issues/597

$ worksummary remove 6     # after previous adds (not shown) added a second '6...' item
Error: prefix '6' is ambiguous. Matches:
  64  Updated documentation
  6a  Reviewed PR
```

### `replace`

Equivalent to `remove <id>` followed by `add` with the same `work_date`. The new item gets a fresh ID (since its content changed). Prints the new ID's prefix.

```
$ worksummary replace 6 "Fixed bug 128 and added regression test"
Replaced [6] with [a3]: Fixed bug 128 and added regression test
```

### `summary`

Renders the date's items as Teams-ready markdown to stdout.

```
$ worksummary summary
**Work — Wed 28 May 2026**

- Fixed bug 128 [1]
- Reviewed PR for new menu items [2][3]
- Pair-programmed on auth refactor

**References**
1. https://github.com/MESH-Research/knowledge-commons-profiles/issues/597
2. https://github.com/example/repo/pull/42
3. https://github.com/example/repo/issues/88
```

Rules:

- Header is bold: `**Work — <weekday> <day> <Month> <year>**`.
- Bullets use markdown dashes (`- `).
- For each URL in a bullet's description, in left-to-right order: strip the URL from the bullet text, append a `[N]` reference where N is the next global footnote number, and add the URL to the References list. Multiple URLs in one bullet produce sequential refs like `[1][2]`. These references (the in-text "[1]" etc.) should be in superscript.
- Whitespace left behind by removed URLs is collapsed (multiple spaces become one; trailing space before punctuation removed).
- If a day has no items, output a single line: `No work items recorded for 2026-05-28.` (no header, no bullets).
- If items exist but no URLs, the References section is omitted entirely (no header, no list).

## URL extraction

Regex: `https?://\S+` with trailing punctuation stripped (`.,;:!?)]}`).

Rationale: simple, fast, predictable. We don't need to handle bare `www.` or other scheme-less URLs — they're not common in this user's workflow and parsing them is error-prone.

Edge cases handled:
- URL at end of bullet followed by sentence punctuation: `see https://example.com.` → URL is `https://example.com`, the `.` stays in the text.
- URL in parens: `(see https://example.com)` → URL is `https://example.com`, `)` stays.
- Multiple URLs in one bullet: extracted in order, each gets a separate footnote.

## Date handling

`--date` parses ISO `YYYY-MM-DD` strictly. Anything else errors with a clear message:

```
Error: --date must be in YYYY-MM-DD format (got 'yesterday').
```

`work_date` is stored as ISO `YYYY-MM-DD`. `created_at` is stored as ISO 8601 with seconds precision, local time, no timezone suffix (this is a single-user single-machine tool — timezone portability isn't a goal).

## Storage location

XDG-compliant path:
- `$XDG_DATA_HOME/worksummary/work.db` if `XDG_DATA_HOME` is set
- otherwise `~/.local/share/worksummary/work.db`

The directory is created on first run. The DB schema is created if the file doesn't exist or the `items` table is missing. No migrations needed in v1 — if the schema changes later, we add a simple version check.

## Error handling

User-facing errors print to stderr with exit code 1 and no Python traceback. Categories:

- Invalid input (bad date format, unknown command): Click handles these natively.
- Ambiguous ID prefix: print candidates, exit 1.
- ID prefix not found: print message, exit 1.
- No items for the requested date (`ls`, `summary`): print a friendly message, exit 0 (not an error).
- DB I/O errors: surface the OS error message, exit 1.

## Testing strategy

Per the project's TDD convention (red/green):

- All function stubs raise `NotImplementedError`.
- Tests are written first and must fail before implementation.
- Unit tests are isolated: pure modules tested directly; `storage.py` tested against an in-memory SQLite (`:memory:`); `cli.py` tested with Click's `CliRunner`, monkey-patching `paths.db_path()` to point at a temp file.
- Tests verify behaviour (return values, side-effects on the DB) not implementation (no counting function calls, no asserting on log output).
- Coverage target: each module's public API exercised by at least one happy-path and one error-path test. The `formatting.py` Teams output has dedicated tests for: no items, items without URLs, items with one URL, items with multiple URLs, multiple items with URLs interleaved (verifying global numbering).

## Setup & packaging

- `pyproject.toml` with `[project.scripts] worksummary = "worksummary.cli:cli"` so `uv run worksummary ...` works.
- Top-level `__version__.py` and `worksummary/__version__.py` both set to `1.0.0`, kept in sync by commitizen.
- `.pre-commit-config.yaml` with `ruff check` and `ruff format`.
- `.github/workflows/version-release.yml` as specified in the user's global CLAUDE.md.
- Python `>=3.12` per the global CLAUDE.md template.

## Open questions

None — all design decisions are settled.
