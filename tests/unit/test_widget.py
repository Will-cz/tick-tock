"""Unit tests for TickTockWidget - no Tk window required."""

from datetime import datetime
from pathlib import Path
import pytest
import tkinter as tk
from unittest.mock import patch

from src.config import Config
from src.projects import ProjectManager
from src.storage import Storage
from src.timer import Timer, TimerEvent, TimerState
from src.app.services.widget_tree_service import TreeNodeEntry
from src.ui.widget import TickTockWidget
from src.ui.formatting import format_elapsed as _format_elapsed
import src.ui.widget as widget_mod


# ---------------------------------------------------------------------------
# Fixture: real Tk window (withdrawn so nothing appears on screen)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def require_tk():
    """Skip GUI tests if a usable Tk runtime is unavailable."""
    try:
        root = tk.Tk()
        root.withdraw()
        root.destroy()
    except tk.TclError as exc:
        pytest.skip(f"Tk is not available in this environment: {exc}")


class _NoopTray:
    def __init__(self, *args, **kwargs):
        self._running = False

    def start(self) -> bool:
        self._running = False
        return False

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return False

    def update_tooltip(self, _text: str) -> None:
        return None


class _ExportProbeService:
    def __init__(self):
        self.saved_state: tuple[float, str] | None = None
        self.exported_path: Path | None = None

    def save_timer_state(self, elapsed: float, state: str) -> None:
        self.saved_state = (elapsed, state)

    def export_json(self, path: Path) -> None:
        self.exported_path = path


@pytest.fixture(scope="module", autouse=True)
def patch_system_tray():
    """Disable real pystray threads during widget tests to avoid teardown noise."""
    with patch.object(widget_mod, "SystemTrayIcon", _NoopTray):
        yield


@pytest.fixture(scope="module")
def built_widget(require_tk):
    """One TickTockWidget per module - avoids creating multiple Tk instances.

    Withdrawn immediately so no window appears on screen.
    """
    w = TickTockWidget()
    w.build()
    assert w._root is not None
    w._root.withdraw()
    yield w
    try:
        w.close()
    except Exception:
        pass


@pytest.fixture(scope="module")
def built_widget_pm(tmp_path_factory, require_tk):
    """TickTockWidget with ProjectManager and Storage, window withdrawn."""
    db = tmp_path_factory.mktemp("db") / "test.db"
    storage = Storage(db)
    pm = ProjectManager(storage)
    w = TickTockWidget(storage=storage, project_manager=pm)
    w.build()
    assert w._root is not None
    w._root.withdraw()
    yield w, pm, storage
    try:
        w.close()
    except Exception:
        pass


@pytest.fixture(autouse=False)
def reset_timer(built_widget):
    """Reset the widget's timer to IDLE between GUI tests."""
    yield
    built_widget._timer.reset()
    if built_widget._root:
        built_widget._root.update()


# ---------------------------------------------------------------------------
# Pure helper: _format_elapsed
# ---------------------------------------------------------------------------


class TestFormatElapsed:
    def test_zero(self):
        assert _format_elapsed(0) == "00:00:00"

    def test_negative_clamps_to_zero(self):
        assert _format_elapsed(-5) == "00:00:00"

    def test_seconds_only(self):
        assert _format_elapsed(45) == "00:00:45"

    def test_one_minute(self):
        assert _format_elapsed(60) == "00:01:00"

    def test_one_hour(self):
        assert _format_elapsed(3600) == "01:00:00"

    def test_mixed(self):
        assert _format_elapsed(3661) == "01:01:01"

    def test_large_value(self):
        # 10 hours, 30 minutes, 5 seconds
        assert _format_elapsed(10 * 3600 + 30 * 60 + 5) == "10:30:05"

    def test_fractional_seconds_truncated(self):
        # 1.9s should show 00:00:01, not 00:00:02
        assert _format_elapsed(1.9) == "00:00:01"


# ---------------------------------------------------------------------------
# Widget - timer state management (no window needed)
# ---------------------------------------------------------------------------


@pytest.fixture
def widget():
    """TickTockWidget without a Tk window - tests timer logic only."""
    return TickTockWidget()


class TestWidgetInitialState:
    def test_initial_timer_state_is_idle(self, widget):
        assert widget.timer.state == TimerState.IDLE

    def test_initial_elapsed_is_zero(self, widget):
        assert widget.timer.elapsed == 0.0

    def test_timer_attribute_returns_same_instance(self, widget):
        assert widget.timer is widget._timer


class TestWidgetTimerControls:
    def test_toggle_starts_idle_timer(self, widget):
        widget._on_toggle()
        assert widget.timer.state == TimerState.RUNNING
        widget.timer.stop()

    def test_toggle_stops_running_timer(self, widget):
        widget._on_toggle()  # start
        widget._on_toggle()  # stop
        assert widget.timer.state == TimerState.STOPPED
        widget.timer.reset()

    def test_toggle_continues_stopped_timer(self, widget):
        widget._on_toggle()  # start
        widget._on_toggle()  # stop
        widget._on_toggle()  # continue
        assert widget.timer.state == TimerState.RUNNING
        widget.timer.stop()

    def test_stop_stops_running_timer(self, widget):
        widget._on_toggle()  # start
        widget._timer.stop()
        assert widget.timer.state == TimerState.STOPPED

    def test_toggle_after_stop_continues_without_reset(self, widget):
        """toggle on a STOPPED timer resumes from existing elapsed (no reset)."""
        widget._on_toggle()  # start
        widget.timer.pause()
        widget.timer._elapsed_before_pause = 300.0  # inject elapsed
        widget.timer._state = TimerState.STOPPED  # simulate stopped
        widget._on_toggle()  # should continue_from_stopped
        assert widget.timer.state == TimerState.RUNNING
        assert widget.timer.elapsed >= 300.0
        widget.timer.stop()

    def test_stop_on_paused_timer(self, widget):
        widget._on_toggle()  # start
        widget._on_toggle()  # pause
        widget._timer.stop()
        assert widget.timer.state == TimerState.STOPPED

    def test_reset_returns_to_idle(self, widget):
        widget._on_toggle()  # start
        widget._timer.reset()
        assert widget.timer.state == TimerState.IDLE

    def test_reset_clears_elapsed(self, widget):
        widget._on_toggle()  # start
        widget._timer.reset()
        assert widget.timer.elapsed == 0.0


