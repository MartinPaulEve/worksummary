from pathlib import Path

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
    monkeypatch.setenv("XDG_DATA_HOME", "")
    monkeypatch.setenv("HOME", str(tmp_path))
    result = paths.db_path()
    assert result == tmp_path / ".local" / "share" / "worksummary" / "work.db"
