"""Project management for Tick-Tock Widget."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.storage import Storage
from src.validation import normalize_name


@dataclass
class Project:
    """In-memory project record mirrored from storage."""

    project_id: int
    name: str
    description: str
    elapsed_seconds: float
    created_at: str
    ref_number: str = ""
    alias: str = ""
    color: str = ""
    archived: bool = False
    notes: str = ""


class ProjectManager:
    """In-memory CRUD for projects, persisted via Storage.

    On first run (empty DB) a "Default" project is automatically created,
    migrating any existing single-project timer state.
    """

    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._projects: list[Project] = []
        self._active_id: Optional[int] = None
        self._load()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def projects(self) -> list[Project]:
        """Return a snapshot of the current project list."""
        return list(self._projects)

    @property
    def active_project(self) -> Optional[Project]:
        """Return the currently active project, or None."""
        if self._active_id is None:
            return None
        return next(
            (p for p in self._projects if p.project_id == self._active_id), None
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(
        self,
        name: str,
        description: str = "",
        *,
        ref_number: str = "",
        alias: str = "",
        color: str = "",
        notes: str = "",
    ) -> Project:
        """Add a new project.  Raises ``ValueError`` on validation failure."""
        name = normalize_name(name, field_label="Project name")
        if any(p.name.lower() == name.lower() for p in self._projects):
            raise ValueError(f"A project named '{name}' already exists")
        alias = alias.strip()
        if alias and any(p.alias.lower() == alias.lower() for p in self._projects):
            raise ValueError(f"An alias '{alias}' already exists")
        description = description.strip()
        ref_number = ref_number.strip()
        notes = notes.strip()
        project_id = self._storage.create_project(
            name,
            description,
            ref_number=ref_number,
            alias=alias,
            color=color,
            notes=notes,
        )
        project = Project(
            project_id=project_id,
            name=name,
            description=description,
            elapsed_seconds=0.0,
            created_at=datetime.now().isoformat(),
            ref_number=ref_number,
            alias=alias,
            color=color,
            archived=False,
            notes=notes,
        )
        self._projects.append(project)
        return project

    def update(
        self,
        project_id: int,
        name: str,
        description: str = "",
        *,
        ref_number: str = "",
        alias: str = "",
        color: str = "",
        notes: str = "",
    ) -> None:
        """Rename/re-describe a project.  Raises ``ValueError`` on failure."""
        name = normalize_name(name, field_label="Project name")
        if any(
            p.name.lower() == name.lower() and p.project_id != project_id
            for p in self._projects
        ):
            raise ValueError(f"A project named '{name}' already exists")
        alias = alias.strip()
        if alias and any(
            p.alias.lower() == alias.lower() and p.project_id != project_id
            for p in self._projects
        ):
            raise ValueError(f"An alias '{alias}' already exists")
        project = self._by_id(project_id)
        description = description.strip()
        ref_number = ref_number.strip()
        notes = notes.strip()
        project.name = name
        project.description = description
        project.ref_number = ref_number
        project.alias = alias
        project.color = color
        project.notes = notes
        self._storage.update_project(
            project_id,
            name,
            description,
            ref_number=ref_number,
            alias=alias,
            color=color,
            notes=notes,
        )

    def set_archived(self, project_id: int, archived: bool) -> None:
        """Archive or unarchive a project."""
        project = self._by_id(project_id)
        project.archived = archived
        self._storage.set_project_archived(project_id, archived)
        # If archiving the active project, switch to first non-archived one.
        if archived and self._active_id == project_id:
            first = next((p for p in self._projects if not p.archived), None)
            self._active_id = first.project_id if first else None
            self._storage.set_app_state(
                "active_project_id",
                str(self._active_id) if self._active_id is not None else "",
            )

    def delete(self, project_id: int) -> None:
        """Delete a project.  Active project shifts to the first remaining one."""
        self._by_id(project_id)  # raises if not found
        self._storage.delete_project(project_id)
        self._projects = [p for p in self._projects if p.project_id != project_id]
        if self._active_id == project_id:
            first = self._projects[0] if self._projects else None
            self._active_id = first.project_id if first else None
            self._storage.set_app_state(
                "active_project_id",
                str(self._active_id) if self._active_id is not None else "",
            )

    # ------------------------------------------------------------------
    # Active-project operations
    # ------------------------------------------------------------------

    def switch(self, project_id: int) -> Project:
        """Make *project_id* the active project and persist the choice."""
        project = self._by_id(project_id)
        self._active_id = project_id
        self._storage.set_app_state("active_project_id", str(project_id))
        return project

    def save_elapsed(self, elapsed_seconds: float) -> None:
        """Persist *elapsed_seconds* for the currently active project."""
        active = self.active_project
        if active is None:
            return
        active.elapsed_seconds = elapsed_seconds
        self._storage.save_project_elapsed(active.project_id, elapsed_seconds)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _by_id(self, project_id: int) -> Project:
        p = next((x for x in self._projects if x.project_id == project_id), None)
        if p is None:
            raise ValueError(f"Project {project_id} not found")
        return p

    def reload(self) -> None:
        """Re-read all projects from storage (e.g. after an import)."""
        self._projects = []
        self._active_id = None
        self._load()

    def _load(self) -> None:
        rows = self._storage.list_projects()
        self._projects = [
            Project(
                project_id=r["id"],
                name=r["name"],
                description=r["description"],
                elapsed_seconds=r["elapsed_seconds"],
                created_at=r["created_at"],
                ref_number=r.get("ref_number", ""),
                alias=r.get("alias", ""),
                color=r.get("color", ""),
                archived=r.get("archived", False),
                notes=r.get("notes", ""),
            )
            for r in rows
        ]
        if not self._projects:
            # First run: create a default project, migrating any saved timer state.
            saved = self._storage.load_timer_state()
            default_elapsed = (
                saved["elapsed_seconds"]
                if saved and saved["elapsed_seconds"] > 0
                else 0.0
            )
            default = self.add("Default", "")
            if default_elapsed > 0:
                self._storage.save_project_elapsed(default.project_id, default_elapsed)
                default.elapsed_seconds = default_elapsed
            self._active_id = default.project_id
            self._storage.set_app_state("active_project_id", str(default.project_id))
            return

        # Restore active project from persisted app state.
        active_str = self._storage.get_app_state("active_project_id")
        if active_str:
            try:
                candidate = int(active_str)
                self._active_id = (
                    candidate
                    if any(p.project_id == candidate for p in self._projects)
                    else self._projects[0].project_id
                )
            except ValueError:
                self._active_id = self._projects[0].project_id
        else:
            self._active_id = self._projects[0].project_id
