from datetime import date, datetime

import click

from worksummary.ids import shortest_unique_prefixes
from worksummary.storage import Item
from worksummary.urls import rewrite_with_footnotes

# Teams renders markdown bold (**...**) only when you TYPE it, not when you
# paste it. To get bold text via paste we translate ASCII letters and digits
# into the Unicode Mathematical Bold block (U+1D400+) — these are real
# characters that render bold everywhere with no markdown needed.
_BOLD_MAP: dict[int, int] = {}
for _i, _c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    _BOLD_MAP[ord(_c)] = 0x1D400 + _i
for _i, _c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    _BOLD_MAP[ord(_c)] = 0x1D41A + _i
for _i, _c in enumerate("0123456789"):
    _BOLD_MAP[ord(_c)] = 0x1D7CE + _i


def _bold(text: str) -> str:
    """Return `text` with ASCII letters/digits converted to Unicode bold."""
    return text.translate(_BOLD_MAP)


def _format_header_date(d: date) -> str:
    return d.strftime("%a %-d %b %Y")


def _format_time(created_at: str) -> str:
    try:
        return datetime.fromisoformat(created_at).strftime("%H:%M")
    except ValueError:
        return created_at[11:16] if len(created_at) >= 16 else created_at


def format_summary(items: list[Item], work_date: date) -> str:
    """Render items as Teams-paste-friendly text using Unicode bold for headers."""
    if not items:
        return f"No work items recorded for {work_date.isoformat()}."

    header = _bold("Work") + " — " + _bold(_format_header_date(work_date))

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
        sections.append(_bold("References"))
        for i, url in enumerate(references, start=1):
            sections.append(f"{i}. {url}")

    return "\n".join(sections)


def format_ls(
    items: list[Item],
    work_date: date,
    all_hashes: list[str],
    use_color: bool = True,
) -> str:
    """Render items as a listing.

    The unique-prefix portion of each id is colored red and wrapped in
    literal `[brackets]`. Prefix uniqueness is computed against `all_hashes`
    (the full set of ids in the database), not just the visible items, so
    every prefix shown here is guaranteed to be accepted by `remove` and
    `replace` regardless of which date the user filtered by.
    """
    if not items:
        return f"No work items recorded for {work_date.isoformat()}."

    prefix_lens = shortest_unique_prefixes(all_hashes)

    lines: list[str] = []
    for item in items:
        k = prefix_lens[item.id]
        prefix = item.id[:k]
        rest = item.id[k:]
        colored_prefix = click.style(prefix, fg="red") if use_color else prefix
        date_str = item.work_date.isoformat()
        time_str = _format_time(item.created_at)
        lines.append(f"[{colored_prefix}]{rest}  {date_str} {time_str}  {item.description}")

    return "\n".join(lines)
