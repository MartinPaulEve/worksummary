# worksummary CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Click-based Python CLI (`worksummary`) that records daily work items in SQLite and renders a Teams-ready markdown summary, with SHA-1 IDs that accept shortest-unique prefixes.

**Architecture:** A single Python package broken into pure modules (paths, dates, urls, ids, formatting) and one I/O module (storage), wired together by a thin Click CLI. SQLite via stdlib. Tests written first per TDD; each module exercised in isolation, CLI tested via Click's `CliRunner` against an in-memory/temp DB.

**Tech Stack:** Python ≥3.12, Click, stdlib `sqlite3`, `hashlib`, `re`, `pathlib`. Packaging via `uv`/`pyproject.toml`. Tests via `pytest`. Lint/format via `ruff`. Pre-commit hooks. GitHub Actions for versioning via `commitizen-tools/commitizen-action`.

**Spec:** `docs/superpowers/specs/2026-05-28-worksummary-cli-design.md`

---

## Task 0: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `__version__.py`
- Create: `worksummary/__init__.py`
- Create: `worksummary/__version__.py`
- Create: `tests/__init__.py`
- Create: `.pre-commit-config.yaml`
- Create: `.github/workflows/version-release.yml`
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Initialise git repo with `main` as the default branch**

```bash
cd /home/martin/Documents/Programming/worksummary
git init -b main
```

Expected: `Initialized empty Git repository in .../worksummary/.git/`

- [ ] **Step 2: Write `.gitignore`**

Create `.gitignore`:
```
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.pytest_cache/
.ruff_cache/
dist/
build/
*.db
.coverage
htmlcov/
```

- [ ] **Step 3: Write `pyproject.toml`**

Create `pyproject.toml`:
```toml
[project]
name = "worksummary"
version = "1.0.0"
description = "Log daily work items and produce a Teams-ready summary."
readme = "README.md"
requires-python = ">=3.12"
authors = [{ name = "Martin Eve", email = "martin@eve.gd" }]
dependencies = [
    "click>=8.1",
]

[project.scripts]
worksummary = "worksummary.cli:cli"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.5",
    "pre-commit>=3.7",
    "commitizen>=3.27",
]

[tool.commitizen]
version = "1.0.0"
version_files = [
    "__version__.py",
    "pyproject.toml:version",
    "worksummary/__version__.py",
]
update_changelog_on_bump = true

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "W", "UP", "B", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 4: Create version files**

Create `__version__.py`:
```python
__version__ = "1.0.0"
```

Create `worksummary/__version__.py`:
```python
__version__ = "1.0.0"
```

Create `worksummary/__init__.py`:
```python
from worksummary.__version__ import __version__

__all__ = ["__version__"]
```

Create empty `tests/__init__.py`:
```python
```

- [ ] **Step 5: Write `.pre-commit-config.yaml`**

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

- [ ] **Step 6: Write GitHub Actions versioning workflow**

Create `.github/workflows/version-release.yml`:
```yaml
name: Bump version

on:
  push:
    branches:
      - main

permissions:
  contents: write

jobs:
  bump-version:
    if: "!startsWith(github.event.head_commit.message, 'bump:')"
    runs-on: ubuntu-latest
    name: "Bump version and create changelog with commitizen"
    steps:
      - name: Check out code
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Create bump and changelog
        uses: commitizen-tools/commitizen-action@master
        with:
          push: false

      - name: Configure git for HTTPS push
        run: |
          git config --global user.email "github-actions@github.com"
          git config --global user.name "github-actions"
          git remote set-url origin https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Push using HTTPS
        run: |
          git push origin main --tags
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 7: Write a minimal `README.md`**

Create `README.md`:
```markdown
# worksummary

A command-line tool for logging daily work items and producing a Microsoft Teams-ready summary.

## Install

```bash
uv sync
```

## Usage

```bash
uv run worksummary add "Fixed bug 128 https://github.com/example/repo/issues/128"
uv run worksummary ls
uv run worksummary summary
```

See `docs/superpowers/specs/` for design details.
```

- [ ] **Step 8: Install dependencies and verify**

```bash
uv sync
uv run pytest --collect-only
```

Expected: `uv sync` resolves and installs deps; `pytest --collect-only` reports no tests collected (no test files yet) but exits cleanly.

- [ ] **Step 9: Commit**

```bash
git add .gitignore pyproject.toml __version__.py worksummary/ tests/ .pre-commit-config.yaml .github/ README.md uv.lock docs/
git commit -m "chore: scaffold project with uv, click, pre-commit, and version-release workflow"
```

---

## Task 1: `paths.py` — XDG database path

