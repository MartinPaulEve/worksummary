from datetime import date, datetime

import click

from worksummary.ids import shortest_unique_prefixes
from worksummary.storage import Item
from worksummary.urls import rewrite_with_footnotes


def _format_header_date(d: date) -> str:
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
    """Render items as a listing with the unique-prefix portion of each id colored red."""
    if not items:
        return f"No work items recorded for {work_date.isoformat()}."

    prefix_lens = shortest_unique_prefixes([i.id for i in items])

    lines: list[str] = []
    for item in items:
        k = prefix_lens[item.id]
        prefix = item.id[:k]
        rest = item.id[k:]
        colored_prefix = click.style(prefix, fg="red") if use_color else prefix
        time_str = _format_time(item.created_at)
        lines.append(f"{colored_prefix}{rest}  {time_str}  {item.description}")

    return "\n".join(lines)
