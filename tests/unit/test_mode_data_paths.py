"""Unit tests for mode-specific default data file paths."""

from pathlib import Path

from src.config import Config
from src.storage import Storage


def test_storage_default_db_path_is_prod_when_env_unset(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("TICK_TOCK_ENV", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert Storage.default_db_path() == tmp_path / "TickTock" / "tick_tock.db"


def test_storage_default_db_path_uses_dev_suffix(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TICK_TOCK_ENV", "dev")
    monkeypatch.setattr("src.storage.repo_data_dir", lambda: tmp_path)

    assert Storage.default_db_path() == tmp_path / "tick_tock.dev.db"


def test_storage_default_backup_path_uses_mode_specific_db(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("TICK_TOCK_ENV", "prototype")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert Path(str(Storage.default_db_path()) + ".bak") == (
        tmp_path / "TickTock" / "tick_tock.prototype.db.bak"
    )


def test_config_default_path_uses_mode_specific_name(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TICK_TOCK_ENV", "test")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    cfg = Config()
    assert cfg._config_path == tmp_path / "TickTock" / "config.test.json"


def test_invalid_mode_falls_back_to_prod_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TICK_TOCK_ENV", "not-real")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    cfg = Config()
    assert Storage.default_db_path() == tmp_path / "TickTock" / "tick_tock.db"
    assert cfg._config_path == tmp_path / "TickTock" / "config.json"
