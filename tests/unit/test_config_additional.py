"""Additional unit tests for Config edge branches."""

import json
import logging

import pytest

from src.config import Config, ConfigError


def test_get_theme_setting_returns_default_when_theme_section_not_dict(
    tmp_path,
) -> None:
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps({"theme": "bad"}), encoding="utf-8")
    cfg = Config(config_path=path)
    cfg._config["theme"] = "bad"  # force non-dict to hit fallback branch
    assert cfg.get_theme_setting("name", "fallback") == "fallback"


def test_get_timer_setting_returns_default_when_section_not_dict(tmp_path) -> None:
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps({"timer_settings": "bad"}), encoding="utf-8")
    cfg = Config(config_path=path)
    cfg._config["timer_settings"] = "bad"
    assert cfg.get_timer_setting("max_backup_files", 7) == 7


def test_set_timer_setting_creates_section_when_missing(tmp_path) -> None:
    cfg = Config(config_path=tmp_path / "cfg.json")
    cfg._config.pop("timer_settings", None)
    cfg.set_timer_setting("max_backup_files", 9)
    assert cfg.get_timer_setting("max_backup_files") == 9


def test_ensure_config_file_handles_config_error(tmp_path, monkeypatch) -> None:
    cfg = Config(config_path=tmp_path / "cfg.json")
    cfg._config_path.unlink(missing_ok=True)
    monkeypatch.setattr(cfg, "save", lambda: (_ for _ in ()).throw(ConfigError("boom")))
    cfg._ensure_config_file()  # should not raise


def test_load_sets_error_when_open_raises_oserror(tmp_path, monkeypatch) -> None:
    path = tmp_path / "cfg.json"
    path.write_text("{}", encoding="utf-8")
    cfg = Config(config_path=path)

    def raise_oserror(*_args, **_kwargs):
        raise OSError("denied")

    monkeypatch.setattr("builtins.open", raise_oserror)
    cfg.reload()
    assert cfg.load_error is not None


def test_coerce_float_and_int_reject_bool_and_unsupported_types() -> None:
    with pytest.raises(ValueError):
        Config._coerce_float(True)
    with pytest.raises(TypeError):
        Config._coerce_float(object())
    with pytest.raises(ValueError):
        Config._coerce_int(False)
    with pytest.raises(TypeError):
        Config._coerce_int(object())


def test_migrate_config_version_swallow_save_error(tmp_path, monkeypatch) -> None:
    cfg = Config(config_path=tmp_path / "cfg.json")
    cfg._file_config_version = "0.0.1"
    monkeypatch.setattr(cfg, "save", lambda: (_ for _ in ()).throw(ConfigError("x")))
    cfg._migrate_config_version()  # should not raise


def test_get_mtime_returns_none_on_oserror(tmp_path, monkeypatch) -> None:
    cfg = Config(config_path=tmp_path / "cfg.json")

    class _BadStatPath:
        def stat(self):
            raise OSError("no stat")

    monkeypatch.setattr(cfg, "_config_path", _BadStatPath())
    assert cfg._get_mtime() is None


def test_watch_loop_handles_callback_exception(tmp_path, caplog) -> None:
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps({"environment": "prod"}), encoding="utf-8")
    cfg = Config(config_path=path)

    def boom(_cfg):
        raise RuntimeError("callback failed")

    cfg.on_reload(boom)
    # Force the watcher to detect a "change" immediately on first poll.
    cfg._last_mtime = -1.0
    with caplog.at_level(logging.ERROR, logger="src.config"):
        cfg.start_watching(interval=0.05)
        import time

        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and not caplog.records:
            time.sleep(0.05)
        cfg.stop_watching()

    assert any("callback raised an exception" in r.message for r in caplog.records)
