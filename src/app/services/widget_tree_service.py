"""View-model helpers for Tick-Tock widget tree rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional

from src.projects import Project
from src.timer import TimerState

_ACTION_PLAY = "\u25b6"
_ACTION_PAUSE = "\u23f8"


def _coerce_int(value: object, default: int = 0) -> int:
    """Best-effort int coercion for storage/UI payload values."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _coerce_float(value: object, default: float = 0.0) -> float:
    """Best-effort float coercion for storage/UI payload values."""
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float, str)):
        try:
            return float(value)
        except ValueError:
            return default
    return default


@dataclass(frozen=True)
class SubActivityTreeRow:
    """Normalized sub-activity row data for tree rendering."""

    sub_activity_id: int
    project_id: int
    name: str
    elapsed_seconds: float
    tag: str
    action: str


@dataclass(frozen=True)
class ProjectTreeRow:
    """Normalized project row data for tree rendering."""

    project_id: int
    label: str
    elapsed_seconds: float
    tag: str
    action: str


@dataclass(frozen=True)
class ProjectTreeLiveUpdate:
    """Live update payload for a single project row."""

    iid: str
    elapsed_seconds: float
    action: str


@dataclass(frozen=True)
class SubActivityTreeLiveUpdate:
    """Live update payload for a single sub-activity row."""

    iid: str
    elapsed_seconds: float
    action: str


@dataclass(frozen=True)
class TreeClickResolution:
    """Resolved action from a tree click interaction."""

    action: str
    project_id: Optional[int] = None
    activate_iid: Optional[str] = None
    auto_toggle: bool = False


@dataclass(frozen=True)
class TreeActivationPlan:
    """Activation target produced by keyboard/tree interactions."""

    action: str
    project_id: Optional[int] = None
    sub_activity_id: Optional[int] = None


@dataclass(frozen=True)
class TreeNodeEntry:
    """Node metadata stored for reverse lookup from tree iid."""

    kind: str
    node_id: int
    project_id: Optional[int] = None


def build_sub_activity_tree_rows(
    *,
    sub_rows: Iterable[Mapping[str, object]],
    project_id: int,
    active_sub_activity_id: Optional[int],
    timer_state: TimerState,
) -> list[SubActivityTreeRow]:
    """Build sub-activity tree rows with active/playing visual state."""
    timer_running = timer_state == TimerState.RUNNING
    rows: list[SubActivityTreeRow] = []

    for raw in sub_rows:
        if bool(raw.get("archived", False)):
            continue
        sub_activity_id = _coerce_int(raw.get("id", 0), default=0)
        is_active = active_sub_activity_id == sub_activity_id
        rows.append(
            SubActivityTreeRow(
                sub_activity_id=sub_activity_id,
                project_id=project_id,
                name=str(raw.get("name", "")),
                elapsed_seconds=_coerce_float(raw.get("elapsed_seconds", 0.0)),
                tag="active_sub" if is_active else "sub",
                action=_ACTION_PAUSE if (is_active and timer_running) else _ACTION_PLAY,
            )
        )

    return rows


def build_project_tree_rows(
    *,
    projects: Iterable[Project],
    active_project_id: Optional[int],
    active_sub_activity_id: Optional[int],
    timer_state: TimerState,
    timer_elapsed: float,
) -> list[ProjectTreeRow]:
    """Build project tree rows with active/playing visual state."""
    rows: list[ProjectTreeRow] = []

    for project in projects:
        if project.archived:
            continue
        is_active = project.project_id == active_project_id
        if is_active and active_sub_activity_id is None:
            elapsed = timer_elapsed
        else:
            elapsed = project.elapsed_seconds
        timer_running = is_active and timer_state == TimerState.RUNNING
        rows.append(
            ProjectTreeRow(
                project_id=project.project_id,
                label=project.alias if project.alias else project.name,
                elapsed_seconds=elapsed,
                tag="active_proj" if is_active else "proj",
                action=_ACTION_PAUSE if timer_running else _ACTION_PLAY,
            )
        )

    return rows


def resolve_projects_tree_click_action(
    *,
    clicked_column: str,
    clicked_item_iid: str,
    project_tree_iids: Mapping[int, str],
    active_project_id: Optional[int],
    active_sub_activity_id: Optional[int],
) -> tuple[str, Optional[int]]:
    """Resolve action intent for a projects tree click.

    Returns ``("ignore", None)``, ``("toggle", project_id)``, or
    ``("switch", project_id)``.
    """
    if clicked_column != "#3" or not clicked_item_iid:
        return "ignore", None

    project_id = next(
        (pid for pid, iid in project_tree_iids.items() if iid == clicked_item_iid),
        None,
    )
    if project_id is None:
        return "ignore", None

    if active_project_id == project_id and active_sub_activity_id is None:
        return "toggle", project_id

    return "switch", project_id