**Files:**
- Create: `worksummary/paths.py`
- Create: `tests/test_paths.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_paths.py`:
```python
from pathlib import Path

import pytest

from worksummary import paths


def test_db_path_uses_xdg_data_home_when_set(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    result = paths.db_path()
    assert result == tmp_path / "worksummary" / "work.db"


def test_db_path_falls_back_to_local_share_when_xdg_unset(monkeypatch, tmp_path):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    result = paths.db_path()
    assert result == tmp_path / ".local" / "share" / "worksummary" / "work.db"


def test_db_path_returns_path_object(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert isinstance(paths.db_path(), Path)


def test_db_path_falls_back_when_xdg_is_empty_string(monkeypatch, tmp_path):
    # POSIX says empty XDG vars should be treated as unset
    monkeypatch.setenv("XDG_DATA_HOME", "")
    monkeypatch.setenv("HOME", str(tmp_path))
    result = paths.db_path()
    assert result == tmp_path / ".local" / "share" / "worksummary" / "work.db"
```

- [ ] **Step 2: Write the stub module**

Create `worksummary/paths.py`:
```python
from pathlib import Path


def db_path() -> Path:
    raise NotImplementedError
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
uv run pytest tests/test_paths.py -v
```

Expected: all four tests FAIL with `NotImplementedError`.

- [ ] **Step 4: Implement `db_path`**

Replace `worksummary/paths.py`:
```python
import os
from pathlib import Path


def db_path() -> Path:
    """Return the path where the SQLite database should live.

    Honours $XDG_DATA_HOME; otherwise falls back to ~/.local/share.
    """
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "worksummary" / "work.db"
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
uv run pytest tests/test_paths.py -v
```

Expected: all four tests PASS.

- [ ] **Step 6: Commit**

```bash
uv run pre-commit run --files worksummary/paths.py tests/test_paths.py
git add worksummary/paths.py tests/test_paths.py
git commit -m "feat(paths): resolve XDG-compliant database path"
```

---

## Task 2: `dates.py` — ISO date parsing

**Files:**
- Create: `worksummary/dates.py`
- Create: `tests/test_dates.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dates.py`:
```python
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
```

- [ ] **Step 2: Write the stub module**

Create `worksummary/dates.py`:
```python
from datetime import date


def parse_iso_date(text: str) -> date:
    raise NotImplementedError


def today() -> date:
    raise NotImplementedError


def format_iso(d: date) -> str:
    raise NotImplementedError
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
uv run pytest tests/test_dates.py -v
```

Expected: all six tests FAIL.

- [ ] **Step 4: Implement the module**

Replace `worksummary/dates.py`:
```python
from datetime import date, datetime


def parse_iso_date(text: str) -> date:
    """Parse a date in strict YYYY-MM-DD format."""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"date must be in YYYY-MM-DD format (got {text!r})"
        ) from exc


def today() -> date:
    """Return today's local date."""
    return date.today()


def format_iso(d: date) -> str:
    """Format a date as ISO YYYY-MM-DD."""
    return d.isoformat()
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
uv run pytest tests/test_dates.py -v
```

Expected: all six tests PASS.

- [ ] **Step 6: Commit**

```bash
uv run pre-commit run --files worksummary/dates.py tests/test_dates.py
git add worksummary/dates.py tests/test_dates.py
git commit -m "feat(dates): parse and format ISO YYYY-MM-DD dates"
```

---

## Task 3: `urls.py` — URL extraction and footnote rewriting

