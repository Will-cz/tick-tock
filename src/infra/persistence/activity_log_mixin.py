"""Activity-log persistence mixin for :class:`src.storage.Storage`."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from typing import Any, ContextManager, Optional, Protocol, TypedDict, cast


class ActivityLogEntry(TypedDict):
    """Single activity-log row shape returned by persistence reads."""

    id: int
    timestamp: str
    action: str
    project: str


class _ActivityLogStorage(Protocol):
    def connect(self) -> ContextManager[sqlite3.Connection]:
        """Yield a DB connection context."""
        raise NotImplementedError


class ActivityLogMixin:
    """Mixin providing activity-log read/write methods."""

    def log_activity(
        self: _ActivityLogStorage, action: str, project: str = "default"
    ) -> None:
        """Append an activity log entry with the current timestamp."""
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO activity_log (timestamp, action, project)"
                " VALUES (?, ?, ?)",
                (datetime.now().isoformat(), action, project),
            )

    def get_activity_log(
        self: _ActivityLogStorage, limit: int = 100
    ) -> list[ActivityLogEntry]:
        """Return the most recent activity log entries (newest first)."""
        with self.connect() as conn:
            rows = cast(
                list[tuple[Any, Any, Any, Any]],
                conn.execute(
                    "SELECT id, timestamp, action, project FROM activity_log "
                    "ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall(),
            )
        return [
            {
                "id": int(r[0]),
                "timestamp": str(r[1]),
                "action": str(r[2]),
                "project": str(r[3]),
            }
            for r in rows
        ]

    def apply_retention_policy(
        self: _ActivityLogStorage,
        *,
        history_days: Optional[int] = None,
        max_activity_entries: Optional[int] = None,
    ) -> dict[str, int]:
        """Prune historical tables according to retention settings.

        Returns a mapping with delete counts per table.
        """
        deleted = {
            "daily_time_log": 0,
            "daily_sub_time_log": 0,
            "activity_log": 0,
        }
        with self.connect() as conn:
            if history_days is not None and history_days > 0:
                cutoff_date = (date.today() - timedelta(days=history_days)).isoformat()
                cur = conn.execute(
                    "DELETE FROM daily_time_log WHERE date < ?",
                    (cutoff_date,),
                )
                deleted["daily_time_log"] = max(0, int(cur.rowcount))
                cur = conn.execute(
                    "DELETE FROM daily_sub_time_log WHERE date < ?",
                    (cutoff_date,),
                )
                deleted["daily_sub_time_log"] = max(0, int(cur.rowcount))

            if max_activity_entries is not None and max_activity_entries > 0:
                cur = conn.execute(
                    "DELETE FROM activity_log "
                    "WHERE id NOT IN ("
                    "  SELECT id FROM activity_log ORDER BY id DESC LIMIT ?"
                    ")",
                    (max_activity_entries,),
                )
                deleted["activity_log"] = max(0, int(cur.rowcount))
        return deleted
