import os
from pathlib import Path


def db_path() -> Path:
    """Return the path where the SQLite database should live.

    Honours $XDG_DATA_HOME; otherwise falls back to ~/.local/share.
    """
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "worksummary" / "work.db"
