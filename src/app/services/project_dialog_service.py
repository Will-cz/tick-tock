"""UI-facing service for project dialog data operations."""

from __future__ import annotations

from typing import Any, Optional

from src.storage import Storage
from src.sub_activities import SubActivityManager


class ProjectDialogService:
    """Encapsulates storage and sub-activity operations for project dialog."""

    def __init__(self, storage: Optional[Storage]) -> None:
        self._storage = storage

    @property
    def available(self) -> bool:
        """Return True when a storage backend is available."""
        return self._storage is not None

    def list_sub_activities(self, project_id: int) -> list[dict[str, Any]]:
        """Return sub-activities for a project, or an empty list when unavailable."""
        if self._storage is None:
            return []
        return self._storage.list_sub_activities(project_id)

    def get_daily_seconds_by_project(self, date_str: str) -> dict[Any, Any]:
        """Return per-project daily totals for a date, or an empty mapping."""
        if self._storage is None:
            return {}
        return self._storage.get_daily_seconds_by_project(date_str)

    def add_sub_activity(
        self, project_id: int, name: str, description: str = ""
    ) -> None:
        """Create a sub-activity under the given project."""
        if self._storage is None:
            return
        manager = SubActivityManager(self._storage, project_id)
        manager.add(name, description)

    def delete_sub_activity(self, sub_activity_id: int) -> None:
        """Delete a sub-activity by id when storage is available."""
        if self._storage is None:
            return
        self._storage.delete_sub_activity(sub_activity_id)

    def update_sub_activity(
        self,
        project_id: int,
        sub_activity_id: int,
        name: str,
        description: str,
    ) -> None:
        """Update a sub-activity's name and description."""
        if self._storage is None:
            return
        manager = SubActivityManager(self._storage, project_id)
        manager.update(sub_activity_id, name, description)

    def set_sub_activity_archived(
        self,
        project_id: int,
        sub_activity_id: int,
        archived: bool,
    ) -> None:
        """Archive or unarchive a sub-activity."""
        if self._storage is None:
            return
        manager = SubActivityManager(self._storage, project_id)
        manager.set_archived(sub_activity_id, archived)
