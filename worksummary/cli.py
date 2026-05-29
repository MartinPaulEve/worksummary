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
@click.option(
    "--before",
    "before_prefix",
    default=None,
    help="Insert before the item with this id prefix. Takes the target's date.",
)
def add(description: str, date_str: str | None, before_prefix: str | None) -> None:
    """Add a work item."""
    if before_prefix and date_str:
        click.echo("Error: --before and --date are mutually exclusive.", err=True)
        sys.exit(1)

    conn = _open_db()

    if before_prefix:
        target_id = _resolve_or_exit(conn, before_prefix)
        item = storage.add_item_before(conn, target_id, description)
    else:
        work_date = _parse_date_or_exit(date_str)
        item = storage.add_item(conn, work_date, description)

    prefix_lens = ids.shortest_unique_prefixes(storage.all_ids(conn))
    short = item.id[: prefix_lens[item.id]]
    click.echo(f"Added [{short}] on {item.work_date.isoformat()}: {description}")


@cli.command(name="ls")
@click.option("--date", "date_str", default=None, help="ISO date (YYYY-MM-DD); defaults to today.")
def ls_cmd(date_str: str | None) -> None:
    """List items for a date with unique-prefix coloring."""
    work_date = _parse_date_or_exit(date_str)
    conn = _open_db()
    items = storage.list_items(conn, work_date)
    all_hashes = storage.all_ids(conn)
    use_color = sys.stdout.isatty()
    click.echo(formatting.format_ls(items, work_date, all_hashes, use_color=use_color))


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
    # Compute the display prefix the user would have seen for `old` BEFORE removal,
    # by including its id in the prefix calculation alongside the current set.
    old_prefix_lens = ids.shortest_unique_prefixes([old.id, *storage.all_ids(conn)])
    new_prefix_lens = ids.shortest_unique_prefixes(storage.all_ids(conn))
    old_short = old.id[: old_prefix_lens[old.id]]
    new_short = new.id[: new_prefix_lens[new.id]]
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