def resolve_projects_tree_live_update(
    *,
    panel_tab: str,
    project_tree_iids: Mapping[int, str],
    active_project_id: Optional[int],
    timer_state: TimerState,
    timer_elapsed: float,
) -> Optional[ProjectTreeLiveUpdate]:
    """Resolve live update payload for the active project row, if any."""
    if panel_tab != "projects" or active_project_id is None:
        return None

    iid = project_tree_iids.get(active_project_id)
    if iid is None:
        return None

    return ProjectTreeLiveUpdate(
        iid=iid,
        elapsed_seconds=timer_elapsed,
        action=_ACTION_PAUSE if timer_state == TimerState.RUNNING else _ACTION_PLAY,
    )


def resolve_sub_activity_tree_live_update(
    *,
    sub_tree_iids: Mapping[int, str],
    active_sub_activity_id: Optional[int],
    timer_state: TimerState,
    timer_elapsed: float,
) -> Optional[SubActivityTreeLiveUpdate]:
    """Resolve live update payload for the active sub-activity row, if any."""
    if active_sub_activity_id is None:
        return None

    iid = sub_tree_iids.get(active_sub_activity_id)
    if iid is None:
        return None

    return SubActivityTreeLiveUpdate(
        iid=iid,
        elapsed_seconds=timer_elapsed,
        action=_ACTION_PAUSE if timer_state == TimerState.RUNNING else _ACTION_PLAY,
    )


def resolve_main_tree_click_action(
    *,
    clicked_column: str,
    clicked_item_iid: str,
    tree_node_map: Mapping[str, TreeNodeEntry],
    active_project_id: Optional[int],
    active_sub_activity_id: Optional[int],
    timer_state: TimerState,
    has_project_manager: bool,
) -> TreeClickResolution:
    """Resolve action intent for action-column clicks in the main tree."""
    if clicked_column != "#3":
        return TreeClickResolution(action="ignore")

    entry = tree_node_map.get(clicked_item_iid)
    if entry is None:
        return TreeClickResolution(action="ignore")

    kind = entry.kind
    if kind == "project" and has_project_manager:
        project_id = _coerce_int(entry.node_id, default=-1)
        if (
            project_id >= 0
            and active_project_id == project_id
            and active_sub_activity_id is None
        ):
            return TreeClickResolution(action="toggle")
        return TreeClickResolution(
            action="activate",
            activate_iid=clicked_item_iid,
            auto_toggle=(timer_state != TimerState.RUNNING),
        )

    if kind == "sub":
        sub_id = _coerce_int(entry.node_id, default=-1)
        project_id = _coerce_int(entry.project_id, default=-1)
        if sub_id >= 0 and sub_id == active_sub_activity_id:
            if timer_state == TimerState.RUNNING and project_id >= 0:
                return TreeClickResolution(
                    action="select_project",
                    project_id=project_id,
                )
            return TreeClickResolution(action="toggle")
        return TreeClickResolution(
            action="activate",
            activate_iid=clicked_item_iid,
            auto_toggle=(timer_state != TimerState.RUNNING),
        )

    return TreeClickResolution(
        action="activate",
        activate_iid=clicked_item_iid,
        auto_toggle=(timer_state != TimerState.RUNNING),
    )


def resolve_tree_item_activation(
    *,
    item_iid: str,
    tree_node_map: Mapping[str, TreeNodeEntry],
    active_project_id: Optional[int],
    active_sub_activity_id: Optional[int],
) -> TreeActivationPlan:
    """Resolve activation plan for a tree node selection."""
    if not item_iid:
        return TreeActivationPlan(action="ignore")

    entry = tree_node_map.get(item_iid)
    if entry is None:
        return TreeActivationPlan(action="ignore")

    kind = entry.kind
    if kind == "project":
        project_id = _coerce_int(entry.node_id, default=-1)
        if project_id < 0:
            return TreeActivationPlan(action="ignore")
        if active_project_id == project_id and active_sub_activity_id is None:
            return TreeActivationPlan(action="ignore")
        return TreeActivationPlan(action="select_project", project_id=project_id)

    if kind == "sub":
        sub_id = _coerce_int(entry.node_id, default=-1)
        project_id = _coerce_int(entry.project_id, default=-1)
        if sub_id < 0 or project_id < 0:
            return TreeActivationPlan(action="ignore")
        if sub_id == active_sub_activity_id:
            return TreeActivationPlan(action="ignore")
        if active_project_id is None or active_project_id != project_id:
            return TreeActivationPlan(
                action="switch_then_select_sub",
                project_id=project_id,
                sub_activity_id=sub_id,
            )
        return TreeActivationPlan(action="select_sub", sub_activity_id=sub_id)

    return TreeActivationPlan(action="ignore")
