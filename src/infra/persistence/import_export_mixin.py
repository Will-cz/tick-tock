"""Import/export persistence mixin for :class:`src.storage.Storage`."""

from __future__ import annotations

import json
import logging
import math
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, ContextManager, Optional, Protocol, cast

from src.infra.persistence.activity_log_mixin import ActivityLogEntry
from src.infra.persistence.import_validation import (
    ValidatedImportPayload,
    validate_import_payload,
)

logger = logging.getLogger(__name__)


class _ImportExportStorage(Protocol):
    def connect(self) -> ContextManager[sqlite3.Connection]:
        """Yield a DB connection context."""
        raise NotImplementedError

    def require_int(self, value: object, field_name: str) -> int:
        """Validate and coerce integer payload fields."""
        raise NotImplementedError

    def sanitize_timer_state_for_write(self, state: object) -> str:
        """Normalize timer state values for persistence."""
        raise NotImplementedError

    def require_non_negative_finite_float(
        self, value: object, field_name: str
    ) -> float:
        """Validate and coerce non-negative finite float fields."""
        raise NotImplementedError

    def require_iso_date(self, value: object, field_name: str) -> str:
        """Validate ISO-8601 date strings."""
        raise NotImplementedError

    def validate_import_payload(self, data: object) -> ValidatedImportPayload:
        """Validate import payload structure and values."""
        raise NotImplementedError

    def load_timer_state(self) -> Optional[dict[str, Any]]:
        """Load persisted timer state snapshot."""
        raise NotImplementedError

    def list_projects(self) -> list[dict[str, Any]]:
        """Return persisted projects as dictionaries."""
        raise NotImplementedError

    def get_activity_log(self, limit: int = 100) -> list[ActivityLogEntry]:
        """Return recent activity-log entries."""
        raise NotImplementedError