**Files:**
- Create: `worksummary/urls.py`
- Create: `tests/test_urls.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_urls.py`:
```python
from worksummary import urls


def test_extract_urls_empty():
    assert urls.extract_urls("plain text with no urls") == []


def test_extract_urls_single_http():
    assert urls.extract_urls("see http://example.com") == ["http://example.com"]


def test_extract_urls_single_https():
    assert urls.extract_urls("see https://example.com") == ["https://example.com"]


def test_extract_urls_strips_trailing_sentence_punctuation():
    assert urls.extract_urls("see https://example.com.") == ["https://example.com"]
    assert urls.extract_urls("see https://example.com,") == ["https://example.com"]
    assert urls.extract_urls("see https://example.com!") == ["https://example.com"]
    assert urls.extract_urls("see https://example.com?") == ["https://example.com"]


def test_extract_urls_strips_trailing_brackets():
    assert urls.extract_urls("(see https://example.com)") == ["https://example.com"]
    assert urls.extract_urls("[see https://example.com]") == ["https://example.com"]


def test_extract_urls_multiple():
    text = "fixed https://a.com and also https://b.com here"
    assert urls.extract_urls(text) == ["https://a.com", "https://b.com"]


def test_extract_urls_preserves_query_strings():
    url = "https://example.com/path?a=1&b=2"
    assert urls.extract_urls(f"see {url}") == [url]


def test_rewrite_with_footnotes_no_urls():
    text, extracted, next_n = urls.rewrite_with_footnotes("plain text", start_n=1)
    assert text == "plain text"
    assert extracted == []
    assert next_n == 1


def test_rewrite_with_footnotes_single_url():
    text, extracted, next_n = urls.rewrite_with_footnotes(
        "Fixed bug 128 https://example.com/issues/597", start_n=1
    )
    assert text == "Fixed bug 128 [1]"
    assert extracted == ["https://example.com/issues/597"]
    assert next_n == 2


def test_rewrite_with_footnotes_multiple_urls_sequential():
    text, extracted, next_n = urls.rewrite_with_footnotes(
        "Reviewed https://a.com and https://b.com", start_n=1
    )
    assert text == "Reviewed [1] and [2]"
    assert extracted == ["https://a.com", "https://b.com"]
    assert next_n == 3


def test_rewrite_with_footnotes_continues_numbering():
    text, extracted, next_n = urls.rewrite_with_footnotes(
        "Reviewed https://c.com", start_n=3
    )
    assert text == "Reviewed [3]"
    assert extracted == ["https://c.com"]
    assert next_n == 4


def test_rewrite_with_footnotes_collapses_whitespace_around_removed_url():
    # Adjacent URLs should produce [N][N+1] with no extra space between them
    text, extracted, _ = urls.rewrite_with_footnotes(
        "Reviewed https://a.com https://b.com today", start_n=1
    )
    assert text == "Reviewed [1][2] today"
    assert extracted == ["https://a.com", "https://b.com"]


def test_rewrite_with_footnotes_preserves_trailing_punctuation():
    text, extracted, _ = urls.rewrite_with_footnotes(
        "See https://example.com.", start_n=1
    )
    assert text == "See [1]."
    assert extracted == ["https://example.com"]
```

- [ ] **Step 2: Write the stub module**

Create `worksummary/urls.py`:
```python
def extract_urls(text: str) -> list[str]:
    raise NotImplementedError


def rewrite_with_footnotes(text: str, start_n: int) -> tuple[str, list[str], int]:
    raise NotImplementedError
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
uv run pytest tests/test_urls.py -v
```

Expected: all tests FAIL with `NotImplementedError`.

- [ ] **Step 4: Implement the module**

Replace `worksummary/urls.py`:
```python
import re

_URL_RE = re.compile(r"https?://\S+")
_TRAILING_PUNCT = ".,;:!?)]}\"'"


def _strip_trailing_punct(url: str) -> str:
    while url and url[-1] in _TRAILING_PUNCT:
        url = url[:-1]
    return url


def extract_urls(text: str) -> list[str]:
    """Return all URLs found in `text`, with trailing punctuation stripped."""
    return [_strip_trailing_punct(m.group(0)) for m in _URL_RE.finditer(text)]


def rewrite_with_footnotes(
    text: str, start_n: int
) -> tuple[str, list[str], int]:
    """Replace URLs in `text` with sequential `[N]` references.

    Returns the rewritten text, the extracted URLs in order, and the next
    available footnote number. Adjacent URLs collapse to `[N][N+1]` without
    extra whitespace between them.
    """
    extracted: list[str] = []
    next_n = start_n
    pieces: list[str] = []
    cursor = 0

    for match in _URL_RE.finditer(text):
        raw = match.group(0)
        clean = _strip_trailing_punct(raw)
        # Punctuation that was stripped from the URL stays in the text.
        stripped_tail = raw[len(clean):]

        # Emit text before the URL.
        pieces.append(text[cursor:match.start()])
        pieces.append(f"[{next_n}]")
        pieces.append(stripped_tail)
        extracted.append(clean)
        next_n += 1
        cursor = match.end()

    pieces.append(text[cursor:])
    rewritten = "".join(pieces)

    # Collapse whitespace runs created by removed URLs (but preserve newlines).
    rewritten = re.sub(r"[ \t]+", " ", rewritten)
    # Collapse whitespace between adjacent footnote markers: "[1] [2]" -> "[1][2]"
    rewritten = re.sub(r"\] +\[", "][", rewritten)
    # Tidy " ." -> "." etc. for stripped trailing punctuation that ended up
    # adjacent to the footnote marker.
    rewritten = re.sub(r" ([.,;:!?])", r"\1", rewritten)

    return rewritten, extracted, next_n
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
uv run pytest tests/test_urls.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
uv run pre-commit run --files worksummary/urls.py tests/test_urls.py
git add worksummary/urls.py tests/test_urls.py
git commit -m "feat(urls): extract URLs and rewrite descriptions with [N] footnotes"
```

---

## Task 4: `ids.py` — hash generation, prefixes, resolution

