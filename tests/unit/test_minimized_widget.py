"""Unit tests for MinimizedWidget."""

from pathlib import Path
import tkinter as tk

import pytest

from src.projects import ProjectManager
from src.storage import Storage
from src.sub_activities import SubActivityManager
from src.timer import Timer
from src.ui.minimized_widget import MinimizedWidget
from src.ui.formatting import format_elapsed as _format_elapsed
from src.ui.themes import MATRIX

pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def root_tk():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def widget_env(tmp_path: Path):
    storage = Storage(tmp_path / "mini.db")
    pm = ProjectManager(storage)
    timer = Timer()
    calls = {"toggle": 0, "project": [], "sub": [], "maximize": []}

    def on_toggle():
        calls["toggle"] += 1

    def on_project(project_id: int):
        calls["project"].append(project_id)

    def on_sub(sub_id: int):
        calls["sub"].append(sub_id)

    def on_maximize(x: int, y: int):
        calls["maximize"].append((x, y))

    return storage, pm, timer, calls, on_toggle, on_project, on_sub, on_maximize


@pytest.fixture
def mini(root_tk, widget_env):
    storage, pm, timer, calls, on_toggle, on_project, on_sub, on_maximize = widget_env
    w = MinimizedWidget(
        parent=root_tk,
        timer=timer,
        project_mgr=pm,
        storage=storage,
        theme=MATRIX,
        on_toggle=on_toggle,
        on_project_switch=on_project,
        on_sub_switch=on_sub,
        on_maximize=on_maximize,
        start_x=10,
        start_y=20,
    )
    w._win.update_idletasks()
    yield w, storage, pm, timer, calls
    try:
        w.destroy()
    except Exception:
        pass


class TestMinimizedWidget:
    def test_format_elapsed(self):
        assert _format_elapsed(0) == "00:00:00"
        assert _format_elapsed(3661) == "01:01:01"
        assert _format_elapsed(-10) == "00:00:00"

    def test_refresh_display_running(self, mini):
        w, _s, _pm, timer, _calls = mini
        timer.start()
        w.refresh_display()
        assert w._toggle_btn["text"] == "\u25a0"
        timer.stop()

    def test_refresh_display_paused(self, mini):
        w, _s, _pm, timer, _calls = mini
        timer.start()
        timer.pause()
        w.refresh_display()
        assert w._toggle_btn["text"] == "\u25b6"
        timer.reset()

    def test_refresh_combos_populates_projects_and_activities(self, mini):
        w, storage, pm, _timer, _calls = mini
        p2 = pm.add("Mini P2", "")
        pm.switch(p2.project_id)
        sa_mgr = SubActivityManager(storage, p2.project_id)
        sa_mgr.add("Task 1")
        w.refresh_combos()
        assert "Mini P2" in w._project_combo["values"]
        assert "Task 1" in w._activity_combo["values"]

    def test_project_select_routes_to_callback(self, mini):
        w, _storage, pm, _timer, calls = mini
        p2 = pm.add("SwitchToMe", "")
        w.refresh_combos()
        w._project_combo.set("SwitchToMe")
        w._on_project_select(type("E", (), {})())
        assert p2.project_id in calls["project"]

    def test_activity_select_routes_project_level(self, mini):
        w, _storage, pm, _timer, calls = mini
        w.refresh_combos()
        w._activity_combo.set("")
        w._on_activity_select(type("E", (), {})())
        assert pm.active_project.project_id in calls["project"]

    def test_activity_select_routes_to_sub_activity(self, mini):
        w, storage, pm, _timer, calls = mini
        sa_mgr = SubActivityManager(storage, pm.active_project.project_id)
        sa = sa_mgr.add("Mini Sub")
        w.refresh_combos()
        w._activity_combo.set("Mini Sub")
        w._on_activity_select(type("E", (), {})())
        assert sa.sub_activity_id in calls["sub"]

    def test_toggle_clicked_invokes_callback(self, mini):
        w, _storage, _pm, _timer, calls = mini
        w._on_toggle_clicked()
        assert calls["toggle"] == 1

    def test_drag_motion_updates_coordinates(self, mini):
        w, _storage, _pm, _timer, _calls = mini
        w._drag_start(type("E", (), {"x_root": 10, "y_root": 20})())
        w._drag_motion(type("E", (), {"x_root": 20, "y_root": 35})())
        assert w._drag_x == 20
        assert w._drag_y == 35

    def test_maximize_invokes_callback_and_destroys(self, mini):
        w, _storage, _pm, _timer, calls = mini
        w._maximize()
        assert w._win is None
        assert len(calls["maximize"]) == 1
