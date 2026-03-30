from src.app.services.widget_project_selector_service import (
    build_project_selector_state,
    resolve_selected_project_id,
)
from src.projects import Project


def test_build_project_selector_state_filters_archived_and_prefers_alias() -> None:
    state = build_project_selector_state(
        projects=[
            Project(1, "Default", "", 0.0, "now", alias="DEF"),
            Project(2, "Archived", "", 0.0, "now", archived=True),
        ],
        active_project=Project(1, "Default", "", 0.0, "now", alias="DEF"),
        fallback_title_color="#00AA00",
    )
    assert state.labels == ["DEF"]
    assert state.active_label == "DEF"


def test_build_project_selector_state_active_color_prefers_project_color() -> None:
    active = Project(1, "Default", "", 0.0, "now", color="#FF0000")
    state = build_project_selector_state(
        projects=[active],
        active_project=active,
        fallback_title_color="#00AA00",
    )
    assert state.title_color == "#FF0000"


def test_build_project_selector_state_without_active_uses_defaults() -> None:
    state = build_project_selector_state(
        projects=[],
        active_project=None,
        fallback_title_color="#00AA00",
    )
    assert state.labels == []
    assert state.active_label == "(no project)"
    assert state.title_color == "#00AA00"


def test_resolve_selected_project_id_matches_visible_alias() -> None:
    project_id = resolve_selected_project_id(
        selected_label="DEF",
        projects=[
            Project(1, "Default", "", 0.0, "now", alias="DEF"),
            Project(2, "Archived", "", 0.0, "now", alias="ARC", archived=True),
        ],
    )

    assert project_id == 1


def test_resolve_selected_project_id_returns_none_for_archived_match_only() -> None:
    project_id = resolve_selected_project_id(
        selected_label="ARC",
        projects=[
            Project(1, "Default", "", 0.0, "now", alias="DEF"),
            Project(2, "Archived", "", 0.0, "now", alias="ARC", archived=True),
        ],
    )

    assert project_id is None
