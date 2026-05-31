"""Validation helpers for Storage JSON import payloads."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Callable, Optional, TypedDict, cast

from src.validation import normalize_name


class ProjectImportRow(TypedDict):
    """Validated project row from an import payload."""

    id: int
    name: str
    description: str
    elapsed_seconds: float
    created_at: str
    ref_number: str
    alias: str
    color: str
    archived: bool
    notes: str


class SubActivityImportRow(TypedDict):
    """Validated sub-activity row from an import payload."""

    id: int
    project_id: int
    name: str
    description: str
    elapsed_seconds: float
    created_at: str
    archived: bool


class DailyTimeLogImportRow(TypedDict):
    """Validated daily project time-log row."""

    date: str
    project_id: int
    seconds: float


class DailySubTimeLogImportRow(TypedDict):
    """Validated daily sub-activity time-log row."""

    date: str
    project_id: int
    sub_activity_id: int
    seconds: float


class TimerStateImportRow(TypedDict):
    """Validated timer-state snapshot row."""

    elapsed_seconds: float
    state: str
    saved_at: str


class ValidatedImportPayload(TypedDict):
    """Normalized, validated payload returned by import validation."""

    projects: list[ProjectImportRow]
    sub_activities: list[SubActivityImportRow]
    daily_time_log: list[DailyTimeLogImportRow]
    daily_sub_time_log: list[DailySubTimeLogImportRow]
    timer_state: Optional[TimerStateImportRow]


_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


def _validate_text(value: object, *, field_name: str, max_length: int) -> str:
    """Return a trimmed text field validated for control chars and size."""
    text = str(value).strip()
    if len(text) > max_length:
        raise ValueError(f"{field_name} exceeds {max_length} characters")
    if _CONTROL_CHAR_RE.search(text) is not None:
        raise ValueError(f"{field_name} contains control characters")
    return text


def _require_iso_datetime(value: object, field_name: str) -> str:
    """Validate an ISO-8601 datetime string."""
    text = str(value)
    try:
        datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc
    return text


def validate_import_payload(
    data: object,
    *,
    schema_version: int,
    require_int: Callable[[object, str], int],
    require_non_negative_finite_float: Callable[[object, str], float],
    require_iso_date: Callable[[object, str], str],
    sanitize_timer_state_for_write: Callable[[object], str],
) -> ValidatedImportPayload:
    """Validate and normalize an import payload before mutating the DB."""
    if not isinstance(data, dict) or "projects" not in data:
        raise ValueError("Invalid export file: missing 'projects' key")

    payload = cast(dict[str, object], data)
    if payload.get("export_version") != 1:
        raise ValueError(f"Unsupported export version: {payload.get('export_version')}")

    schema_value = payload.get("schema_version", 1)
    schema_int = require_int(schema_value, "schema_version")
    if schema_int > schema_version:
        raise ValueError(
            "Unsupported schema_version "
            f"{schema_int}; this build supports <= {schema_version}"
        )

    now_iso = datetime.now().isoformat()

    projects_raw = payload.get("projects", [])
    if not isinstance(projects_raw, list):
        raise ValueError("Invalid export file: 'projects' must be a list")
    project_items = cast(list[object], projects_raw)
    projects: list[ProjectImportRow] = []
    project_ids: set[int] = set()
    for idx, raw in enumerate(project_items):
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid projects[{idx}] row")
        row = cast(dict[str, object], raw)
        project_id = require_int(row.get("id"), f"projects[{idx}].id")
        if project_id <= 0 or project_id in project_ids:
            raise ValueError(f"Invalid or duplicate project id: {project_id}")
        project_ids.add(project_id)
        projects.append(
            {
                "id": project_id,
                "name": normalize_name(
                    row.get("name", ""),
                    field_label=f"projects[{idx}].name",
                ),
                "description": _validate_text(
                    row.get("description", ""),
                    field_name=f"projects[{idx}].description",
                    max_length=2000,
                ),
                "elapsed_seconds": require_non_negative_finite_float(
                    row.get("elapsed_seconds", 0.0),
                    f"projects[{idx}].elapsed_seconds",
                ),
                "created_at": _require_iso_datetime(
                    row.get("created_at", now_iso),
                    f"projects[{idx}].created_at",
                ),
                "ref_number": _validate_text(
                    row.get("ref_number", ""),
                    field_name=f"projects[{idx}].ref_number",
                    max_length=256,
                ),
                "alias": _validate_text(
                    row.get("alias", ""),
                    field_name=f"projects[{idx}].alias",
                    max_length=256,
                ),
                "color": _validate_text(
                    row.get("color", ""),
                    field_name=f"projects[{idx}].color",
                    max_length=32,
                ),
                "archived": bool(row.get("archived", False)),
                "notes": _validate_text(
                    row.get("notes", ""),
                    field_name=f"projects[{idx}].notes",
                    max_length=10000,
                ),
            }
        )

    subs_raw = payload.get("sub_activities", [])
    if not isinstance(subs_raw, list):
        raise ValueError("Invalid export file: 'sub_activities' must be a list")
    sub_items = cast(list[object], subs_raw)
    sub_activities: list[SubActivityImportRow] = []
    sub_ids: set[int] = set()
    sub_project_map: dict[int, int] = {}
    for idx, raw in enumerate(sub_items):
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid sub_activities[{idx}] row")
        row = cast(dict[str, object], raw)
        sub_id = require_int(row.get("id"), f"sub_activities[{idx}].id")
        project_id = require_int(
            row.get("project_id"), f"sub_activities[{idx}].project_id"
        )
        if sub_id <= 0 or sub_id in sub_ids:
            raise ValueError(f"Invalid or duplicate sub-activity id: {sub_id}")
        if project_id not in project_ids:
            raise ValueError(
                f"sub_activities[{idx}] references unknown project_id {project_id}"
            )
        sub_ids.add(sub_id)
        sub_project_map[sub_id] = project_id
        sub_activities.append(
            {
                "id": sub_id,
                "project_id": project_id,
                "name": normalize_name(
                    row.get("name", ""),
                    field_label=f"sub_activities[{idx}].name",
                ),
                "description": _validate_text(
                    row.get("description", ""),
                    field_name=f"sub_activities[{idx}].description",
                    max_length=2000,
                ),
                "elapsed_seconds": require_non_negative_finite_float(
                    row.get("elapsed_seconds", 0.0),
                    f"sub_activities[{idx}].elapsed_seconds",
                ),
                "created_at": _require_iso_datetime(
                    row.get("created_at", now_iso),
                    f"sub_activities[{idx}].created_at",
                ),
                "archived": bool(row.get("archived", False)),
            }
        )

    daily_raw = payload.get("daily_time_log", [])
    if not isinstance(daily_raw, list):
        raise ValueError("Invalid export file: 'daily_time_log' must be a list")
    daily_items = cast(list[object], daily_raw)
    daily_time_log: list[DailyTimeLogImportRow] = []
    for idx, raw in enumerate(daily_items):
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid daily_time_log[{idx}] row")
        row = cast(dict[str, object], raw)
        project_id = require_int(
            row.get("project_id"), f"daily_time_log[{idx}].project_id"
        )
        if project_id not in project_ids:
            raise ValueError(
                f"daily_time_log[{idx}] references unknown project_id {project_id}"
            )
        daily_time_log.append(
            {
                "date": require_iso_date(
                    row.get("date"), f"daily_time_log[{idx}].date"
                ),
                "project_id": project_id,
                "seconds": require_non_negative_finite_float(
                    row.get("seconds", 0.0), f"daily_time_log[{idx}].seconds"
                ),
            }
        )

    daily_sub_raw = payload.get("daily_sub_time_log", [])
    if not isinstance(daily_sub_raw, list):
        raise ValueError("Invalid export file: 'daily_sub_time_log' must be a list")
    daily_sub_items = cast(list[object], daily_sub_raw)
    daily_sub_time_log: list[DailySubTimeLogImportRow] = []
    for idx, raw in enumerate(daily_sub_items):
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid daily_sub_time_log[{idx}] row")
        row = cast(dict[str, object], raw)
        project_id = require_int(
            row.get("project_id"), f"daily_sub_time_log[{idx}].project_id"
        )
        sub_id = require_int(
            row.get("sub_activity_id"),
            f"daily_sub_time_log[{idx}].sub_activity_id",
        )
        if project_id not in project_ids:
            raise ValueError(
                f"daily_sub_time_log[{idx}] references unknown project_id {project_id}"
            )
        if sub_id not in sub_ids:
            raise ValueError(
                f"daily_sub_time_log[{idx}] references unknown sub_activity_id {sub_id}"
            )
        if sub_project_map.get(sub_id) != project_id:
            raise ValueError(
                "daily_sub_time_log"
                f"[{idx}] project/sub mismatch ({project_id}/{sub_id})"
            )
        daily_sub_time_log.append(
            {
                "date": require_iso_date(
                    row.get("date"),
                    f"daily_sub_time_log[{idx}].date",
                ),
                "project_id": project_id,
                "sub_activity_id": sub_id,
                "seconds": require_non_negative_finite_float(
                    row.get("seconds", 0.0),
                    f"daily_sub_time_log[{idx}].seconds",
                ),
            }
        )

    timer_state_raw = payload.get("timer_state")
    timer_state: Optional[TimerStateImportRow]
    if timer_state_raw is None:
        timer_state = None
    else:
        if not isinstance(timer_state_raw, dict):
            raise ValueError("Invalid timer_state payload")
        timer_row = cast(dict[str, object], timer_state_raw)
        elapsed = require_non_negative_finite_float(
            timer_row.get("elapsed_seconds", 0.0),
            "timer_state.elapsed_seconds",
        )
        state = sanitize_timer_state_for_write(timer_row.get("state", "stopped"))
        timer_state = {
            "elapsed_seconds": elapsed,
            "state": state,
            "saved_at": _require_iso_datetime(
                timer_row.get("saved_at", now_iso),
                "timer_state.saved_at",
            ),
        }

    activity_raw = payload.get("activity_log", [])
    if activity_raw and not isinstance(activity_raw, list):
        raise ValueError("Invalid export file: 'activity_log' must be a list")
    # activity_log is no longer persisted; the field is accepted for
    # backward compatibility with older exports but discarded.

    return {
        "projects": projects,
        "sub_activities": sub_activities,
        "daily_time_log": daily_time_log,
        "daily_sub_time_log": daily_sub_time_log,
        "timer_state": timer_state,
    }
