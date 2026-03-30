"""Config value sanitation helpers."""

from __future__ import annotations

import copy
import logging
from typing import Any, cast

from src.validation import HEX_COLOR_RE


def coerce_float(value: object) -> float:
    """Coerce a JSON-like scalar to float; rejects booleans and unsupported types."""
    if isinstance(value, bool):
        raise ValueError("bool is not a valid float setting")
    if isinstance(value, (int, float, str)):
        return float(value)
    raise TypeError("unsupported value type for float coercion")


def coerce_int(value: object) -> int:
    """Coerce a JSON-like scalar to int; rejects booleans and unsupported types."""
    if isinstance(value, bool):
        raise ValueError("bool is not a valid integer setting")
    if isinstance(value, (int, float, str)):
        return int(float(value))
    raise TypeError("unsupported value type for int coercion")


def sanitize_loaded_config(
    config: dict[str, Any],
    defaults: dict[str, Any],
    *,
    logger: logging.Logger,
) -> None:
    """Validate loaded config values and replace invalid entries in-place."""

    ui = config.get("ui_preferences")
    if not isinstance(ui, dict):
        logger.warning("Config: ui_preferences is invalid, resetting to defaults")
        config["ui_preferences"] = copy.deepcopy(defaults["ui_preferences"])
        ui = config["ui_preferences"]
    ui_cfg = cast(dict[str, Any], ui)

    opacity = ui_cfg.get("opacity")
    try:
        opacity = coerce_float(opacity)
        if not 0.3 <= opacity <= 1.0:
            raise ValueError("out of range")
        ui_cfg["opacity"] = opacity
    except (TypeError, ValueError):
        logger.warning(
            "Config: invalid opacity %r, resetting to %.2f",
            ui_cfg.get("opacity"),
            defaults["ui_preferences"]["opacity"],
        )
        ui_cfg["opacity"] = defaults["ui_preferences"]["opacity"]

    if not isinstance(ui_cfg.get("always_on_top"), bool):
        logger.warning(
            "Config: invalid always_on_top %r, resetting to %r",
            ui_cfg.get("always_on_top"),
            defaults["ui_preferences"]["always_on_top"],
        )
        ui_cfg["always_on_top"] = defaults["ui_preferences"]["always_on_top"]

    for key in ("window_x", "window_y"):
        val = ui_cfg.get(key)
        if val is not None:
            try:
                ui_cfg[key] = int(val)
            except (TypeError, ValueError):
                logger.warning("Config: invalid %s %r, resetting to None", key, val)
                ui_cfg[key] = None

    ts = config.get("timer_settings")
    if not isinstance(ts, dict):
        logger.warning("Config: timer_settings is invalid, resetting to defaults")
        config["timer_settings"] = copy.deepcopy(defaults["timer_settings"])
        ts = config["timer_settings"]
    ts_cfg = cast(dict[str, Any], ts)

    for key, valid in (
        ("autosave_interval_minutes", {1, 5, 10, 15}),
        ("time_rounding_minutes", {0, 5, 15, 30}),
    ):
        val = ts_cfg.get(key)
        try:
            coerced = coerce_int(val)
            if coerced not in valid:
                raise ValueError("not in valid set")
            ts_cfg[key] = coerced
        except (TypeError, ValueError):
            logger.warning("Config: invalid %s %r, resetting to default", key, val)
            ts_cfg[key] = defaults["timer_settings"][key]

    if ts_cfg.get("date_format") not in {"DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"}:
        logger.warning(
            "Config: invalid date_format %r, resetting to default",
            ts_cfg.get("date_format"),
        )
        ts_cfg["date_format"] = defaults["timer_settings"]["date_format"]

    if ts_cfg.get("time_format") not in {"12h", "24h"}:
        logger.warning(
            "Config: invalid time_format %r, resetting to default",
            ts_cfg.get("time_format"),
        )
        ts_cfg["time_format"] = defaults["timer_settings"]["time_format"]

    mbf = ts_cfg.get("max_backup_files")
    try:
        mbf = coerce_int(mbf)
        if mbf < 1:
            raise ValueError("must be >= 1")
        ts_cfg["max_backup_files"] = mbf
    except (TypeError, ValueError):
        logger.warning(
            "Config: invalid max_backup_files %r, resetting to default",
            ts_cfg.get("max_backup_files"),
        )
        ts_cfg["max_backup_files"] = defaults["timer_settings"]["max_backup_files"]

    retention_days = ts_cfg.get("activity_history_retention_days")
    try:
        retention_days = coerce_int(retention_days)
        if retention_days < 1:
            raise ValueError("must be >= 1")
        ts_cfg["activity_history_retention_days"] = retention_days
    except (TypeError, ValueError):
        logger.warning(
            (
                "Config: invalid activity_history_retention_days %r, "
                "resetting to default"
            ),
            ts_cfg.get("activity_history_retention_days"),
        )
        ts_cfg["activity_history_retention_days"] = defaults["timer_settings"][
            "activity_history_retention_days"
        ]

    activity_max = ts_cfg.get("activity_log_max_entries")
    try:
        activity_max = coerce_int(activity_max)
        if activity_max < 1:
            raise ValueError("must be >= 1")
        ts_cfg["activity_log_max_entries"] = activity_max
    except (TypeError, ValueError):
        logger.warning(
            "Config: invalid activity_log_max_entries %r, resetting to default",
            ts_cfg.get("activity_log_max_entries"),
        )
        ts_cfg["activity_log_max_entries"] = defaults["timer_settings"][
            "activity_log_max_entries"
        ]

    if not isinstance(config.get("theme"), dict):
        logger.warning("Config: theme is invalid, resetting to defaults")
        config["theme"] = copy.deepcopy(defaults["theme"])
    theme = config["theme"]
    assert isinstance(theme, dict)
    theme_cfg = cast(dict[str, Any], theme)

    theme_name = str(theme_cfg.get("name", defaults["theme"]["name"])).lower()
    valid_theme_names = {"matrix", "dark", "light", "custom"}
    if theme_name not in valid_theme_names:
        logger.warning(
            "Config: invalid theme name %r, resetting to default",
            theme_cfg.get("name"),
        )
        theme_name = str(defaults["theme"]["name"])
    theme_cfg["name"] = theme_name

    custom_raw = theme_cfg.get("custom")
    if not isinstance(custom_raw, dict):
        logger.warning("Config: theme.custom is invalid, resetting to defaults")
        custom_raw = copy.deepcopy(defaults["theme"]["custom"])
        theme_cfg["custom"] = custom_raw
    custom_cfg = cast(dict[str, Any], custom_raw)

    for key in ("bg", "fg", "accent"):
        raw = custom_cfg.get(key)
        if not isinstance(raw, str) or HEX_COLOR_RE.fullmatch(raw) is None:
            logger.warning(
                "Config: invalid theme.custom.%s %r, resetting to default",
                key,
                raw,
            )
            custom_cfg[key] = defaults["theme"]["custom"][key]