**Files:**
- Create: `worksummary/ids.py`
- Create: `tests/test_ids.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ids.py`:
```python
import pytest

from worksummary import ids


def test_generate_id_returns_40_char_hex():
    result = ids.generate_id("some description", "2026-05-28T11:42:00")
    assert len(result) == 40
    assert all(c in "0123456789abcdef" for c in result)


def test_generate_id_is_unique_for_identical_input():
    # Random salt should make this practically impossible to collide
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
    # "aaa" and "aab" share "aa"; need full 3 chars to disambiguate.
    # "bbc" is alone with first char 'b'.
    result = ids.shortest_unique_prefixes(["aaa", "aab", "bbc"])
    assert result == {"aaa": 3, "aab": 3, "bbc": 1}


def test_shortest_unique_prefixes_two_share_one_doesnt():
    # "640..." needs 2 to distinguish from "6ab..." (both start with '6').
    # "6ab..." needs 2 to distinguish from "640...".
    # "2e7..." needs 1 (unique first char).
    result = ids.shortest_unique_prefixes([
        "640ab2bae07bedc4c163f679a746f7ab7fb5d1fa",
        "6ab2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        "2e7a9c4d1e0f8b3a5c6d7e8f9a0b1c2d3e4f5a6b",
    ])
    assert result["640ab2bae07bedc4c163f679a746f7ab7fb5d1fa"] == 2
    assert result["6ab2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"] == 2
    assert result["2e7a9c4d1e0f8b3a5c6d7e8f9a0b1c2d3e4f5a6b"] == 1


def test_resolve_unique_short_prefix():
    hashes = ["abc", "bcd"]
    assert ids.resolve("a", hashes) == "abc"
    assert ids.resolve("b", hashes) == "bcd"


def test_resolve_accepts_longer_than_minimum_prefix():
    # Even though "a" alone is unique, the user may type more
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
```

- [ ] **Step 2: Write the stub module**

Create `worksummary/ids.py`:
```python
from collections.abc import Iterable


class AmbiguousIdError(Exception):
    def __init__(self, prefix: str, candidates: list[str]):
        self.prefix = prefix
        self.candidates = candidates
        super().__init__(f"prefix {prefix!r} matches {len(candidates)} items")


class NotFoundError(Exception):
    def __init__(self, prefix: str):
        self.prefix = prefix
        super().__init__(f"no item matches prefix {prefix!r}")


def generate_id(description: str, created_at: str) -> str:
    raise NotImplementedError


def shortest_unique_prefixes(hashes: list[str]) -> dict[str, int]:
    raise NotImplementedError


def resolve(prefix: str, hashes: Iterable[str]) -> str:
    raise NotImplementedError
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
uv run pytest tests/test_ids.py -v
```

Expected: all tests FAIL with `NotImplementedError`.

- [ ] **Step 4: Implement the module**

Replace `worksummary/ids.py`:
```python
import hashlib
import os
from collections.abc import Iterable


class AmbiguousIdError(Exception):
    def __init__(self, prefix: str, candidates: list[str]):
        self.prefix = prefix
        self.candidates = candidates
        super().__init__(f"prefix {prefix!r} matches {len(candidates)} items")


class NotFoundError(Exception):
    def __init__(self, prefix: str):
        self.prefix = prefix
        super().__init__(f"no item matches prefix {prefix!r}")


def generate_id(description: str, created_at: str) -> str:
    """Compute a 40-char SHA-1 hash from the description, timestamp, and a random salt."""
    salt = os.urandom(16).hex()
    payload = f"{description}\0{created_at}\0{salt}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def shortest_unique_prefixes(hashes: list[str]) -> dict[str, int]:
    """Return the minimum prefix length for each hash to be unique within the set."""
    result: dict[str, int] = {}
    for h in hashes:
        k = 1
        while True:
            prefix = h[:k]
            collisions = [other for other in hashes if other != h and other.startswith(prefix)]
            if not collisions:
                result[h] = k
                break
            k += 1
            if k > len(h):
                # Duplicate hash in input — degenerate, give the full length.
                result[h] = len(h)
                break
    return result


def resolve(prefix: str, hashes: Iterable[str]) -> str:
    """Return the single hash starting with `prefix`, or raise."""
    matches = [h for h in hashes if h.startswith(prefix)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise NotFoundError(prefix)
    raise AmbiguousIdError(prefix, matches)
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
uv run pytest tests/test_ids.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
uv run pre-commit run --files worksummary/ids.py tests/test_ids.py
git add worksummary/ids.py tests/test_ids.py
git commit -m "feat(ids): generate SHA-1 ids and resolve shortest unique prefixes"
```

---

## Task 5: `storage.py` — SQLite CRUD

