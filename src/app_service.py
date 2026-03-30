"""Application service layer — coordinates Storage, ProjectManager, and
SubActivityManager so that UI components never call the data layer directly.
"""

from pathlib import Path
from typing import Any, Optional

from src.projects import Project, ProjectManager
from src.storage import Storage
from src.sub_activities import SubActivityManager


class AppService:
    """Thin service that brokers all persistence and project-coordination
    operations on behalf of the UI layer.

    Constructed once in ``main.py`` and injected into :class:`TickTockWidget`.
    Dialogs and secondary widgets receive it (or its ``storage`` / ``project_manager``
    properties) rather than constructing their own access to the data layer.
    """

    def __init__(
        self,
        storage: Storage,
        project_manager: ProjectManager,
        default_backup_keep: Optional[int] = None,
    ) -> None:
        self._storage = storage
        self._project_mgr = project_manager
        self._default_backup_keep = default_backup_keep

    # ------------------------------------------------------------------
    # Properties — allow callers that still need the raw objects
    # ------------------------------------------------------------------

    @property
    def storage(self) -> Storage:
        """Expose the configured storage backend."""
        return self._storage

    @property
    def project_manager(self) -> ProjectManager:
        """Expose the project manager used by the service layer."""
        return self._project_mgr

    # ------------------------------------------------------------------
    # Timer state persistence
    # ------------------------------------------------------------------

    def save_timer_state(self, elapsed: float, state: str) -> None:
        """Persist timer state snapshot for crash-safe restore."""
        self._storage.save_timer_state(elapsed, state)

    def clear_timer_state(self) -> None:
        """Remove persisted timer state."""
        self._storage.clear_timer_state()

    def load_timer_state(self) -> Optional[dict[str, Any]]:
        """Load persisted timer state if available."""
        return self._storage.load_timer_state()

    def log_activity(self, event: str, project_name: str) -> None:
        """Append an activity-log event for auditing/reporting."""
        self._storage.log_activity(event, project_name)

    # ------------------------------------------------------------------
    # Daily time tracking
    # ------------------------------------------------------------------

    def add_daily_seconds(self, project_id: int, date: str, delta: float) -> None:
        """Accumulate project-level daily seconds."""
        self._storage.add_daily_seconds(project_id, date, delta)

    def add_daily_sub_activity_seconds(
        self,
        project_id: int,
        sub_activity_id: int,
        date: str,
        delta: float,
    ) -> None:
        """Accumulate sub-activity daily seconds."""
        self._storage.add_daily_sub_activity_seconds(
            project_id,
            sub_activity_id,
            date,
            delta,
        )

    # ------------------------------------------------------------------
    # Project management
    # ------------------------------------------------------------------

    def switch_project(self, project_id: int) -> Project:
        """Switch the active project and return the newly-active :class:`Project`."""
        return self._project_mgr.switch(project_id)

    def save_project_elapsed(self, elapsed: float) -> None:
        """Persist elapsed time for the active project."""
        self._project_mgr.save_elapsed(elapsed)

    def reload_projects(self) -> None:
        """Reload projects from storage."""
        self._project_mgr.reload()

    # ------------------------------------------------------------------
    # Sub-activity management
    # ------------------------------------------------------------------

    def create_sub_manager(self, project_id: int) -> SubActivityManager:
        """Create a fresh :class:`SubActivityManager` for *project_id*."""
        return SubActivityManager(self._storage, project_id)

    def list_sub_activities(self, project_id: int) -> list[Any]:
        """List sub-activities for a project id."""
        return self._storage.list_sub_activities(project_id)

    # ------------------------------------------------------------------
    # Save elapsed — routes to sub-activity or active project
    # ------------------------------------------------------------------

    def save_elapsed(
        self,
        elapsed: float,
        *,
        sub_activity_id: Optional[int] = None,
        sub_activity_mgr: Optional[SubActivityManager] = None,
    ) -> None:
        """Persist *elapsed* seconds to the active tracking target.

        If *sub_activity_id* and *sub_activity_mgr* are both provided the time
        is saved against the sub-activity; otherwise it is saved against the
        currently active project.
        """
        if sub_activity_id is not None and sub_activity_mgr is not None:
            sub_activity_mgr.save_elapsed(sub_activity_id, elapsed)
        else:
            self._project_mgr.save_elapsed(elapsed)

    # ------------------------------------------------------------------
    # Data I/O
    # ------------------------------------------------------------------

    def export_json(self, path: Path) -> None:
        """Export all persisted data to JSON."""
        self._storage.export_json(path)

    def import_json(self, path: Path) -> None:
        """Import persisted data from a JSON export file."""
        self._storage.import_json(path)

    def backup(self, keep: Optional[int] = None) -> None:
        """Create a backup of the database, honoring retention settings."""
        resolved = keep if keep is not None else self._default_backup_keep
        if resolved is not None:
            self._storage.backup(keep=max(1, int(resolved)))
            return
        self._storage.backup()
