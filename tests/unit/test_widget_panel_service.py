from src.app.services.widget_panel_service import (
    compute_panel_window_height,
    resolve_panel_tab_click,
    resolve_panel_tab_label_colors,
)


def test_resolve_panel_tab_click_active_tab_collapses_panel() -> None:
    collapse_value, switch_tab = resolve_panel_tab_click(
        clicked_tab="sub_activities",
        current_tab="sub_activities",
        panel_collapsed=False,
    )
    assert collapse_value is True
    assert switch_tab is None


def test_resolve_panel_tab_click_when_collapsed_expands_and_switches() -> None:
    collapse_value, switch_tab = resolve_panel_tab_click(
        clicked_tab="projects",
        current_tab="sub_activities",
        panel_collapsed=True,
    )
    assert collapse_value is False
    assert switch_tab == "projects"


def test_compute_panel_window_height_collapsed_uses_visible_content_height() -> None:
    new_h = compute_panel_window_height(
        collapsed=True,
        outer_frame_reqheight=210,
        window_h_projects=180,
        window_h_tree=500,
    )
    assert new_h == 216


def test_compute_panel_window_height_uses_projects_floor_when_collapsed() -> None:
    new_h = compute_panel_window_height(
        collapsed=True,
        outer_frame_reqheight=100,
        window_h_projects=180,
        window_h_tree=500,
    )
    assert new_h == 180


def test_resolve_panel_tab_label_colors_marks_active_tab() -> None:
    sub_fg, proj_fg = resolve_panel_tab_label_colors(
        tab="projects",
        fg="#ffffff",
        fg_dim="#999999",
    )
    assert sub_fg == "#999999"
    assert proj_fg == "#ffffff"