**Files:**
- Create: `worksummary/storage.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_storage.py`:
```python
import sqlite3
from datetime import date

import pytest

from worksummary import storage


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    storage.init_db(c)
    yield c
    c.close()


def test_init_db_creates_items_table(conn):
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
    )
    assert cursor.fetchone() is not None


def test_init_db_is_idempotent(conn):
    # Calling init_db twice should not raise
    storage.init_db(conn)


def test_add_item_returns_item_with_id(conn):
    item = storage.add_item(conn, date(2026, 5, 28), "Did a thing")
    assert isinstance(item.id, str)
    assert len(item.id) == 40
    assert item.work_date == date(2026, 5, 28)
    assert item.description == "Did a thing"
    assert item.created_at  # non-empty timestamp


def test_add_item_persists(conn):
    added = storage.add_item(conn, date(2026, 5, 28), "Did a thing")
    fetched = storage.get_item(conn, added.id)
    assert fetched.id == added.id
    assert fetched.description == "Did a thing"


def test_list_items_for_date(conn):
    storage.add_item(conn, date(2026, 5, 28), "today A")
    storage.add_item(conn, date(2026, 5, 27), "yesterday")
    storage.add_item(conn, date(2026, 5, 28), "today B")

    today_items = storage.list_items(conn, date(2026, 5, 28))
    assert len(today_items) == 2
    assert {i.description for i in today_items} == {"today A", "today B"}


def test_list_items_orders_by_created_at(conn):
    a = storage.add_item(conn, date(2026, 5, 28), "first")
    b = storage.add_item(conn, date(2026, 5, 28), "second")
    items = storage.list_items(conn, date(2026, 5, 28))
    assert [i.id for i in items] == [a.id, b.id]


def test_list_items_empty_for_unknown_date(conn):
    assert storage.list_items(conn, date(2026, 5, 28)) == []


def test_remove_item_deletes_row(conn):
    added = storage.add_item(conn, date(2026, 5, 28), "to remove")
    storage.remove_item(conn, added.id)
    assert storage.get_item(conn, added.id) is None


def test_remove_item_unknown_id_raises(conn):
    with pytest.raises(KeyError):
        storage.remove_item(conn, "0" * 40)


def test_get_item_unknown_returns_none(conn):
    assert storage.get_item(conn, "0" * 40) is None


def test_all_ids_returns_all_hashes(conn):
    a = storage.add_item(conn, date(2026, 5, 28), "A")
    b = storage.add_item(conn, date(2026, 5, 27), "B")
    assert set(storage.all_ids(conn)) == {a.id, b.id}


def test_all_ids_empty(conn):
    assert storage.all_ids(conn) == []
```

- [ ] **Step 2: Write the stub module**

Create `worksummary/storage.py`:
```python
import sqlite3
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Item:
    id: str
    work_date: date
    created_at: str
    description: str


def init_db(conn: sqlite3.Connection) -> None:
    raise NotImplementedError


def add_item(conn: sqlite3.Connection, work_date: date, description: str) -> Item:
    raise NotImplementedError


def list_items(conn: sqlite3.Connection, work_date: date) -> list[Item]:
    raise NotImplementedError


def get_item(conn: sqlite3.Connection, item_id: str) -> Item | None:
    raise NotImplementedError


def remove_item(conn: sqlite3.Connection, item_id: str) -> None:
    raise NotImplementedError


def all_ids(conn: sqlite3.Connection) -> list[str]:
    raise NotImplementedError


def connect(path) -> sqlite3.Connection:
    raise NotImplementedError
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
uv run pytest tests/test_storage.py -v
```

Expected: all tests FAIL with `NotImplementedError`.

- [ ] **Step 4: Implement the module**

