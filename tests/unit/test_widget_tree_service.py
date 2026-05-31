from __future__ import annotations

from src.app.services.widget_tree_service import (
    TreeNodeEntry,
    build_project_tree_rows,
    build_sub_activity_tree_rows,
    resolve_main_tree_click_action,
    resolve_projects_tree_click_action,
    resolve_projects_tree_live_update,
    resolve_sub_activity_tree_live_update,
    resolve_tree_item_activation,
)
from src.projects import Project
from src.timer import TimerState


def test_build_sub_activity_tree_rows_filters_archived_and_marks_active() -> None:
    rows = build_sub_activity_tree_rows(
        sub_rows=[
            {"id": 1, "name": "A", "elapsed_seconds": 10.0, "archived": False},
            {"id": 2, "name": "B", "elapsed_seconds": 5.0, "archived": True},
        ],
        project_id=7,
        active_sub_activity_id=1,
        timer_state=TimerState.RUNNING,
        today_seconds_by_sub={1: 120.0},
        live_active_delta=3.0,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row.project_id == 7
    assert row.sub_activity_id == 1
    assert row.elapsed_seconds == 123.0
    assert row.tag == "active_sub"
    assert row.action == "\u23f8"


def test_build_sub_activity_tree_rows_inactive_uses_play_symbol() -> None:
    rows = build_sub_activity_tree_rows(
        sub_rows=[{"id": 3, "name": "C", "elapsed_seconds": 2.0, "archived": False}],
        project_id=8,
        active_sub_activity_id=None,
        timer_state=TimerState.PAUSED,
        today_seconds_by_sub={3: 50.0},
    )

    assert len(rows) == 1
    assert rows[0].tag == "sub"
    assert rows[0].action == "\u25b6"
    assert rows[0].elapsed_seconds == 50.0


def test_build_project_tree_rows_active_project_uses_today_plus_live() -> None:
    projects = [
        Project(1, "P1", "", 10.0, "now"),
        Project(2, "P2", "", 20.0, "now"),
    ]
    rows = build_project_tree_rows(
        projects=projects,
        active_project_id=1,
        active_sub_activity_id=None,
        timer_state=TimerState.RUNNING,
        today_seconds_by_project={1: 100.0, 2: 75.0},
        live_active_delta=5.0,
    )

    assert len(rows) == 2
    active = next(r for r in rows if r.project_id == 1)
    other = next(r for r in rows if r.project_id == 2)
    assert active.elapsed_seconds == 105.0
    assert other.elapsed_seconds == 75.0
    assert active.tag == "active_proj"
    assert active.action == "\u23f8"


def test_build_project_tree_rows_active_sub_still_adds_live_to_project() -> None:
    projects = [
        Project(1, "P1", "", 10.0, "now"),
    ]
    rows = build_project_tree_rows(
        projects=projects,
        active_project_id=1,
        active_sub_activity_id=11,
        timer_state=TimerState.RUNNING,
        today_seconds_by_project={1: 40.0},
        live_active_delta=2.5,
    )

    assert len(rows) == 1
    assert rows[0].elapsed_seconds == 42.5
    assert rows[0].action == "\u23f8"


def test_build_project_tree_rows_skips_archived() -> None:
    projects = [
        Project(1, "P1", "", 10.0, "now", archived=True),
        Project(2, "P2", "", 20.0, "now", alias="Alias"),
    ]
    rows = build_project_tree_rows(
        projects=projects,
        active_project_id=2,
        active_sub_activity_id=None,
        timer_state=TimerState.PAUSED,
        today_seconds_by_project={2: 60.0},
    )

    assert len(rows) == 1
    assert rows[0].project_id == 2
    assert rows[0].label == "Alias"
    assert rows[0].elapsed_seconds == 60.0
    assert rows[0].action == "\u25b6"


def test_resolve_projects_tree_click_action_ignores_non_action_column() -> None:
    action, project_id = resolve_projects_tree_click_action(
        clicked_column="#2",
        clicked_item_iid="iid-1",
        project_tree_iids={1: "iid-1"},
        active_project_id=1,
        active_sub_activity_id=None,
    )
    assert action == "ignore"
    assert project_id is None


def test_resolve_projects_tree_click_action_toggles_active_project() -> None:
    action, project_id = resolve_projects_tree_click_action(
        clicked_column="#3",
        clicked_item_iid="iid-1",
        project_tree_iids={1: "iid-1"},
        active_project_id=1,
        active_sub_activity_id=None,
    )
    assert action == "toggle"
    assert project_id == 1


def test_resolve_projects_tree_click_action_switches_when_sub_active() -> None:
    action, project_id = resolve_projects_tree_click_action(
        clicked_column="#3",
        clicked_item_iid="iid-1",
        project_tree_iids={1: "iid-1"},
        active_project_id=1,
        active_sub_activity_id=99,
    )
    assert action == "switch"
    assert project_id == 1


def test_resolve_projects_tree_click_action_switches_other_project() -> None:
    action, project_id = resolve_projects_tree_click_action(
        clicked_column="#3",
        clicked_item_iid="iid-2",
        project_tree_iids={1: "iid-1", 2: "iid-2"},
        active_project_id=1,
        active_sub_activity_id=None,
    )
    assert action == "switch"
    assert project_id == 2


def test_resolve_projects_tree_live_update_ignores_non_projects_tab() -> None:
    update = resolve_projects_tree_live_update(
        panel_tab="sub_activities",
        project_tree_iids={1: "iid-1"},
        active_project_id=1,
        timer_state=TimerState.RUNNING,
        today_base_seconds=10.0,
        live_active_delta=2.0,
    )
    assert update is None


def test_resolve_projects_tree_live_update_ignores_missing_iid() -> None:
    update = resolve_projects_tree_live_update(
        panel_tab="projects",
        project_tree_iids={2: "iid-2"},
        active_project_id=1,
        timer_state=TimerState.RUNNING,
        today_base_seconds=10.0,
        live_active_delta=2.0,
    )
    assert update is None


def test_resolve_projects_tree_live_update_returns_pause_action_when_running() -> None:
    update = resolve_projects_tree_live_update(
        panel_tab="projects",
        project_tree_iids={1: "iid-1"},
        active_project_id=1,
        timer_state=TimerState.RUNNING,
        today_base_seconds=10.0,
        live_active_delta=2.0,
    )
    assert update is not None
    assert update.iid == "iid-1"
    assert update.elapsed_seconds == 12.0
    assert update.action == "\u23f8"


def test_resolve_projects_tree_live_update_returns_play_action_when_paused() -> None:
    update = resolve_projects_tree_live_update(
        panel_tab="projects",
        project_tree_iids={1: "iid-1"},
        active_project_id=1,
        timer_state=TimerState.PAUSED,
        today_base_seconds=12.0,
        live_active_delta=0.0,
    )
    assert update is not None
    assert update.action == "\u25b6"


def test_resolve_sub_activity_tree_live_update_missing_active_returns_none() -> None:
    update = resolve_sub_activity_tree_live_update(
        sub_tree_iids={1: "sa-1"},
        active_sub_activity_id=None,
        timer_state=TimerState.RUNNING,
        today_base_seconds=10.0,
        live_active_delta=0.0,
    )
    assert update is None


def test_resolve_sub_activity_tree_live_update_returns_pause_when_running() -> None:
    update = resolve_sub_activity_tree_live_update(
        sub_tree_iids={1: "sa-1"},
        active_sub_activity_id=1,
        timer_state=TimerState.RUNNING,
        today_base_seconds=8.0,
        live_active_delta=2.0,
    )
    assert update is not None
    assert update.iid == "sa-1"
    assert update.elapsed_seconds == 10.0
    assert update.action == "\u23f8"


def test_resolve_main_tree_click_action_ignores_non_action_column() -> None:
    resolution = resolve_main_tree_click_action(
        clicked_column="#2",
        clicked_item_iid="row-1",
        tree_node_map={"row-1": TreeNodeEntry(kind="sub", node_id=11, project_id=3)},
        active_project_id=3,
        active_sub_activity_id=11,
        timer_state=TimerState.RUNNING,
        has_project_manager=True,
    )

    assert resolution.action == "ignore"


def test_resolve_main_tree_click_action_toggles_active_sub_when_paused() -> None:
    resolution = resolve_main_tree_click_action(
        clicked_column="#3",
        clicked_item_iid="row-1",
        tree_node_map={"row-1": TreeNodeEntry(kind="sub", node_id=11, project_id=3)},
        active_project_id=3,
        active_sub_activity_id=11,
        timer_state=TimerState.PAUSED,
        has_project_manager=True,
    )

    assert resolution.action == "toggle"


def test_resolve_main_tree_click_action_selects_project_when_sub_running() -> None:
    resolution = resolve_main_tree_click_action(
        clicked_column="#3",
        clicked_item_iid="row-1",
        tree_node_map={"row-1": TreeNodeEntry(kind="sub", node_id=11, project_id=7)},
        active_project_id=7,
        active_sub_activity_id=11,
        timer_state=TimerState.RUNNING,
        has_project_manager=True,
    )

    assert resolution.action == "select_project"
    assert resolution.project_id == 7


def test_resolve_main_tree_click_action_activates_for_new_target() -> None:
    resolution = resolve_main_tree_click_action(
        clicked_column="#3",
        clicked_item_iid="row-1",
        tree_node_map={"row-1": TreeNodeEntry(kind="sub", node_id=12, project_id=7)},
        active_project_id=7,
        active_sub_activity_id=11,
        timer_state=TimerState.PAUSED,
        has_project_manager=True,
    )

    assert resolution.action == "activate"
    assert resolution.activate_iid == "row-1"
    assert resolution.auto_toggle is True


def test_resolve_tree_item_activation_ignores_missing_item() -> None:
    plan = resolve_tree_item_activation(
        item_iid="missing",
        tree_node_map={"row-1": TreeNodeEntry(kind="sub", node_id=11, project_id=3)},
        active_project_id=3,
        active_sub_activity_id=11,
    )

    assert plan.action == "ignore"


def test_resolve_tree_item_activation_selects_project_from_project_row() -> None:
    plan = resolve_tree_item_activation(
        item_iid="proj-2",
        tree_node_map={"proj-2": TreeNodeEntry(kind="project", node_id=2)},
        active_project_id=1,
        active_sub_activity_id=None,
    )

    assert plan.action == "select_project"
    assert plan.project_id == 2


def test_resolve_tree_item_activation_switches_then_selects_sub() -> None:
    plan = resolve_tree_item_activation(
        item_iid="sub-9",
        tree_node_map={"sub-9": TreeNodeEntry(kind="sub", node_id=9, project_id=2)},
        active_project_id=1,
        active_sub_activity_id=None,
    )

    assert plan.action == "switch_then_select_sub"
    assert plan.project_id == 2
    assert plan.sub_activity_id == 9


def test_resolve_tree_item_activation_selects_sub_when_project_matches() -> None:
    plan = resolve_tree_item_activation(
        item_iid="sub-9",
        tree_node_map={"sub-9": TreeNodeEntry(kind="sub", node_id=9, project_id=2)},
        active_project_id=2,
        active_sub_activity_id=None,
    )

    assert plan.action == "select_sub"
    assert plan.sub_activity_id == 9
