"""Sub-activity persistence mixin for :class:`src.storage.Storage`."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from typing import Any, ContextManager, Protocol, cast

logger = logging.getLogger(__name__)


class _SubActivityStorage(Protocol):
    def connect(self) -> ContextManager[sqlite3.Connection]:
        """Yield a DB connection context."""
        raise NotImplementedError

    def sanitize_elapsed_for_write(self, value: object, field_name: str) -> float:
        """Validate elapsed values before writing to persistence."""
        raise NotImplementedError


class SubActivityMixin:
    """Mixin providing sub-activity CRUD and elapsed-save methods."""

    def create_sub_activity(
        self: _SubActivityStorage,
        project_id: int,
        name: str,
        description: str = "",
    ) -> int:
        """Insert a new sub-activity under *project_id*; return its id."""
        with self.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO sub_activities"
                " (project_id, name, description, elapsed_seconds, created_at)"
                " VALUES (?, ?, ?, 0.0, ?)",
                (project_id, name, description, datetime.now().isoformat()),
            )
            rowid = cursor.lastrowid
            if rowid is None:
                raise sqlite3.DatabaseError("Failed to create sub-activity row id")
            return int(rowid)

    def update_sub_activity(
        self: _SubActivityStorage,
        sub_activity_id: int,
        name: str,
        description: str = "",
    ) -> None:
        """Update the name and description of a sub-activity."""
        with self.connect() as conn:
            conn.execute(
                "UPDATE sub_activities SET name = ?, description = ? WHERE id = ?",
                (name, description, sub_activity_id),
            )

    def delete_sub_activity(self: _SubActivityStorage, sub_activity_id: int) -> None:
        """Delete a sub-activity by id."""
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM daily_sub_time_log WHERE sub_activity_id = ?",
                (sub_activity_id,),
            )
            conn.execute("DELETE FROM sub_activities WHERE id = ?", (sub_activity_id,))

    def list_sub_activities(
        self: _SubActivityStorage, project_id: int
    ) -> list[dict[str, Any]]:
        """Return all sub-activities for *project_id*, ordered by creation."""
        with self.connect() as conn:
            rows = cast(
                list[tuple[Any, Any, Any, Any, Any, Any, Any]],
                conn.execute(
                    "SELECT id, project_id, name, description, elapsed_seconds,"
                    " created_at, archived"
                    " FROM sub_activities WHERE project_id = ? ORDER BY id",
                    (project_id,),
                ).fetchall(),
            )
        result: list[dict[str, Any]] = []
        for r in rows:
            sub_id = int(r[0])
            elapsed = r[4]
            if (
                not isinstance(elapsed, (int, float))
                or elapsed < 0
                or elapsed != elapsed
            ):
                logger.warning(
                    "Sub-activity %d has invalid elapsed_seconds %r, resetting to 0",
                    sub_id,
                    elapsed,
                )
                elapsed = 0.0
            result.append(
                {
                    "id": sub_id,
                    "project_id": int(r[1]),
                    "name": str(r[2]) if r[2] is not None else "",
                    "description": str(r[3]) if r[3] is not None else "",
                    "elapsed_seconds": float(elapsed),
                    "created_at": str(r[5]) if r[5] is not None else "",
                    "archived": bool(r[6]),
                }
            )
        return result

    def save_sub_activity_elapsed(
        self: _SubActivityStorage, sub_activity_id: int, elapsed_seconds: float
    ) -> None:
        """Persist *elapsed_seconds* for a sub-activity."""
        clean_elapsed = self.sanitize_elapsed_for_write(
            elapsed_seconds, "sub_activities.elapsed_seconds"
        )
        with self.connect() as conn:
            conn.execute(
                "UPDATE sub_activities SET elapsed_seconds = ? WHERE id = ?",
                (clean_elapsed, sub_activity_id),
            )

    def set_sub_activity_archived(
        self: _SubActivityStorage, sub_activity_id: int, archived: bool
    ) -> None:
        """Archive or unarchive a sub-activity."""
        with self.connect() as conn:
            conn.execute(
                "UPDATE sub_activities SET archived = ? WHERE id = ?",
                (1 if archived else 0, sub_activity_id),
            )