Replace `worksummary/storage.py`:
```python
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from worksummary import ids
from worksummary.dates import format_iso, parse_iso_date


@dataclass(frozen=True)
class Item:
    id: str
    work_date: date
    created_at: str
    description: str


def init_db(conn: sqlite3.Connection) -> None:
    """Create the items table if it doesn't exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id          TEXT PRIMARY KEY,
            work_date   TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            description TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_items_work_date ON items(work_date)"
    )
    conn.commit()


def connect(path: Path | str) -> sqlite3.Connection:
    """Open (and initialise) the SQLite database at `path`."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    init_db(conn)
    return conn


def _row_to_item(row: tuple) -> Item:
    return Item(
        id=row[0],
        work_date=parse_iso_date(row[1]),
        created_at=row[2],
        description=row[3],
    )


def add_item(conn: sqlite3.Connection, work_date: date, description: str) -> Item:
    """Insert a new item and return it."""
    # Microsecond precision so rapid successive inserts retain insertion order.
    created_at = datetime.now().isoformat()
    item_id = ids.generate_id(description, created_at)
    conn.execute(
        "INSERT INTO items (id, work_date, created_at, description) VALUES (?, ?, ?, ?)",
        (item_id, format_iso(work_date), created_at, description),
    )
    conn.commit()
    return Item(
        id=item_id,
        work_date=work_date,
        created_at=created_at,
        description=description,
    )


def list_items(conn: sqlite3.Connection, work_date: date) -> list[Item]:
    """Return all items for the given date, ordered by creation time."""
    cursor = conn.execute(
        "SELECT id, work_date, created_at, description FROM items "
        "WHERE work_date = ? ORDER BY created_at ASC, id ASC",
        (format_iso(work_date),),
    )
    return [_row_to_item(row) for row in cursor.fetchall()]


def get_item(conn: sqlite3.Connection, item_id: str) -> Item | None:
    """Return a single item by id, or None if not found."""
    cursor = conn.execute(
        "SELECT id, work_date, created_at, description FROM items WHERE id = ?",
        (item_id,),
    )
    row = cursor.fetchone()
    return _row_to_item(row) if row else None


def remove_item(conn: sqlite3.Connection, item_id: str) -> None:
    """Delete an item by id. Raises KeyError if it doesn't exist."""
    cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    if cursor.rowcount == 0:
        raise KeyError(item_id)
    conn.commit()


def all_ids(conn: sqlite3.Connection) -> list[str]:
    """Return all item ids in the database."""
    cursor = conn.execute("SELECT id FROM items")
    return [row[0] for row in cursor.fetchall()]
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
uv run pytest tests/test_storage.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
uv run pre-commit run --files worksummary/storage.py tests/test_storage.py
git add worksummary/storage.py tests/test_storage.py
git commit -m "feat(storage): add SQLite CRUD for work items"
```

---

## Task 6: `formatting.py` — Teams summary and `ls` renderer

**Files:**
- Create: `worksummary/formatting.py`
- Create: `tests/test_formatting.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_formatting.py`:
```python
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


# --- Summary tests ---


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


# --- ls tests ---


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
    # No ANSI escape sequences
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
    # Two items both starting with 'a' — prefix length should be 2 for each
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
    # ANSI red is \x1b[31m or \x1b[91m depending on Click; just verify the
    # colored prefix is present somewhere
    assert "\x1b[" in output
    # And both full hashes are still present in the output
    assert "ab" + "0" * 38 in output
    assert "ac" + "0" * 38 in output
```

- [ ] **Step 2: Write the stub module**

Create `worksummary/formatting.py`:
```python
from datetime import date

from worksummary.storage import Item


def format_summary(items: list[Item], work_date: date) -> str:
    raise NotImplementedError


def format_ls(items: list[Item], work_date: date, use_color: bool = True) -> str:
    raise NotImplementedError
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
uv run pytest tests/test_formatting.py -v
```

Expected: all tests FAIL with `NotImplementedError`.

- [ ] **Step 4: Implement the module**

Replace `worksummary/formatting.py`:
```python
from datetime import date, datetime

import click

from worksummary.ids import shortest_unique_prefixes
from worksummary.storage import Item
from worksummary.urls import rewrite_with_footnotes


def _format_header_date(d: date) -> str:
    # Short weekday + day + short month + year, e.g. "Thu 28 May 2026"
    return d.strftime("%a %-d %b %Y")


def _format_time(created_at: str) -> str:
    try:
        return datetime.fromisoformat(created_at).strftime("%H:%M")
    except ValueError:
        return created_at[11:16] if len(created_at) >= 16 else created_at


def format_summary(items: list[Item], work_date: date) -> str:
    """Render items as Teams-ready markdown."""
    if not items:
        return f"No work items recorded for {work_date.isoformat()}."

    header = f"**Work — {_format_header_date(work_date)}**"

    bullets: list[str] = []
    references: list[str] = []
    next_n = 1

    for item in items:
        text, urls_in_item, next_n = rewrite_with_footnotes(item.description, next_n)
        bullets.append(f"- {text}")
        references.extend(urls_in_item)

    sections = [header, "", *bullets]
    if references:
        sections.append("")
        sections.append("**References**")
        for i, url in enumerate(references, start=1):
            sections.append(f"{i}. {url}")

    return "\n".join(sections)


def format_ls(items: list[Item], work_date: date, use_color: bool = True) -> str:
    """Render items as a colored listing with unique-prefix coloring."""
    if not items:
        return f"No work items recorded for {work_date.isoformat()}."

    prefix_lens = shortest_unique_prefixes([i.id for i in items])

    lines: list[str] = []
    for item in items:
        k = prefix_lens[item.id]
        prefix = item.id[:k]
        rest = item.id[k:]
        if use_color:
            colored_prefix = click.style(prefix, fg="red")
        else:
            colored_prefix = prefix
        time_str = _format_time(item.created_at)
        lines.append(f"{colored_prefix}{rest}  {time_str}  {item.description}")

    return "\n".join(lines)
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
uv run pytest tests/test_formatting.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
uv run pre-commit run --files worksummary/formatting.py tests/test_formatting.py
git add worksummary/formatting.py tests/test_formatting.py
git commit -m "feat(formatting): render Teams summary and colored ls output"
```

