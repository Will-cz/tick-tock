"""Pure helpers for widget panel/tab behavior decisions."""

from __future__ import annotations

from typing import Optional


def resolve_panel_tab_click(
    *,
    clicked_tab: str,
    current_tab: str,
    panel_collapsed: bool,
) -> tuple[Optional[bool], Optional[str]]:
    """Return collapse-change and tab-switch actions for a tab click.

    Returns ``(collapse_value, switch_tab)`` where either item may be ``None``
    to indicate no action.
    """
    if clicked_tab == current_tab and not panel_collapsed:
        return True, None
    if panel_collapsed:
        return False, clicked_tab
    return None, clicked_tab


def compute_panel_window_height(
    *,
    collapsed: bool,
    outer_frame_reqheight: Optional[int],
    window_h_projects: int,
    window_h_tree: int,
    outer_padding: int = 6,
) -> int:
    """Compute target window height after panel collapse/expand change."""
    if collapsed and outer_frame_reqheight is not None:
        return max(window_h_projects, outer_frame_reqheight + outer_padding)
    return window_h_tree


def resolve_panel_tab_label_colors(
    *,
    tab: str,
    fg: str,
    fg_dim: str,
) -> tuple[str, str]:
    """Return ``(sub_tab_fg, projects_tab_fg)`` for the active tab."""
    if tab == "sub_activities":
        return fg, fg_dim
    return fg_dim, fg
