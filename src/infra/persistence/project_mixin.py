"""Project persistence mixin for :class:`src.storage.Storage`."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from typing import Any, ContextManager, Protocol, cast

logger = logging.getLogger(__name__)


class _ProjectStorage(Protocol):
    def connect(self) -> ContextManager[sqlite3.Connection]:
        """Yield a DB connection context."""
        raise NotImplementedError

    def sanitize_elapsed_for_write(self, value: object, field_name: str) -> float:
        """Validate elapsed values before writing to persistence."""
        raise NotImplementedError


class ProjectMixin:
    """Mixin providing project CRUD and elapsed-save methods."""

    def create_project(
        self: _ProjectStorage,
        name: str,
        description: str,
        *,
        ref_number: str = "",
        alias: str = "",
        color: str = "",
        notes: str = "",
    ) -> int:
        """Insert a project row and return the created project id."""
        with self.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO projects"
                " (name, description, elapsed_seconds, created_at,"
                " ref_number, alias, color, notes)"
                " VALUES (?, ?, 0.0, ?, ?, ?, ?, ?)",
                (
                    name,
                    description,
                    datetime.now().isoformat(),
                    ref_number,
                    alias,
                    color,
                    notes,
                ),
            )
            rowid = cursor.lastrowid
            if rowid is None:
                raise sqlite3.DatabaseError("Failed to create project row id")
            return int(rowid)

    def update_project(
        self: _ProjectStorage,
        project_id: int,
        name: str,
        description: str,
        *,
        ref_number: str = "",
        alias: str = "",
        color: str = "",
        notes: str = "",
    ) -> None:
        """Update mutable project fields by id."""
        with self.connect() as conn:
            conn.execute(
                "UPDATE projects"
                " SET name = ?, description = ?,"
                " ref_number = ?, alias = ?, color = ?, notes = ?"
                " WHERE id = ?",
                (name, description, ref_number, alias, color, notes, project_id),
            )

    def set_project_archived(
        self: _ProjectStorage, project_id: int, archived: bool
    ) -> None:
        """Archive or unarchive a project row."""
        with self.connect() as conn:
            conn.execute(
                "UPDATE projects SET archived = ? WHERE id = ?",
                (1 if archived else 0, project_id),
            )

    def delete_project(self: _ProjectStorage, project_id: int) -> None:
        """Delete a project and all dependent rows."""
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM daily_sub_time_log WHERE project_id = ?", (project_id,)
            )
            conn.execute(
                "DELETE FROM sub_activities WHERE project_id = ?", (project_id,)
            )
            conn.execute(
                "DELETE FROM daily_time_log WHERE project_id = ?", (project_id,)
            )
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    def list_projects(self: _ProjectStorage) -> list[dict[str, Any]]:
        """Return all projects in storage order with sanitized fields."""
        with self.connect() as conn:
            rows = cast(
                list[tuple[Any, Any, Any, Any, Any, Any, Any, Any, Any, Any]],
                conn.execute(
                    "SELECT id, name, description, elapsed_seconds, created_at,"
                    " ref_number, alias, color, archived, notes"
                    " FROM projects ORDER BY id"
                ).fetchall(),
            )
        result: list[dict[str, Any]] = []
        for r in rows:
            project_id = int(r[0])
            elapsed = r[3]
            if (
                not isinstance(elapsed, (int, float))
                or elapsed < 0
                or elapsed != elapsed
            ):
                logger.warning(
                    "Project %d has invalid elapsed_seconds %r, resetting to 0",
                    project_id,
                    elapsed,
                )
                elapsed = 0.0
            result.append(
                {
                    "id": project_id,
                    "name": str(r[1]) if r[1] is not None else "",
                    "description": str(r[2]) if r[2] is not None else "",
                    "elapsed_seconds": float(elapsed),
                    "created_at": str(r[4]) if r[4] is not None else "",
                    "ref_number": str(r[5]) if r[5] is not None else "",
                    "alias": str(r[6]) if r[6] is not None else "",
                    "color": str(r[7]) if r[7] is not None else "",
                    "archived": bool(r[8]),
                    "notes": str(r[9]) if r[9] is not None else "",
                }
            )
        return result

    def save_project_elapsed(
        self: _ProjectStorage, project_id: int, elapsed_seconds: float
    ) -> None:
        """Persist elapsed seconds for one project."""
        clean_elapsed = self.sanitize_elapsed_for_write(
            elapsed_seconds, "projects.elapsed_seconds"
        )
        with self.connect() as conn:
            conn.execute(
                "UPDATE projects SET elapsed_seconds = ? WHERE id = ?",
                (clean_elapsed, project_id),
            )