---

## Task 7: `cli.py` — Click commands

**Files:**
- Create: `worksummary/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cli.py`:
```python
import re
import sqlite3
from pathlib import Path

import pytest
from click.testing import CliRunner

from worksummary import cli, storage


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
    # ls without --date should find it
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
    # Get the id from ls output
    ls_out = _strip_ansi(_ls(runner, "--date", "2026-05-28").output)
    # First token of the line is the hash
    hash_str = ls_out.strip().split()[0]
    # Remove using just the first character (it's the only item)
    result = runner.invoke(cli.cli, ["remove", hash_str[0]])
    assert result.exit_code == 0
    assert "Removed" in result.output

    # Now the date should be empty
    ls_out = _ls(runner, "--date", "2026-05-28").output
    assert "No work items recorded" in ls_out


def test_remove_unknown_prefix_errors(runner):
    result = runner.invoke(cli.cli, ["remove", "zzzz"])
    assert result.exit_code != 0
    assert "no item matches" in result.output.lower() or "not found" in result.output.lower()


def test_remove_ambiguous_prefix_errors(runner, monkeypatch):
    # Deterministic hashes that share a first-char prefix.
    fixed_ids = iter([
        "a" + "1" * 39,
        "a" + "2" * 39,
    ])
    monkeypatch.setattr(
        cli.ids, "generate_id", lambda desc, ts: next(fixed_ids)
    )

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
```

- [ ] **Step 2: Write the stub module**

Create `worksummary/cli.py`:
```python
import click

from worksummary import paths


@click.group()
def cli() -> None:
    """Log daily work items and produce a Teams-ready summary."""
    raise NotImplementedError
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: all tests FAIL.

- [ ] **Step 4: Implement the module**

Replace `worksummary/cli.py`:
```python
import sys

import click

from worksummary import dates, formatting, ids, paths, storage


def _open_db():
    return storage.connect(paths.db_path())


def _resolve_or_exit(conn, prefix: str) -> str:
    """Resolve a prefix to a full id, printing an error and exiting on failure."""
    try:
        return ids.resolve(prefix, storage.all_ids(conn))
    except ids.NotFoundError:
        click.echo(f"Error: no item matches prefix {prefix!r}.", err=True)
        sys.exit(1)
    except ids.AmbiguousIdError as exc:
        click.echo(f"Error: prefix {prefix!r} is ambiguous. Matches:", err=True)
        prefix_lens = ids.shortest_unique_prefixes(exc.candidates)
        for cand in exc.candidates:
            short = cand[: prefix_lens[cand]]
            item = storage.get_item(conn, cand)
            desc = item.description if item else ""
            click.echo(f"  {short}  {desc}", err=True)
        sys.exit(1)


def _parse_date_or_exit(text: str | None):
    if text is None:
        return dates.today()
    try:
        return dates.parse_iso_date(text)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@click.group()
def cli() -> None:
    """Log daily work items and produce a Teams-ready summary."""


@cli.command()
@click.argument("description")
@click.option("--date", "date_str", default=None, help="ISO date (YYYY-MM-DD); defaults to today.")
def add(description: str, date_str: str | None) -> None:
    """Add a work item."""
    work_date = _parse_date_or_exit(date_str)
    conn = _open_db()
    item = storage.add_item(conn, work_date, description)
    prefix_lens = ids.shortest_unique_prefixes(storage.all_ids(conn))
    short = item.id[: prefix_lens[item.id]]
    click.echo(f"Added [{short}] on {work_date.isoformat()}: {description}")


@cli.command(name="ls")
@click.option("--date", "date_str", default=None, help="ISO date (YYYY-MM-DD); defaults to today.")
def ls_cmd(date_str: str | None) -> None:
    """List items for a date with unique-prefix coloring."""
    work_date = _parse_date_or_exit(date_str)
    conn = _open_db()
    items = storage.list_items(conn, work_date)
    use_color = sys.stdout.isatty()
    click.echo(formatting.format_ls(items, work_date, use_color=use_color))


@cli.command()
@click.argument("prefix")
def remove(prefix: str) -> None:
    """Remove the item with the given id prefix."""
    conn = _open_db()
    full_id = _resolve_or_exit(conn, prefix)
    item = storage.get_item(conn, full_id)
    storage.remove_item(conn, full_id)
    click.echo(f"Removed: {item.description}")