class ImportExportMixin:
    """Mixin providing JSON export/import methods."""

    def export_json(self: _ImportExportStorage, path: Path) -> None:
        """Export all data to a portable JSON file at *path*.

        The exported file contains projects, daily time log, timer state, and
        the most recent activity log entries.  It can be re-imported with
        :meth:`import_json`.
        """
        with self.connect() as conn:
            daily_rows = cast(
                list[tuple[Any, Any, Any]],
                conn.execute(
                    "SELECT date, project_id, seconds FROM daily_time_log"
                    " ORDER BY date, project_id"
                ).fetchall(),
            )
            sub_rows = cast(
                list[tuple[Any, Any, Any, Any, Any, Any, Any]],
                conn.execute(
                    "SELECT id, project_id, name, description,"
                    " elapsed_seconds, created_at,"
                    " archived FROM sub_activities ORDER BY id"
                ).fetchall(),
            )
            daily_sub_rows = cast(
                list[tuple[Any, Any, Any, Any]],
                conn.execute(
                    "SELECT date, project_id, sub_activity_id, seconds"
                    " FROM daily_sub_time_log"
                    " ORDER BY date, project_id, sub_activity_id"
                ).fetchall(),
            )

        data: dict[str, object] = {
            "export_version": 1,
            "exported_at": datetime.now().isoformat(),
            "schema_version": int(getattr(self, "_SCHEMA_VERSION", 1)),
            "timer_state": self.load_timer_state(),
            "projects": self.list_projects(),
            "sub_activities": [
                {
                    "id": int(r[0]),
                    "project_id": int(r[1]),
                    "name": str(r[2]),
                    "description": str(r[3]),
                    "elapsed_seconds": float(r[4]),
                    "created_at": str(r[5]),
                    "archived": bool(r[6]),
                }
                for r in sub_rows
            ],
            "daily_time_log": [
                {
                    "date": str(r[0]),
                    "project_id": int(r[1]),
                    "seconds": float(r[2]),
                }
                for r in daily_rows
            ],
            "daily_sub_time_log": [
                {
                    "date": str(r[0]),
                    "project_id": int(r[1]),
                    "sub_activity_id": int(r[2]),
                    "seconds": float(r[3]),
                }
                for r in daily_sub_rows
            ],
            "activity_log": self.get_activity_log(limit=10_000),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(path)
        logger.info("Data exported to %s", path)

    @staticmethod
    def require_non_negative_finite_float(value: object, field_name: str) -> float:
        """Validate numeric import fields used for elapsed/seconds values."""
        try:
            if isinstance(value, bool):
                raise ValueError("bool is not a valid numeric value")
            if isinstance(value, (int, float, str)):
                parsed = float(value)
            else:
                raise TypeError("unsupported numeric value type")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid {field_name}: {value!r}") from exc
        if math.isnan(parsed) or math.isinf(parsed) or parsed < 0:
            raise ValueError(f"Invalid {field_name}: {value!r}")
        return parsed

    @staticmethod
    def require_iso_date(value: object, field_name: str) -> str:
        """Validate YYYY-MM-DD dates for daily log import rows."""
        text = str(value)
        try:
            date.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"Invalid {field_name}: {value!r}") from exc
        return text

    def validate_import_payload(
        self: _ImportExportStorage, data: object
    ) -> ValidatedImportPayload:
        """Validate and normalize an import payload before mutating the DB."""
        return validate_import_payload(
            data,
            schema_version=int(getattr(self, "_SCHEMA_VERSION", 1)),
            require_int=self.require_int,
            require_non_negative_finite_float=self.require_non_negative_finite_float,
            require_iso_date=self.require_iso_date,
            sanitize_timer_state_for_write=self.sanitize_timer_state_for_write,
        )

    def import_json(self: _ImportExportStorage, path: Path) -> None:
        """Import data from a JSON file previously created by :meth:`export_json`.

        **Replaces** all existing projects and daily time log entries.  Timer
        state is restored from the file.  Activity log entries are appended.

        Raises:
            ValueError: if the file is not a valid export.
            OSError:    if the file cannot be read.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        validated = self.validate_import_payload(data)

        with self.connect() as conn:
            # Replace projects and all dependent rows.
            conn.execute("DELETE FROM daily_sub_time_log")
            conn.execute("DELETE FROM sub_activities")
            conn.execute("DELETE FROM daily_time_log")
            conn.execute("DELETE FROM projects")
            for p in validated["projects"]:
                conn.execute(
                    "INSERT INTO projects"
                    " (id, name, description, elapsed_seconds, created_at,"
                    "  ref_number, alias, color, archived, notes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        p["id"],
                        p["name"],
                        p["description"],
                        p["elapsed_seconds"],
                        p["created_at"],
                        p["ref_number"],
                        p["alias"],
                        p["color"],
                        1 if p["archived"] else 0,
                        p["notes"],
                    ),
                )
            # Replace sub-activities.
            for sa in validated["sub_activities"]:
                conn.execute(
                    "INSERT INTO sub_activities"
                    " (id, project_id, name, description, elapsed_seconds, created_at,"
                    " archived)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        sa["id"],
                        sa["project_id"],
                        sa["name"],
                        sa["description"],
                        sa["elapsed_seconds"],
                        sa["created_at"],
                        1 if sa["archived"] else 0,
                    ),
                )
            # Replace daily time log.
            for daily_entry in validated["daily_time_log"]:
                conn.execute(
                    "INSERT OR REPLACE INTO daily_time_log (date, project_id, seconds)"
                    " VALUES (?, ?, ?)",
                    (
                        daily_entry["date"],
                        daily_entry["project_id"],
                        daily_entry["seconds"],
                    ),
                )
            # Replace sub-activity daily log.
            for daily_sub_entry in validated["daily_sub_time_log"]:
                conn.execute(
                    "INSERT OR REPLACE INTO daily_sub_time_log"
                    " (date, project_id, sub_activity_id, seconds)"
                    " VALUES (?, ?, ?, ?)",
                    (
                        daily_sub_entry["date"],
                        daily_sub_entry["project_id"],
                        daily_sub_entry["sub_activity_id"],
                        daily_sub_entry["seconds"],
                    ),
                )
            # Restore timer state.
            ts = validated["timer_state"]
            if ts is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO timer_state"
                    " (id, elapsed_seconds, state, saved_at)"
                    " VALUES (1, ?, ?, ?)",
                    (
                        ts["elapsed_seconds"],
                        ts["state"],
                        ts["saved_at"],
                    ),
                )
            else:
                conn.execute("DELETE FROM timer_state WHERE id = 1")
            # Append activity log entries from export.
            for activity_entry in validated["activity_log"]:
                conn.execute(
                    "INSERT INTO activity_log (timestamp, action, project)"
                    " VALUES (?, ?, ?)",
                    (
                        activity_entry["timestamp"],
                        activity_entry["action"],
                        activity_entry["project"],
                    ),
                )
        logger.info("Data imported from %s", path)
