"""View-model helpers for widget project selector display state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from src.projects import Project


@dataclass(frozen=True)
class ProjectSelectorState:
    """Computed UI state for project combobox and title color."""

    labels: list[str]
    active_label: str
    title_color: str


def _project_label(project: Project) -> str:
    """Return the visible label text for a project."""
    return project.alias if project.alias else project.name


def build_project_selector_state(
    *,
    projects: Iterable[Project],
    active_project: Optional[Project],
    fallback_title_color: str,
    empty_label: str = "(no project)",
) -> ProjectSelectorState:
    """Build combobox labels, selected label, and title icon color."""
    visible_projects = [p for p in projects if not p.archived]
    labels = [_project_label(p) for p in visible_projects]

    if active_project is not None:
        active_label = _project_label(active_project)
        title_color = (
            active_project.color if active_project.color else fallback_title_color
        )
    else:
        active_label = empty_label
        title_color = fallback_title_color

    return ProjectSelectorState(
        labels=labels,
        active_label=active_label,
        title_color=title_color,
    )


def resolve_selected_project_id(
    *,
    selected_label: str,
    projects: Iterable[Project],
) -> Optional[int]:
    """Resolve selected combobox label to a visible project id."""
    for project in projects:
        if project.archived:
            continue
        if _project_label(project) == selected_label:
            return project.project_id
    return None