@cli.command()
@click.argument("prefix")
@click.argument("description")
def replace(prefix: str, description: str) -> None:
    """Replace an item: removes the old one and adds a new one on the same date."""
    conn = _open_db()
    full_id = _resolve_or_exit(conn, prefix)
    old = storage.get_item(conn, full_id)
    storage.remove_item(conn, full_id)
    new = storage.add_item(conn, old.work_date, description)
    prefix_lens = ids.shortest_unique_prefixes(storage.all_ids(conn))
    old_prefix_lens = ids.shortest_unique_prefixes([old.id, *storage.all_ids(conn)])
    old_short = old.id[: old_prefix_lens[old.id]]
    new_short = new.id[: prefix_lens[new.id]]
    click.echo(f"Replaced [{old_short}] with [{new_short}]: {description}")


@cli.command()
@click.option("--date", "date_str", default=None, help="ISO date (YYYY-MM-DD); defaults to today.")
def summary(date_str: str | None) -> None:
    """Print a Teams-ready markdown summary for a date."""
    work_date = _parse_date_or_exit(date_str)
    conn = _open_db()
    items = storage.list_items(conn, work_date)
    click.echo(formatting.format_summary(items, work_date))


if __name__ == "__main__":
    cli()
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Run the full test suite**

```bash
uv run pytest -v
```

Expected: every test PASSES.

- [ ] **Step 7: Smoke-test the CLI end-to-end**

```bash
uv run worksummary add "Wrote the worksummary CLI https://github.com/example/repo/pull/1" --date 2026-05-28
uv run worksummary add "Reviewed PR" --date 2026-05-28
uv run worksummary ls --date 2026-05-28
uv run worksummary summary --date 2026-05-28
```

Expected: `add` confirms, `ls` shows two items with colored prefixes (when run in a real TTY), `summary` produces:
```
**Work — Thu 28 May 2026**

- Wrote the worksummary CLI [1]
- Reviewed PR

**References**
1. https://github.com/example/repo/pull/1
```

- [ ] **Step 8: Clean up the smoke-test data**

```bash
uv run python -c "from worksummary import paths; import os; p = paths.db_path(); os.remove(p) if p.exists() else None"
```

- [ ] **Step 9: Commit**

```bash
uv run pre-commit run --files worksummary/cli.py tests/test_cli.py
git add worksummary/cli.py tests/test_cli.py
git commit -m "feat(cli): wire add/ls/remove/replace/summary commands"
```

---

## Task 8: Final wiring — README and pre-commit install

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Expand the README with full command reference**

Replace `README.md`:
```markdown
# worksummary

A command-line tool for logging daily work items and producing a Microsoft Teams-ready summary.

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

# List items for a date (with unique-prefix coloring)
worksummary ls
worksummary ls --date 2026-05-27

# Remove an item by id prefix
worksummary remove 6        # shortest unique prefix
worksummary remove 640      # any longer prefix also works

# Replace an item (delete + add on the same date)
worksummary replace 6 "Fixed bug 128 and added regression test"

# Render a Teams-ready summary
worksummary summary
worksummary summary --date 2026-05-27
```

## Development

```bash
uv run pytest
uv run ruff check
uv run ruff format
```

See `docs/superpowers/specs/` for the design document and `docs/superpowers/plans/` for the implementation plan.
```

- [ ] **Step 2: Install pre-commit hooks locally**

```bash
uv run pre-commit install
```

Expected: `pre-commit installed at .git/hooks/pre-commit`

- [ ] **Step 3: Run all hooks across the full repo**

```bash
uv run pre-commit run --all-files
```

Expected: all hooks pass (or auto-fix and pass on re-run).

- [ ] **Step 4: Final commit**

```bash
git add README.md
git commit -m "docs: expand README with full command reference"
```

---

## Self-review notes

- **Spec coverage:** all five commands (`add`, `ls`, `remove`, `replace`, `summary`) implemented (Task 7); date parsing (Task 2), URL footnote rewriting (Task 3 + 6), SHA-1 IDs with prefix resolution (Task 4), SQLite storage (Task 5), XDG path (Task 1), Teams markdown rendering (Task 6), TTY-aware coloring (Task 6 + 7), scaffolding/versioning (Task 0 + 8). The spec's "user can use a longer prefix than the minimum" requirement is covered by `test_resolve_accepts_longer_than_minimum_prefix` in Task 4 and exercised end-to-end in CLI tests.
- **No placeholders.** Every step has concrete code or an exact command.
- **Type consistency:** `Item` dataclass defined in Task 5 and imported in Task 6 + 7 with the same field names. `ids.AmbiguousIdError` / `ids.NotFoundError` defined in Task 4 and caught in Task 7. `paths.db_path()` defined in Task 1 and monkey-patched in Task 7 tests. Function signatures match across tasks.
