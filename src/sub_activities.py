"""Sub-activity management for Tick-Tock Widget.

Sub-activities are children of a project, enabling time tracking at a finer
granularity.  A project can have zero or more sub-activities.  Time logged
against a sub-activity is owned by the sub-activity; callers are responsible
for aggregating to the parent project as needed.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.storage import Storage
from src.validation import normalize_name


@dataclass
class SubActivity:
    """In-memory sub-activity record for one project."""

    sub_activity_id: int
    project_id: int
    name: str
    description: str
    elapsed_seconds: float
    created_at: str
    archived: bool = False


class SubActivityManager:
    """In-memory CRUD for sub-activities belonging to a single project.

    All mutations are immediately persisted via the injected :class:`Storage`.

    Usage::

        manager = SubActivityManager(storage, project_id=1)
        sa = manager.add("Design")
        manager.save_elapsed(sa.sub_activity_id, 300.0)
    """

    def __init__(self, storage: Storage, project_id: int) -> None:
        self._storage = storage
        self._project_id = project_id
        self._sub_activities: list[SubActivity] = []
        self._load()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def project_id(self) -> int:
        """Return owning project id for this manager instance."""
        return self._project_id

    @property
    def sub_activities(self) -> list[SubActivity]:
        """Return a snapshot of sub-activities for the project."""
        return list(self._sub_activities)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(self, name: str, description: str = "") -> SubActivity:
        """Add a new sub-activity.  Raises ``ValueError`` on validation failure."""
        name = normalize_name(name, field_label="Sub-activity name")
        if any(sa.name.lower() == name.lower() for sa in self._sub_activities):
            raise ValueError(
                f"A sub-activity named '{name}' already exists in this project"
            )
        description = description.strip()
        sub_activity_id = self._storage.create_sub_activity(
            self._project_id, name, description
        )
        sa = SubActivity(
            sub_activity_id=sub_activity_id,
            project_id=self._project_id,
            name=name,
            description=description,
            elapsed_seconds=0.0,
            created_at=datetime.now().isoformat(),
            archived=False,
        )
        self._sub_activities.append(sa)
        return sa

    def update(self, sub_activity_id: int, name: str, description: str = "") -> None:
        """Rename/re-describe a sub-activity.  Raises ``ValueError`` on failure."""
        name = normalize_name(name, field_label="Sub-activity name")
        if any(
            sa.name.lower() == name.lower() and sa.sub_activity_id != sub_activity_id
            for sa in self._sub_activities
        ):
            raise ValueError(
                f"A sub-activity named '{name}' already exists in this project"
            )
        sa = self._by_id(sub_activity_id)
        description = description.strip()
        sa.name = name
        sa.description = description
        self._storage.update_sub_activity(sub_activity_id, name, description)

    def delete(self, sub_activity_id: int) -> None:
        """Delete a sub-activity by id."""
        self._by_id(sub_activity_id)  # raises if not found
        self._storage.delete_sub_activity(sub_activity_id)
        self._sub_activities = [
            sa for sa in self._sub_activities if sa.sub_activity_id != sub_activity_id
        ]

    def set_archived(self, sub_activity_id: int, archived: bool) -> None:
        """Archive or unarchive a sub-activity."""
        sa = self._by_id(sub_activity_id)
        sa.archived = archived
        self._storage.set_sub_activity_archived(sub_activity_id, archived)

    # ------------------------------------------------------------------
    # Time tracking
    # ------------------------------------------------------------------

    def save_elapsed(self, sub_activity_id: int, elapsed_seconds: float) -> None:
        """Persist *elapsed_seconds* for a sub-activity."""
        sa = self._by_id(sub_activity_id)
        sa.elapsed_seconds = elapsed_seconds
        self._storage.save_sub_activity_elapsed(sub_activity_id, elapsed_seconds)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, sub_activity_id: int) -> Optional[SubActivity]:
        """Return the sub-activity with *sub_activity_id*, or ``None``."""
        return next(
            (
                sa
                for sa in self._sub_activities
                if sa.sub_activity_id == sub_activity_id
            ),
            None,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _by_id(self, sub_activity_id: int) -> SubActivity:
        sa = self.get(sub_activity_id)
        if sa is None:
            raise ValueError(f"Sub-activity {sub_activity_id} not found")
        return sa

    def reload(self) -> None:
        """Re-read sub-activities from storage."""
        self._sub_activities = []
        self._load()

    def _load(self) -> None:
        rows = self._storage.list_sub_activities(self._project_id)
        self._sub_activities = [
            SubActivity(
                sub_activity_id=r["id"],
                project_id=r["project_id"],
                name=r["name"],
                description=r["description"],
                elapsed_seconds=r["elapsed_seconds"],
                created_at=r["created_at"],
                archived=r["archived"],
            )
            for r in rows
        ]
