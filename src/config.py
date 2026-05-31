"""Configuration management for Tick-Tock Widget."""

import copy
import json
import logging
import os
import threading
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any, Optional, cast

from src.config_sanitizer import (
    coerce_float as _cs_coerce_float,
    coerce_int as _cs_coerce_int,
    sanitize_loaded_config,
)
from src.paths import user_data_dir

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when a config save operation fails."""


class Environment(Enum):
    """Supported runtime modes used for path and behavior selection."""

    DEV = "dev"
    TEST = "test"
    PROD = "prod"
    PROTOTYPE = "prototype"


class Config:
    """Load and save application settings from a JSON file.

    Environment variable overrides (applied after loading the file):

    - ``TICK_TOCK_ENV``   — environment name: ``dev``, ``test``, ``prod``, ``prototype``
    - ``TICK_TOCK_DEBUG`` — enable debug mode: ``1``, ``true``, or ``yes``

    - Auto-creates the config file with defaults if it does not exist.
    - Atomic save (write to ``.tmp`` then rename) to avoid partial writes.
    - Bad JSON falls back to defaults; error stored in :attr:`load_error`.
    - :meth:`start_watching` polls for file changes and fires ``on_reload`` callbacks.
    """

    DEFAULT_CONFIG: dict[str, Any] = {
        "config_version": "0.1.0",
        "environment": "prod",
        "debug": False,
        "ui_preferences": {
            "window_x": None,
            "window_y": None,
            "always_on_top": True,
            "opacity": 0.90,
        },
        "theme": {
            "name": "matrix",
            "custom": {
                "bg": "#001100",
                "fg": "#00FF00",
                "accent": "#003300",
            },
        },
        "timer_settings": {
            "autosave_interval_minutes": 1,
            "time_rounding_minutes": 0,
            "date_format": "DD/MM/YYYY",
            "time_format": "24h",
            "max_backup_files": 5,
            "activity_history_retention_days": 3650,
        },
    }

    _ENV_VAR_MAP: dict[str, str] = {
        "TICK_TOCK_ENV": "environment",
        "TICK_TOCK_DEBUG": "debug",
    }

    _HOT_RELOAD_INTERVAL: float = 1.0  # seconds between mtime checks

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._config: dict[str, Any] = copy.deepcopy(self.DEFAULT_CONFIG)
        self._config_path = config_path or self._default_config_path()
        self._load_error: Optional[str] = None

        # Hot-reload state — must be set before save() is called.
        self._watch_thread: Optional[threading.Thread] = None
        self._watch_stop = threading.Event()
        self._reload_callbacks: list[Callable[["Config"], None]] = []
        self._last_mtime: Optional[float] = None

        _file_existed = self._config_path.exists()
        self._file_config_version: str = ""  # captured by _load() before merge
        self._load()  # deep-merge file over defaults
        self._sanitize()  # fix invalid values
        if _file_existed and not self._load_error:
            self._migrate_config_version()  # bump version if outdated, save
        self._apply_env_overrides()
        self._ensure_config_file()
        self._last_mtime = self._get_mtime()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return a config value by key, or *default* if not found."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value (in-memory only until :meth:`save` is called)."""
        self._config[key] = value

    def get_ui_pref(self, key: str, default: Any = None) -> Any:
        """Return a UI preference value, or *default* if not set."""
        prefs = self._config.get("ui_preferences", {})
        if isinstance(prefs, dict):
            return cast(dict[str, Any], prefs).get(key, default)
        return default

    def set_ui_pref(self, key: str, value: Any) -> None:
        """Set a UI preference value (in-memory only until :meth:`save` is called)."""
        if "ui_preferences" not in self._config or not isinstance(
            self._config["ui_preferences"], dict
        ):
            self._config["ui_preferences"] = {}
        self._config["ui_preferences"][key] = value

    def get_theme_setting(self, key: str, default: Any = None) -> Any:
        """Return a value from the ``theme`` section of the config."""
        theme_cfg = self._config.get("theme", {})
        if isinstance(theme_cfg, dict):
            return cast(dict[str, Any], theme_cfg).get(key, default)
        return default

    def set_theme_setting(self, key: str, value: Any) -> None:
        """Set a value in the ``theme`` section (in-memory only until :meth:`save`)."""
        if "theme" not in self._config or not isinstance(self._config["theme"], dict):
            self._config["theme"] = {}
        self._config["theme"][key] = value

    def get_timer_setting(self, key: str, default: Any = None) -> Any:
        """Return a value from the ``timer_settings`` section of the config."""
        ts = self._config.get("timer_settings", {})
        if isinstance(ts, dict):
            return cast(dict[str, Any], ts).get(key, default)
        return default

    def set_timer_setting(self, key: str, value: Any) -> None:
        """Set a value in the ``timer_settings`` section (in-memory only
        until :meth:`save`)."""
        if "timer_settings" not in self._config or not isinstance(
            self._config["timer_settings"], dict
        ):
            self._config["timer_settings"] = {}
        self._config["timer_settings"][key] = value

    def save(self) -> None:
        """Write config to disk. Uses a .tmp file + rename to avoid partial writes.

        Raises:
            ConfigError: if the file cannot be written.
        """
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._config_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
            tmp.replace(self._config_path)
        except OSError as exc:
            raise ConfigError(
                f"Failed to save config to {self._config_path}: {exc}"
            ) from exc
        self._last_mtime = self._get_mtime()

    def reload(self) -> None:
        """Re-read the config file. Env overrides are re-applied.

        Sets :attr:`load_error` on bad JSON.
        """
        self._config = copy.deepcopy(self.DEFAULT_CONFIG)
        self._load()
        self._sanitize()
        self._apply_env_overrides()
        self._last_mtime = self._get_mtime()

    def on_reload(self, callback: Callable[["Config"], None]) -> None:
        """Register *callback* to be invoked after each hot-reload."""
        self._reload_callbacks.append(callback)

    def start_watching(self, interval: float = _HOT_RELOAD_INTERVAL) -> None:
        """Start a background thread that polls the config file for mtime changes.

        Calls :meth:`reload` and fires :meth:`on_reload` callbacks on change.
        Calling again while already watching is a no-op.
        """
        if self._watch_thread and self._watch_thread.is_alive():
            return
        self._watch_stop.clear()
        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(interval,),
            daemon=True,
            name="config-hot-reload",
        )
        self._watch_thread.start()

    def stop_watching(self) -> None:
        """Stop the watcher thread."""
        self._watch_stop.set()
        if self._watch_thread:
            self._watch_thread.join(timeout=5.0)
            self._watch_thread = None

    @property
    def load_error(self) -> Optional[str]:
        """Error from the last load attempt, or ``None``."""
        return self._load_error

    # ------------------------------------------------------------------
    # Environment / mode helpers
    # ------------------------------------------------------------------

    @property
    def environment(self) -> Environment:
        """Return effective runtime environment enum value."""
        env_str = str(self._config.get("environment", "prod")).lower()
        try:
            return Environment(env_str)
        except ValueError:
            return Environment.PROD

    @property
    def debug(self) -> bool:
        """Return whether debug mode is enabled."""
        return bool(self._config.get("debug", False))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _default_config_path(self) -> Path:
        """Default config path, isolated by runtime mode.

        Filenames:
        - prod: ``config.json``
        - dev/test/prototype: ``config.<env>.json``

        This resolves under ``user_data_dir()``.
        """
        env = os.environ.get("TICK_TOCK_ENV", "prod").lower()
        if env not in {"dev", "test", "prototype", "prod"}:
            env = "prod"
        name = "config.json" if env == "prod" else f"config.{env}.json"
        return user_data_dir() / name

    def _ensure_config_file(self) -> None:
        """Create the config file with defaults if it does not exist."""
        if not self._config_path.exists():
            try:
                self.save()
            except ConfigError as exc:
                logger.warning("Could not auto-create config file: %s", exc)

    @staticmethod
    def _deep_merge(
        destination: dict[str, Any], source: dict[str, Any]
    ) -> dict[str, Any]:
        """Recursively merge *source* into *destination* (in-place, source wins).

        Nested dicts are merged key-by-key so that default sub-keys absent from
        *source* are preserved.  All other types are replaced wholesale.
        Returns *destination*.
        """
        for key, value in source.items():
            if (
                key in destination
                and isinstance(destination[key], dict)
                and isinstance(value, dict)
            ):
                Config._deep_merge(
                    cast(dict[str, Any], destination[key]), cast(dict[str, Any], value)
                )
            else:
                destination[key] = value
        return destination

    def _load(self) -> None:
        self._load_error = None
        if not self._config_path.exists():
            return
        try:
            with open(self._config_path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Config root must be a JSON object")
            # Capture the version stored in the file *before* the deep-merge
            # overwrites it with the default, so _migrate_config_version() can
            # compare the actual file version against the expected one.
            self._file_config_version = data.get("config_version", "")
            # Deep-merge so nested dict defaults (e.g. new ui_pref keys) are
            # preserved when an older config file omits them.
            self._deep_merge(self._config, data)
        except (json.JSONDecodeError, ValueError) as exc:
            self._load_error = str(exc)
            logger.warning(
                "Config file %s is invalid — using defaults. Error: %s",
                self._config_path,
                exc,
            )
        except OSError as exc:
            self._load_error = str(exc)
            logger.warning("Could not read config file %s: %s", self._config_path, exc)

    def _sanitize(self) -> None:
        """Validate config values; replace invalid entries with safe defaults.

        Called after loading from disk so that manually-edited invalid values
        never reach the rest of the application.
        """
        sanitize_loaded_config(
            self._config,
            self.DEFAULT_CONFIG,
            logger=logger,
        )

    @staticmethod
    def _coerce_float(value: object) -> float:
        """Coerce JSON-like scalar values to float with strict typing."""
        return _cs_coerce_float(value)

    @staticmethod
    def _coerce_int(value: object) -> int:
        """Coerce JSON-like scalar values to int with strict typing."""
        return _cs_coerce_int(value)

    def _migrate_config_version(self) -> None:
        """If the loaded config_version is outdated, update it and save.

        This ensures that old config files gain any new default keys that were
        added in later app versions (already filled in by the deep-merge in
        ``_load``).  The save is performed before env-override values are
        applied so that runtime-only overrides are not written to disk.
        """
        # Compare against the version found in the file (before it was merged),
        # not the in-memory value (which may already carry the default version).
        target = self.DEFAULT_CONFIG["config_version"]
        current = self._file_config_version
        if current == target:
            return
        logger.info(
            "Config version migrated from %r to %r; saving updated config.",
            current,
            target,
        )
        self._config["config_version"] = target
        try:
            self.save()
        except ConfigError as exc:
            logger.warning("Could not save migrated config: %s", exc)

    def _apply_env_overrides(self) -> None:
        for env_var, key in self._ENV_VAR_MAP.items():
            value = os.environ.get(env_var)
            if value is not None:
                if key == "debug":
                    self._config[key] = value.lower() in ("1", "true", "yes")
                else:
                    self._config[key] = value

    def _get_mtime(self) -> Optional[float]:
        try:
            return self._config_path.stat().st_mtime
        except OSError:
            return None

    def _watch_loop(self, interval: float) -> None:
        while not self._watch_stop.is_set():
            self._watch_stop.wait(interval)
            if self._watch_stop.is_set():
                break
            mtime = self._get_mtime()
            if mtime is not None and mtime != self._last_mtime:
                logger.debug("Config file changed, reloading.")
                try:
                    self.reload()
                except Exception:  # pylint: disable=broad-except
                    # Keep watcher alive even if reload fails unexpectedly.
                    self._last_mtime = mtime
                    logger.exception("Config reload failed; keeping previous settings")
                    continue
                for cb in list(self._reload_callbacks):
                    try:
                        cb(self)
                    except Exception:  # pylint: disable=broad-except
                        logger.exception("Config reload callback raised an exception")