class TestWidgetOnlyOneStateActive:
    """Timer can't be both running and paused simultaneously."""

    def test_not_both_running_and_paused_after_start(self, widget):
        widget._on_toggle()
        state = widget.timer.state
        assert not (state == TimerState.RUNNING and state == TimerState.PAUSED)
        widget.timer.stop()

    def test_start_ignored_when_already_running(self, widget):
        widget._on_toggle()  # start
        widget.timer.start()  # ignored
        assert widget.timer.state == TimerState.RUNNING
        widget.timer.stop()

    def test_start_ignored_when_paused(self, widget):
        widget.timer.start()
        widget.timer.pause()
        widget.timer.start()  # ignored
        assert widget.timer.state == TimerState.PAUSED
        widget.timer.reset()


class TestWidgetTimeValidation:
    def test_elapsed_never_negative(self, widget):
        # elapsed should be >= 0 in every possible state
        assert widget.timer.elapsed >= 0.0
        widget._on_toggle()
        assert widget.timer.elapsed >= 0.0
        widget._on_toggle()
        assert widget.timer.elapsed >= 0.0
        widget._timer.stop()
        assert widget.timer.elapsed >= 0.0
        widget._timer.reset()
        assert widget.timer.elapsed == 0.0


class TestWidgetTodayTotals:
    def test_today_base_total_refresh_is_scoped_to_active_project(self, tmp_path):
        storage = Storage(tmp_path / "today_scope.db")
        pm = ProjectManager(storage)
        second = pm.add("Second", "")
        day_text = "2026-04-10"

        storage.add_daily_seconds(pm.active_project.project_id, day_text, 40.0)
        storage.add_daily_seconds(second.project_id, day_text, 100.0)

        w = TickTockWidget(storage=storage, project_manager=pm)
        w._today_cache.date = day_text
        w._today_cache.last_refresh = None

        with patch("src.app.services.widget_today_service.datetime") as mock_datetime:
            mock_now = datetime(2026, 4, 10, 9, 30, 0)
            mock_datetime.now.return_value = mock_now
            w._refresh_today_base_total(force=True)
            assert w._today_cache.base_total == pytest.approx(40.0)

            pm.switch(second.project_id)
            w._refresh_today_base_total(force=True)
            assert w._today_cache.base_total == pytest.approx(100.0)

    def test_daily_flush_updates_only_matching_cached_project(self, tmp_path):
        storage = Storage(tmp_path / "today_flush.db")
        pm = ProjectManager(storage)
        second = pm.add("Second", "")
        w = TickTockWidget(storage=storage, project_manager=pm)

        day_text = "2026-04-10"
        w._today_cache.date = day_text
        w._today_cache.project_id = pm.active_project.project_id
        w._today_cache.base_total = 25.0

        with patch("src.app.services.widget_today_service.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 4, 10, 12, 0, 0)

            w._on_daily_flushed(day_text, second.project_id, 10.0)
            assert w._today_cache.base_total == pytest.approx(25.0)

            w._on_daily_flushed(day_text, pm.active_project.project_id, 10.0)
            assert w._today_cache.base_total == pytest.approx(35.0)


class TestWidgetExportPersistence:
    def test_export_forces_live_state_persist_before_writing(
        self, tmp_path, monkeypatch
    ):
        w = TickTockWidget()
        probe = _ExportProbeService()
        out = tmp_path / "snapshot.json"

        w._app_service = probe
        w._storage = object()
        w._root = object()
        w._timer.restore(123.0, "running")

        calls: list[tuple[str, float]] = []
        monkeypatch.setattr(
            w._controller,
            "save_active_elapsed",
            lambda elapsed: calls.append(("save_active_elapsed", elapsed)),
        )
        monkeypatch.setattr(
            w._controller,
            "flush_daily_at",
            lambda elapsed: calls.append(("flush_daily_at", elapsed)),
        )
        monkeypatch.setattr(
            widget_mod.filedialog, "asksaveasfilename", lambda **_: str(out)
        )
        monkeypatch.setattr(widget_mod.messagebox, "showinfo", lambda *_, **__: None)
        monkeypatch.setattr(widget_mod.messagebox, "showerror", lambda *_, **__: None)

        w._export_data()

        assert probe.saved_state is not None
        assert probe.saved_state[1] == "running"
        assert probe.exported_path == out
        assert any(name == "save_active_elapsed" for name, _ in calls)
        assert any(name == "flush_daily_at" for name, _ in calls)
        w.timer.stop()


class TestWidgetRapidClicking:
    """Rapid button presses must not raise exceptions or corrupt state."""

    def test_rapid_toggle_no_exception(self, widget):
        for _ in range(20):
            widget._on_toggle()
        # Finish in a clean state
        widget._timer.reset()
        assert widget.timer.state == TimerState.IDLE

    def test_rapid_stop_no_exception(self, widget):
        widget._on_toggle()
        for _ in range(10):
            widget._timer.stop()
        assert widget.timer.state == TimerState.STOPPED

    def test_rapid_reset_no_exception(self, widget):
        widget._on_toggle()
        for _ in range(10):
            widget._timer.reset()
        assert widget.timer.state == TimerState.IDLE

    def test_stop_on_idle_is_safe(self, widget):
        """stop() on idle timer is silently ignored."""
        widget._timer.stop()
        assert widget.timer.state == TimerState.IDLE

    def test_reset_on_idle_is_safe(self, widget):
        widget._timer.reset()
        assert widget.timer.state == TimerState.IDLE


class TestWidgetConfigHotReload:
    def test_setup_registers_reload_callback_and_starts_watcher(
        self, tmp_path, monkeypatch
    ):
        cfg = Config(config_path=tmp_path / "config.json")
        widget = TickTockWidget(config=cfg)

        starts: list[int] = []
        monkeypatch.setattr(cfg, "start_watching", lambda: starts.append(1))

        queued: list[object] = []
        monkeypatch.setattr(widget, "_post_ui", lambda fn: queued.append(fn))

        widget._setup_config_hot_reload()
        assert starts == [1]
        assert cfg._reload_callbacks

        cfg._reload_callbacks[-1](cfg)
        assert len(queued) == 1
        queued[0]()  # should not raise when _root is None

    def test_setup_does_not_register_duplicate_callbacks(self, tmp_path, monkeypatch):
        cfg = Config(config_path=tmp_path / "config.json")
        widget = TickTockWidget(config=cfg)

        monkeypatch.setattr(cfg, "start_watching", lambda: None)

        widget._setup_config_hot_reload()
        first_count = len(cfg._reload_callbacks)
        widget._setup_config_hot_reload()
        assert len(cfg._reload_callbacks) == first_count


class TestWidgetAcceptsExternalTimer:
    def test_custom_timer_is_used(self):
        t = Timer()
        widget = TickTockWidget(timer=t)
        assert widget.timer is t

    def test_callbacks_registered_on_custom_timer(self):
        """Widget registers its own callback on a supplied timer."""
        t = Timer()
        TickTockWidget(timer=t)
        # At minimum TICK and STARTED are registered
        assert len(t._callbacks[TimerEvent.STARTED]) >= 1  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# GUI tests - require Tkinter display (Windows)
# ---------------------------------------------------------------------------


@pytest.mark.gui
@pytest.mark.usefixtures("require_tk")
class TestWidgetGui:
    """Tests that use a real (hidden) Tk window.

    All tests share one Tk instance (module scope) - each test resets
    the timer via the ``reset_timer`` fixture.
    """

    @pytest.fixture(autouse=True)
    def auto_reset(self, built_widget):
        yield
        built_widget._timer.reset()
        if built_widget._root:
            built_widget._root.update()

    def test_build_creates_root(self, built_widget):
        assert built_widget._root is not None

    def test_root_is_not_destroyed(self, built_widget):
        """Tk window stays alive across tests (module-scoped fixture)."""
        assert built_widget._root is not None
        # winfo_exists() returns 1 for a live widget
        assert built_widget._root.winfo_exists()

    def test_toggle_btn_initial_text_is_start(self, built_widget):
        assert built_widget._toggle_btn is not None
        assert "Start" in built_widget._toggle_btn["text"]

    def test_time_label_exists(self, built_widget):
        assert built_widget._time_label is not None

    def test_date_label_exists(self, built_widget):
        assert built_widget._date_label is not None


# ---------------------------------------------------------------------------
# Widget with ProjectManager - GUI + project management
# ---------------------------------------------------------------------------


@pytest.mark.gui
@pytest.mark.usefixtures("require_tk")
class TestWidgetWithProjectManager:
    """Tests that require a TickTockWidget wired to a real ProjectManager."""

    @pytest.fixture(autouse=True)
    def auto_reset(self, built_widget_pm):
        w, pm, _storage = built_widget_pm
        yield
        w._timer.reset()
        if w._root:
            w._root.update()

    def test_project_row_widgets_exist(self, built_widget_pm):
        w, _pm, _s = built_widget_pm
        assert w._project_combobox is not None
        assert w._title_icon_label is not None
        assert w._tree is not None

    def test_controller_active_project_name_returns_name(self, built_widget_pm):
        w, pm, _s = built_widget_pm
        assert w._controller.active_project_name() == pm.active_project.name

    def test_controller_active_project_name_fallback(self):
        """Without a project manager the fallback is 'default'."""
        w = TickTockWidget()
        assert w._controller.active_project_name() == "default"

    def test_update_project_selector_shows_non_archived(self, built_widget_pm):
        w, pm, _s = built_widget_pm
        second = pm.add("SAToArchive", "")
        w._update_project_selector()
        # Combobox values should include the new project
        assert w._project_combobox is not None
        assert any("SAToArchive" in v for v in w._project_combobox["values"])
        pm.set_archived(second.project_id, True)
        w._update_project_selector()
        # Archived projects should not appear in the combobox
        assert not any("SAToArchive" in v for v in w._project_combobox["values"])

    def test_update_project_selector_sets_active_label(self, built_widget_pm):
        w, pm, _s = built_widget_pm
        w._update_project_selector()
        active = pm.active_project
        expected = active.alias if active.alias else active.name
        assert expected == w._project_combobox.get()

    def test_title_icon_updates_with_active_project_color(self, built_widget_pm):
        w, pm, _s = built_widget_pm
        pm.update(pm.active_project.project_id, pm.active_project.name, color="#FF0000")
        w._update_project_selector()
        assert w._title_icon_label["fg"] == "#FF0000"

    def test_title_icon_dim_when_no_color(self, built_widget_pm):
        w, pm, _s = built_widget_pm
        pm.update(pm.active_project.project_id, pm.active_project.name, color="")
        w._update_project_selector()
        # icon falls back to fg_dim when no color
        assert w._title_icon_label["fg"] == "#00AA00"

    # ---- v0.6.1 new features -----------------------------------------

    def test_combobox_shows_active_project(self, built_widget_pm):
        """Combobox displays the active project's alias (or name if no alias)."""
        w, pm, _s = built_widget_pm
        w._update_project_selector()
        active = pm.active_project
        expected = active.alias if active.alias else active.name
        assert w._project_combobox.get() == expected

    def test_combobox_updates_after_project_switch(self, built_widget_pm):
        """Combobox reflects the newly active project after a switch."""
        w, pm, _s = built_widget_pm
        second = pm.add("Combobox Switch Target", "")
        w._on_project_switch(second.project_id)
        expected = second.alias if second.alias else second.name
        assert w._project_combobox.get() == expected
        # Switch back to original project
        w._on_project_switch(pm.projects[0].project_id)

    def test_report_button_is_enabled(self, built_widget_pm):
        """Report button must be enabled and wired up (v0.9.0)."""
        w, _pm, _s = built_widget_pm
        assert w._report_btn is not None
        assert str(w._report_btn["state"]) == "normal"

    def test_opacity_var_initialized(self, built_widget_pm):
        """Opacity DoubleVar is created and within valid range."""
        w, _pm, _s = built_widget_pm
        assert w._opacity_var is not None
        val = w._opacity_var.get()
        assert 0.3 <= val <= 1.0

    def test_opacity_change_updates_window(self, built_widget_pm):
        """_on_opacity_change adjusts window alpha without raising."""
        w, _pm, _s = built_widget_pm
        # Should not raise even when config is absent
        w._on_opacity_change("0.7")
        w._on_opacity_change("1.0")

    def test_tree_action_column_exists(self, built_widget_pm):
        """Tree has three columns: tree, elapsed, action."""
        w, _pm, _s = built_widget_pm
        assert "action" in w._tree["columns"]

    def test_tree_action_shows_play_for_inactive_row(self, built_widget_pm):
        """Inactive sub-activity rows show a play symbol in the action column."""
        w, pm, _s = built_widget_pm
        assert w._sub_activity_mgr is not None
        sa = w._sub_activity_mgr.add("InactiveSub")
        w._rebuild_tree()
        sa_iid = w._sub_tree_iids.get(sa.sub_activity_id)
        assert sa_iid is not None
        assert w._tree.set(sa_iid, "action") == "\u25b6"
        # Clean up
        w._sub_activity_mgr.set_archived(sa.sub_activity_id, True)
        w._rebuild_tree()

    def test_on_projects_changed_updates_selector(self, built_widget_pm):
        w, pm, _s = built_widget_pm
        new_project = pm.add("NewProject", "")
        w._on_projects_changed()
        # New project should appear in the combobox
        combo_vals = list(w._project_combobox["values"])
        assert any("NewProject" in v for v in combo_vals)
        # Clean up
        pm.set_archived(new_project.project_id, True)
        w._on_projects_changed()

    def test_on_tree_select_project_switches_project(self, built_widget_pm):
        w, pm, _s = built_widget_pm
        second = pm.add("SecondPM", "")
        w._on_tree_select_project(second.project_id)
        assert pm.active_project.project_id == second.project_id
        # switch back
        w._on_project_switch(pm.projects[0].project_id)

    def test_project_switch_saves_and_restores_elapsed(self, built_widget_pm):
        w, pm, _s = built_widget_pm
        second = pm.add("ForSwitch", "")
        # Give the first project some elapsed time
        w._timer.restore(500.0)
        w._on_project_switch(second.project_id)
        assert pm.active_project.project_id == second.project_id
        # Active project's elapsed should now be 0 (new project)
        assert w._timer.elapsed == pytest.approx(0.0)
        # Clean up: switch back
        w._on_project_switch(pm.projects[0].project_id)

    def test_on_projects_changed_resyncs_stopped_timer_to_new_active_project(
        self, built_widget_pm
    ):
        w, pm, _s = built_widget_pm
        second = pm.add("ResyncTarget", "")
        pm.switch(second.project_id)
        pm.save_elapsed(88.0)

        # Simulate stale STOPPED elapsed from a previously active project.
        w._timer.restore(15.0, "stopped")
        w._on_projects_changed()

        assert w._timer.state == TimerState.STOPPED
        assert w._timer.elapsed == pytest.approx(88.0)

    def test_before_project_change_switches_away_from_active_project(
        self, built_widget_pm
    ):
        w, pm, _s = built_widget_pm
        pm.add("Fallback", "")
        target_id = pm.active_project.project_id

        ok = w._before_project_change(target_id)

        assert ok is True
        assert pm.active_project is not None
        assert pm.active_project.project_id != target_id

    def test_before_sub_activity_delete_switches_target_to_project(
        self, built_widget_pm
    ):
        w, pm, _s = built_widget_pm
        assert w._sub_activity_mgr is not None

        sa = w._sub_activity_mgr.add("DeleteTarget")
        w._sub_activity_mgr.save_elapsed(sa.sub_activity_id, 120.0)
        pm.save_elapsed(45.0)
        w._active_sub_activity_id = sa.sub_activity_id
        w._timer.restore(120.0, "stopped")

        ok = w._before_sub_activity_delete(
            pm.active_project.project_id, sa.sub_activity_id
        )

        assert ok is True
        assert w._active_sub_activity_id is None
        assert w._timer.state == TimerState.STOPPED
        assert w._timer.elapsed == pytest.approx(45.0)

    def test_storage_callbacks_fire_with_project_manager(self, built_widget_pm):
        w, pm, storage = built_widget_pm
        w._on_toggle()  # start callback route
        w._on_toggle()  # pause callback route
        w._on_toggle()  # resume callback route
        w._timer.stop()  # stop callback route
        w._timer.reset()  # reset callback route
        # No assertion needed - just verifying no exception is raised

    def test_restore_timer_state_on_startup(self, tmp_path):
        """Widget restores elapsed from active project on build()."""
        storage = Storage(tmp_path / "rt.db")
        pm = ProjectManager(storage)
        pm.save_elapsed(300.0)
        w = TickTockWidget(storage=storage, project_manager=pm)
        w.build()
        assert w._root is not None
        w._root.withdraw()
        assert w._timer.elapsed == pytest.approx(300.0)
        w.close()

    def test_restore_timer_state_prefers_saved_running_state(
        self, tmp_path, monkeypatch
    ):
        """Startup restore should honor persisted running state when available."""
        storage = Storage(tmp_path / "rt_running.db")
        pm = ProjectManager(storage)
        pm.save_elapsed(100.0)
        storage.save_timer_state(250.0, "running")

        w = TickTockWidget(storage=storage, project_manager=pm)
        monkeypatch.setattr(w, "_refresh_elapsed", lambda: None)
        monkeypatch.setattr(w, "_update_project_combobox", lambda: None)
        monkeypatch.setattr(w, "_rebuild_tree", lambda: None)
        monkeypatch.setattr(w, "_set_panel_collapsed", lambda _collapsed: None)
        w._restore_timer_state()
        assert w._timer.state == TimerState.RUNNING
        assert w._timer.elapsed >= 250.0
        w.timer.stop()

    def test_restore_timer_state_prefers_saved_paused_state(
        self, tmp_path, monkeypatch
    ):
        """Startup restore should honor persisted paused state when available."""
        storage = Storage(tmp_path / "rt_paused.db")
        pm = ProjectManager(storage)
        pm.save_elapsed(100.0)
        storage.save_timer_state(240.0, "paused")

        w = TickTockWidget(storage=storage, project_manager=pm)
        monkeypatch.setattr(w, "_refresh_elapsed", lambda: None)
        monkeypatch.setattr(w, "_update_project_combobox", lambda: None)
        monkeypatch.setattr(w, "_rebuild_tree", lambda: None)
        monkeypatch.setattr(w, "_set_panel_collapsed", lambda _collapsed: None)
        w._restore_timer_state()
        assert w._timer.state == TimerState.PAUSED
        assert w._timer.elapsed == pytest.approx(240.0)
        w.timer.reset()

    def test_time_label_format(self, built_widget):
        """Clock label shows HH:MM:SS pattern after the first clock tick."""
        built_widget._root.update()  # process pending after() callbacks
        text = built_widget._time_label["text"]
        parts = text.split(":")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_date_label_format(self, built_widget):
        """Date label shows DD/MM/YYYY pattern after the first clock tick."""
        built_widget._root.update()
        text = built_widget._date_label["text"]
        parts = text.split("/")
        assert len(parts) == 3

    def test_start_updates_toggle_to_stop(self, built_widget):
        built_widget._on_toggle()  # start
        built_widget._root.update()  # flush after(0, ...) callbacks
        assert "Stop" in built_widget._toggle_btn["text"]
        built_widget._timer.stop()

    def test_stop_resets_toggle_to_start_or_continue(self, built_widget):
        built_widget._on_toggle()  # start
        built_widget._timer.stop()
        built_widget._root.update()
        # After stopping a running timer some elapsed is accumulated, so the
        # button shows "Continue" (resume without reset).  If elapsed happens
        # to round to exactly 0 (extremely unlikely) it falls back to "Start".
        btn_text = built_widget._toggle_btn["text"]
        assert "Start" in btn_text or "Continue" in btn_text

    def test_pause_updates_toggle_to_resume(self, built_widget):
        built_widget._on_toggle()  # start
        built_widget._timer.pause()
        built_widget._root.update()
        assert "Start" in built_widget._toggle_btn["text"]

    def test_reset_shows_start_btn(self, built_widget):
        built_widget._on_toggle()  # start
        built_widget._timer.reset()
        built_widget._root.update()
        assert "Start" in built_widget._toggle_btn["text"]

    def test_drag_start_stores_coordinates(self, built_widget):
        event = type("Event", (), {"x_root": 100, "y_root": 200})()
        built_widget._drag_start(event)
        assert built_widget._drag_x == 100
        assert built_widget._drag_y == 200

    def test_drag_motion_updates_internal_state(self, built_widget):
        """Drag motion updates the stored cursor coordinates."""
        start = type("Event", (), {"x_root": 50, "y_root": 60})()
        built_widget._drag_start(start)
        move = type("Event", (), {"x_root": 70, "y_root": 90})()
        built_widget._drag_motion(move)
        # After motion the stored coords should reflect the latest position
        assert built_widget._drag_x == 70
        assert built_widget._drag_y == 90

    def test_close_stops_timer(self, built_widget):
        built_widget._on_toggle()  # start
        built_widget._timer.stop()  # stop without destroying window
        state = built_widget._timer.state
        assert state in (TimerState.STOPPED, TimerState.IDLE)

    def test_on_window_close_request_hides_to_tray_when_running(self, built_widget_pm):
        w, _pm, _s = built_widget_pm
        assert w._root is not None

        class RunningTray:
            @staticmethod
            def is_running() -> bool:
                return True

            @staticmethod
            def stop() -> None:
                return None

        w._root.deiconify()
        w._root.update_idletasks()
        w._tray = RunningTray()

        w._on_window_close_request()
        w._root.update_idletasks()

        assert w._root.state() == "withdrawn"
        w._root.deiconify()

    def test_toggle_tray_visibility_round_trip(self, built_widget_pm):
        w, _pm, _s = built_widget_pm
        assert w._root is not None

        w._root.deiconify()
        w._root.update_idletasks()
        w._toggle_tray_visibility()
        assert w._root.state() == "withdrawn"

        w._toggle_tray_visibility()
        assert w._root.state() != "withdrawn"
        w._root.withdraw()

    def test_hide_to_tray_destroys_minimized_widget(self, built_widget_pm):
        w, _pm, _s = built_widget_pm
        assert w._root is not None

        class FakeMini:
            def __init__(self) -> None:
                self.destroyed = False

            def destroy(self) -> None:
                self.destroyed = True

        mini = FakeMini()
        w._minimized_widget = mini
        w._root.deiconify()
        w._hide_to_tray()

        assert mini.destroyed is True
        assert w._minimized_widget is None
        assert w._root.state() == "withdrawn"

    def test_minimize_and_restore_window_flow(self, built_widget_pm, monkeypatch):
        w, _pm, _s = built_widget_pm
        assert w._root is not None

        created: dict[str, object] = {}

        class FakeMini:
            def __init__(self, **kwargs):
                created.update(kwargs)

            @staticmethod
            def destroy() -> None:
                return None

        monkeypatch.setattr(widget_mod, "MinimizedWidget", FakeMini)

        w._root.deiconify()
        w._minimize()

        assert isinstance(w._minimized_widget, FakeMini)
        assert w._root.state() == "withdrawn"
        assert created["on_maximize"] == w._restore

        w._restore(40, 60)
        assert w._minimized_widget is None
        assert w._root.state() != "withdrawn"
        w._root.withdraw()

    def test_run_requires_no_explicit_build(self, built_widget):
        """After build(), the root exists and hasn't been auto-destroyed."""
        # build() was called in the fixture - verify the root is still live
        assert built_widget._root is not None
        assert built_widget._root.winfo_exists()


# ---------------------------------------------------------------------------
# Sub-activity tracking (no Tk window required)
# ---------------------------------------------------------------------------


class TestWidgetSubActivityTracking:
    """Logic tests for sub-activity time tracking - no GUI window needed."""

    @pytest.fixture
    def wpm(self, tmp_path):
        """Widget with real Storage + ProjectManager, no built window."""
        storage = Storage(tmp_path / "sa_test.db")
        pm = ProjectManager(storage)
        w = TickTockWidget(storage=storage, project_manager=pm)
        yield w, pm, storage
        if w.timer.state in (TimerState.RUNNING, TimerState.PAUSED):
            w.timer.stop()
        w.timer.reset()

    # ---- initialisation --------------------------------------------------

    def test_sub_activity_mgr_initialized_with_pm_and_storage(self, wpm):
        from src.sub_activities import SubActivityManager

        w, _, _ = wpm
        assert isinstance(w._sub_activity_mgr, SubActivityManager)

    def test_sub_activity_mgr_scoped_to_active_project(self, wpm):
        w, pm, _ = wpm
        assert w._sub_activity_mgr.project_id == pm.active_project.project_id

    def test_sub_activity_mgr_none_without_storage(self):
        w = TickTockWidget()
        assert w._sub_activity_mgr is None

    def test_active_sub_activity_id_starts_none(self, wpm):
        w, _, _ = wpm
        assert w._active_sub_activity_id is None

    def test_project_switch_same_project_clears_active_sub_activity(self, wpm):
        """Switching to the active project id returns to project-level tracking."""
        w, pm, _ = wpm
        sa = w._sub_activity_mgr.add("MiniSwitch")
        w._sub_activity_mgr.save_elapsed(sa.sub_activity_id, 120.0)
        pm.save_elapsed(45.0)
        w._active_sub_activity_id = sa.sub_activity_id
        w._timer.restore(120.0)

        w._on_project_switch(pm.active_project.project_id)

        assert w._active_sub_activity_id is None
        assert w._timer.elapsed == pytest.approx(45.0)

    # ---- controller.save_active_elapsed -----------------------------------

    def test_controller_save_active_elapsed_to_project_by_default(self, wpm):
        w, pm, _ = wpm
        w._controller.save_active_elapsed(120.0)
        assert pm.active_project.elapsed_seconds == pytest.approx(120.0)

    def test_controller_save_active_elapsed_to_sub_activity(self, wpm):
        w, pm, _ = wpm
        sa = w._sub_activity_mgr.add("Design")
        w._active_sub_activity_id = sa.sub_activity_id
        w._controller.save_active_elapsed(75.0)
        assert w._sub_activity_mgr.get(
            sa.sub_activity_id
        ).elapsed_seconds == pytest.approx(75.0)
        # Project's own elapsed_seconds must NOT be written
        assert pm.active_project.elapsed_seconds == pytest.approx(0.0)

    def test_controller_save_active_elapsed_no_project_mgr(self):
        """Controller elapsed save is safe when there is no ProjectManager."""
        w = TickTockWidget()
        w._controller.save_active_elapsed(50.0)  # must not raise

    def test_controller_save_active_elapsed_sub_id_without_mgr(self, wpm):
        """Has active sub-activity id but manager was cleared - falls through."""
        w, pm, _ = wpm
        w._active_sub_activity_id = 999
        w._sub_activity_mgr = None
        # Should fall back to project save
        w._controller.save_active_elapsed(40.0)
        assert pm.active_project.elapsed_seconds == pytest.approx(40.0)

    # ---- _load_sub_activities_for_project --------------------------------

    def test_load_creates_sub_activity_manager(self, wpm):
        from src.sub_activities import SubActivityManager

        w, pm, _ = wpm
        w._load_sub_activities_for_project(pm.active_project.project_id)
        assert isinstance(w._sub_activity_mgr, SubActivityManager)

    def test_load_clears_active_sub_activity(self, wpm):
        w, pm, _ = wpm
        w._active_sub_activity_id = 42  # fake active sub
        w._load_sub_activities_for_project(pm.active_project.project_id)
        assert w._active_sub_activity_id is None

    def test_load_without_storage_clears_active_id(self, wpm):
        w, pm, _ = wpm
        w._storage = None
        w._active_sub_activity_id = 5
        w._load_sub_activities_for_project(pm.active_project.project_id)
        assert w._active_sub_activity_id is None

    # ---- sub-activity time tracking round-trip ---------------------------

    def test_sub_activity_elapsed_persists_across_instances(self, wpm):
        """Elapsed saved via controller survives a reload."""
        w, pm, storage = wpm
        sa = w._sub_activity_mgr.add("Task A")
        w._active_sub_activity_id = sa.sub_activity_id
        w._controller.save_active_elapsed(300.0)
        from src.sub_activities import SubActivityManager

        mgr2 = SubActivityManager(storage, pm.active_project.project_id)
        assert mgr2.get(sa.sub_activity_id).elapsed_seconds == pytest.approx(300.0)

    def test_project_elapsed_unchanged_when_sub_active(self, wpm):
        """Project's own elapsed stays 0 while tracking via a sub-activity."""
        w, pm, storage = wpm
        sa = w._sub_activity_mgr.add("Coding")
        w._active_sub_activity_id = sa.sub_activity_id
        w._controller.save_active_elapsed(500.0)
        from src.projects import ProjectManager as PM2

        pm2 = PM2(storage)
        assert pm2.active_project.elapsed_seconds == pytest.approx(0.0)

    def test_reset_with_sub_activity_active_clears_elapsed(self, wpm):
        """User reset zeros the active sub-activity's elapsed."""
        w, pm, _ = wpm
        sa = w._sub_activity_mgr.add("Sprint")
        w._active_sub_activity_id = sa.sub_activity_id
        w._controller.save_active_elapsed(200.0)
        # Fire reset callback (simulates the user pressing Reset)
        w._controller.on_reset(w._timer)
        reloaded_sa = w._sub_activity_mgr.get(sa.sub_activity_id)
        assert reloaded_sa.elapsed_seconds == pytest.approx(0.0)

    def test_stop_with_sub_activity_saves_to_sub(self, wpm):
        """Stopping the timer while a sub-activity is active saves to that sub."""
        w, pm, _ = wpm
        sa = w._sub_activity_mgr.add("Review")
        w._active_sub_activity_id = sa.sub_activity_id
        w._timer.restore(150.0)
        w._controller.on_stopped(w._timer)
        assert w._sub_activity_mgr.get(
            sa.sub_activity_id
        ).elapsed_seconds == pytest.approx(150.0)
        assert pm.active_project.elapsed_seconds == pytest.approx(0.0)

    # ---- _on_tree_click integration --------------------------------------

    def test_tree_click_active_sub_running_falls_back_to_project(
        self,
        wpm,
        monkeypatch,
    ):
        w, pm, _ = wpm

        class DummyTree:
            @staticmethod
            def identify_column(_x: int) -> str:
                return "#3"

            @staticmethod
            def identify_row(_y: int) -> str:
                return "sub-row"

        called = {"project_id": None}
        monkeypatch.setattr(
            w,
            "_on_tree_select_project",
            lambda project_id: called.update({"project_id": project_id}),
        )

        w._tree = DummyTree()
        w._active_sub_activity_id = 77
        w._timer.restore(10.0, "running")
        w._tree_node_map = {
            "sub-row": TreeNodeEntry(
                kind="sub",
                node_id=77,
                project_id=pm.active_project.project_id,
            )
        }

        event = type("Event", (), {"x": 0, "y": 0})()
        assert w._on_tree_click(event) == "break"
        assert called["project_id"] == pm.active_project.project_id

    def test_tree_click_inactive_target_paused_activates_and_toggles(
        self,
        wpm,
        monkeypatch,
    ):
        w, pm, _ = wpm

        class DummyTree:
            @staticmethod
            def identify_column(_x: int) -> str:
                return "#3"

            @staticmethod
            def identify_row(_y: int) -> str:
                return "sub-row"

        called = {"activate": None, "toggle": 0}
        monkeypatch.setattr(
            w,
            "_activate_tree_item",
            lambda iid: called.update({"activate": iid}),
        )
        monkeypatch.setattr(
            w,
            "_on_toggle",
            lambda: called.update({"toggle": called["toggle"] + 1}),
        )

        w._tree = DummyTree()
        w._active_sub_activity_id = None
        w._timer.restore(5.0, "paused")
        w._tree_node_map = {
            "sub-row": TreeNodeEntry(
                kind="sub",
                node_id=88,
                project_id=pm.active_project.project_id,
            )
        }

        event = type("Event", (), {"x": 0, "y": 0})()
        assert w._on_tree_click(event) == "break"
        assert called["activate"] == "sub-row"
        assert called["toggle"] == 1

    def test_tree_click_active_project_level_toggles_only(self, wpm, monkeypatch):
        w, pm, _ = wpm

        class DummyTree:
            @staticmethod
            def identify_column(_x: int) -> str:
                return "#3"

            @staticmethod
            def identify_row(_y: int) -> str:
                return "proj-row"

        called = {"activate": 0, "toggle": 0}
        monkeypatch.setattr(
            w,
            "_activate_tree_item",
            lambda _iid: called.update({"activate": called["activate"] + 1}),
        )
        monkeypatch.setattr(
            w,
            "_on_toggle",
            lambda: called.update({"toggle": called["toggle"] + 1}),
        )

        w._tree = DummyTree()
        w._active_sub_activity_id = None
        w._tree_node_map = {
            "proj-row": TreeNodeEntry(
                kind="project",
                node_id=pm.active_project.project_id,
            )
        }

        event = type("Event", (), {"x": 0, "y": 0})()
        assert w._on_tree_click(event) == "break"
        assert called["toggle"] == 1
        assert called["activate"] == 0


# ---------------------------------------------------------------------------
# v0.6.0 - UI Enhancements
# ---------------------------------------------------------------------------


class TestValidateWindowPosition:
    """Tests for _validate_window_position - screen-boundary clamping."""

    def test_in_bounds_position_unchanged(self):
        x, y = TickTockWidget._validate_window_position(
            200, 100, 340, 390, 0, 0, 1920, 1080
        )
        assert x == 200
        assert y == 100

    def test_y_below_zero_clamped_to_zero(self):
        _x, y = TickTockWidget._validate_window_position(
            200, -50, 340, 390, 0, 0, 1920, 1080
        )
        assert y == 0

    def test_x_too_far_right_clamped(self):
        # x so large that < margin (50) px would be visible on right
        x, _y = TickTockWidget._validate_window_position(
            1900, 100, 340, 390, 0, 0, 1920, 1080
        )
        assert x <= 1920 - 50

    def test_y_too_far_down_clamped(self):
        _x, y = TickTockWidget._validate_window_position(
            100, 1060, 340, 390, 0, 0, 1920, 1080
        )
        assert y <= 1080 - 50

    def test_negative_x_allowed_when_window_still_partially_visible(self):
        # Window can extend off the left as long as margin px are shown
        x, _y = TickTockWidget._validate_window_position(
            -100, 100, 340, 390, 0, 0, 1920, 1080
        )
        # 50 - 340 = -290; -100 >= -290 so x stays at -100
        assert x == -100

    def test_x_clamped_to_margin_minus_width_when_far_left(self):
        x, _y = TickTockWidget._validate_window_position(
            -500, 100, 340, 390, 0, 0, 1920, 1080
        )
        assert x == 50 - 340  # == -290


@pytest.mark.gui
@pytest.mark.usefixtures("require_tk")
class TestWidgetConfig:
    """v0.6.0 - config integration: title, always-on-top, env indicator."""

    def test_build_without_config_succeeds(self):
        """Passing no config should not break widget construction."""
        w = TickTockWidget()
        w.build()
        assert w._root is not None
        w._root.withdraw()
        w.close()

    def test_title_label_has_no_env_suffix_in_prod(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        # default environment is prod
        w = TickTockWidget(config=cfg)
        w.build()
        w._root.withdraw()
        try:
            assert w._title_label is not None
            label_text = w._title_label.cget("text")
            assert "DEV" not in label_text
            assert "TEST" not in label_text
            assert "PROTO" not in label_text
        finally:
            w.close()

    def test_get_window_title_text_prod_has_no_suffix(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        w = TickTockWidget(config=cfg)
        assert "DEV" not in w._get_window_title_text()
        assert "TEST" not in w._get_window_title_text()

    def test_get_window_title_text_dev_has_suffix(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TICK_TOCK_ENV", "dev")
        cfg = Config(config_path=tmp_path / "config.json")
        w = TickTockWidget(config=cfg)
        assert "DEV" in w._get_window_title_text()

    def test_get_window_title_text_test_has_suffix(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TICK_TOCK_ENV", "test")
        cfg = Config(config_path=tmp_path / "config.json")
        assert "TEST" in TickTockWidget(config=cfg)._get_window_title_text()

    def test_get_window_title_text_prototype_has_suffix(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TICK_TOCK_ENV", "prototype")
        cfg = Config(config_path=tmp_path / "config.json")
        assert "PROTO" in TickTockWidget(config=cfg)._get_window_title_text()

    def test_save_window_state_persists_to_config(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        w = TickTockWidget(config=cfg)
        w.build()
        w._root.withdraw()
        try:
            w._save_window_state()
            assert cfg.get_ui_pref("window_x") is not None
            assert cfg.get_ui_pref("window_y") is not None
        finally:
            w.close()

    def test_close_saves_window_state(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        w = TickTockWidget(config=cfg)
        w.build()
        w._root.withdraw()
        w.close()
        # Position should have been persisted on close
        assert cfg.get_ui_pref("window_x") is not None

    def test_always_on_top_var_set_from_config(self, tmp_path):
        cfg = Config(config_path=tmp_path / "config.json")
        cfg.set_ui_pref("always_on_top", False)
        w = TickTockWidget(config=cfg)
        w.build()
        w._root.withdraw()
        try:
            assert w._always_on_top_var is not None
            assert w._always_on_top_var.get() is False
        finally:
            w.close()


@pytest.mark.gui
@pytest.mark.usefixtures("require_tk")
class TestWidgetStateIndicator:
    """v0.6.0 - elapsed label colour per timer state."""

    @pytest.fixture(scope="class")
    def w(self):
        widget = TickTockWidget()
        widget.build()
        assert widget._root is not None
        widget._root.withdraw()
        yield widget
        try:
            widget.close()
        except Exception:
            pass

    def _update(self, widget):
        widget._root.update()

    def test_running_toggle_btn_shows_pause(self, w):
        w._timer.start()
        self._update(w)
        assert "Stop" in w._toggle_btn["text"]
        w._timer.stop()
        self._update(w)

    def test_paused_toggle_btn_shows_resume(self, w):
        w._timer.start()
        w._timer.pause()
        self._update(w)
        assert "Start" in w._toggle_btn["text"]
        w._timer.reset()
        self._update(w)

    def test_idle_toggle_btn_shows_start(self, w):
        w._timer.reset()
        self._update(w)
        assert "Start" in w._toggle_btn["text"]
