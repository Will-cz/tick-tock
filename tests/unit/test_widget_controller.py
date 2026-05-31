"""Unit tests for WidgetController - no Tkinter, no display required."""

from pathlib import Path

import pytest

from src.app_service import AppService
from src.projects import ProjectManager
from src.storage import Storage
from src.ui.widget_controller import WidgetController


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeTimer:
    """Minimal Timer stand-in - just exposes the ``elapsed`` attribute."""

    def __init__(self, elapsed: float = 0.0) -> None:
        self.elapsed = elapsed


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "ctrl_test.db")


@pytest.fixture
def pm(storage: Storage) -> ProjectManager:
    return ProjectManager(storage)


@pytest.fixture
def svc(storage: Storage, pm: ProjectManager) -> AppService:
    return AppService(storage=storage, project_manager=pm)


@pytest.fixture
def ctrl(svc: AppService, pm: ProjectManager) -> WidgetController:
    return WidgetController(
        app_service=svc,
        project_manager=pm,
        active_sub_callback=lambda: (None, None),
    )


# ---------------------------------------------------------------------------
# Config-derived settings (no service required)
# ---------------------------------------------------------------------------


class TestConfigSettings:
    def test_defaults_with_no_config(self):
        c = WidgetController(app_service=None, project_manager=None, config=None)
        assert c.get_autosave_interval_ticks() == 60

    def test_round_elapsed_no_config_returns_unchanged(self):
        c = WidgetController(app_service=None, project_manager=None, config=None)
        assert c.round_elapsed(90.0) == 90.0

    def test_round_elapsed_5_min(self, tmp_path: Path):
        from src.config import Config

        cfg = Config(config_path=tmp_path / "cfg.json")
        cfg.set_timer_setting("time_rounding_minutes", 5)
        c = WidgetController(app_service=None, project_manager=None, config=cfg)
        # 271 s -> nearest 5 min = 300 s
        assert c.round_elapsed(271.0) == 300.0
        # 149 s -> nearest 5 min = 0 s (round-half-to-even; 74 s rounds down)
        assert c.round_elapsed(74.0) == 0.0

    def test_autosave_interval_from_config(self, tmp_path: Path):
        from src.config import Config

        cfg = Config(config_path=tmp_path / "cfg.json")
        cfg.set_timer_setting("autosave_interval_minutes", 5)
        c = WidgetController(app_service=None, project_manager=None, config=cfg)
        assert c.get_autosave_interval_ticks() == 300

    def test_max_backups_from_config(self, tmp_path: Path):
        from src.config import Config

        cfg = Config(config_path=tmp_path / "cfg.json")
        cfg.set_timer_setting("max_backup_files", 10)
        assert cfg.get_timer_setting("max_backup_files", 5) == 10


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


class TestInitialState:
    def test_tick_count_starts_at_zero(self, ctrl: WidgetController):
        assert ctrl.tick_count == 0

    def test_daily_elapsed_starts_at_zero(self, ctrl: WidgetController):
        assert ctrl.last_saved_daily_elapsed == 0.0

    def test_switching_project_starts_false(self, ctrl: WidgetController):
        assert ctrl.switching_project is False


class TestThreadSafeStateAccessors:
    def test_set_switching_project(self, ctrl: WidgetController):
        ctrl.set_switching_project(True)
        assert ctrl.switching_project is True

    def test_set_daily_anchor_updates_elapsed_and_date(self, ctrl: WidgetController):
        ctrl.set_daily_anchor(42.0, "2026-04-08")
        assert ctrl.get_last_saved_daily_elapsed() == 42.0
        assert ctrl.current_date == "2026-04-08"

    def test_handle_midnight_rollover_updates_date(self, ctrl: WidgetController):
        ctrl.current_date = "2026-04-07"
        ctrl.handle_midnight_rollover(0.0, "2026-04-08")
        assert ctrl.current_date == "2026-04-08"


# ---------------------------------------------------------------------------
# on_started
# ---------------------------------------------------------------------------


class TestOnStarted:
    def test_resets_tick_count(self, ctrl: WidgetController):
        ctrl.tick_count = 42
        ctrl.on_started(FakeTimer(0.0))
        assert ctrl.tick_count == 0

    def test_resets_daily_elapsed(self, ctrl: WidgetController):
        ctrl.last_saved_daily_elapsed = 999.0
        ctrl.on_started(FakeTimer(0.0))
        assert ctrl.last_saved_daily_elapsed == 0.0

    def test_saves_timer_state(self, ctrl: WidgetController, svc: AppService):
        ctrl.on_started(FakeTimer(0.0))
        state = svc.load_timer_state()
        assert state is not None
        assert state["state"] == "running"


# ---------------------------------------------------------------------------
# on_paused
# ---------------------------------------------------------------------------


class TestOnPaused:
    def test_saves_timer_state_as_paused(self, ctrl: WidgetController, svc: AppService):
        ctrl.on_paused(FakeTimer(120.0))
        state = svc.load_timer_state()
        assert state is not None
        assert state["state"] == "paused"

    def test_flushes_daily_elapsed(self, ctrl: WidgetController, pm: ProjectManager):
        p = pm.add("Pause Test Project")
        pm.switch(p.project_id)
        ctrl.last_saved_daily_elapsed = 0.0
        ctrl.on_paused(FakeTimer(60.0))
        # daily delta should have been written
        assert ctrl.last_saved_daily_elapsed == 60.0


# ---------------------------------------------------------------------------
# on_resumed
# ---------------------------------------------------------------------------


class TestOnResumed:
    def test_saves_timer_state_as_running(
        self, ctrl: WidgetController, svc: AppService
    ):
        ctrl.on_resumed(FakeTimer(50.0))
        state = svc.load_timer_state()
        assert state is not None
        assert state["state"] == "running"

    def test_anchors_daily_elapsed(self, ctrl: WidgetController):
        ctrl.on_resumed(FakeTimer(50.0))
        assert ctrl.last_saved_daily_elapsed == 50.0


# ---------------------------------------------------------------------------
# on_stopped
# ---------------------------------------------------------------------------


class TestOnStopped:
    def test_saves_elapsed_to_project(self, ctrl: WidgetController, pm: ProjectManager):
        p = pm.add("Stop Test Project")
        pm.switch(p.project_id)
        ctrl.on_stopped(FakeTimer(180.0))
        pm.reload()
        updated = next(x for x in pm.projects if x.project_id == p.project_id)
        assert abs(updated.elapsed_seconds - 180.0) < 0.01

    def test_saves_elapsed_to_sub_activity_via_callback(
        self, svc: AppService, pm: ProjectManager
    ):
        p = pm.add("Stop Sub Project")
        pm.switch(p.project_id)
        mgr = svc.create_sub_manager(p.project_id)
        sa = mgr.add("Stop Sub Task")

        c = WidgetController(
            app_service=svc,
            project_manager=pm,
            active_sub_callback=lambda: (sa.sub_activity_id, mgr),
        )
        c.on_stopped(FakeTimer(90.0))

        subs = svc.list_sub_activities(p.project_id)
        updated = next(x for x in subs if x["id"] == sa.sub_activity_id)
        assert abs(updated["elapsed_seconds"] - 90.0) < 0.01

    def test_timer_state_saved_as_stopped(
        self, ctrl: WidgetController, svc: AppService
    ):
        ctrl.on_stopped(FakeTimer(50.0))
        state = svc.load_timer_state()
        assert state is not None
        assert state["state"] == "stopped"


# ---------------------------------------------------------------------------
# on_reset
# ---------------------------------------------------------------------------


class TestOnReset:
    def test_clears_timer_state(self, ctrl: WidgetController, svc: AppService):
        svc.save_timer_state(100.0, "running")
        ctrl.on_reset(FakeTimer(0.0))
        assert svc.load_timer_state() is None

    def test_saves_zero_elapsed_to_project(
        self, ctrl: WidgetController, pm: ProjectManager
    ):
        p = pm.add("Reset Test Project")
        pm.switch(p.project_id)
        pm.save_elapsed(500.0)  # give it some elapsed first
        ctrl.on_reset(FakeTimer(0.0))
        pm.reload()
        updated = next(x for x in pm.projects if x.project_id == p.project_id)
        assert updated.elapsed_seconds == 0.0

    def test_switching_project_suppresses_save_and_log(
        self, svc: AppService, pm: ProjectManager
    ):
        """When switching_project=True, reset should NOT zero-out elapsed."""
        p = pm.add("Switch Reset Project")
        pm.switch(p.project_id)
        pm.save_elapsed(777.0)

        c = WidgetController(
            app_service=svc,
            project_manager=pm,
            active_sub_callback=lambda: (None, None),
        )
        c.switching_project = True
        c.on_reset(FakeTimer(0.0))

        pm.reload()
        updated = next(x for x in pm.projects if x.project_id == p.project_id)
        # elapsed should remain unchanged - no save_active_elapsed(0.0) was called
        assert abs(updated.elapsed_seconds - 777.0) < 0.01

    def test_resets_tick_count(self, ctrl: WidgetController):
        ctrl.tick_count = 55
        ctrl.on_reset(FakeTimer(0.0))
        assert ctrl.tick_count == 0

    def test_resets_daily_elapsed(self, ctrl: WidgetController):
        ctrl.last_saved_daily_elapsed = 300.0
        ctrl.on_reset(FakeTimer(0.0))
        assert ctrl.last_saved_daily_elapsed == 0.0


# ---------------------------------------------------------------------------
# on_tick - periodic autosave
# ---------------------------------------------------------------------------


class TestOnTick:
    def test_increments_tick_count(self, ctrl: WidgetController):
        ctrl.on_tick(FakeTimer(10.0))
        assert ctrl.tick_count == 1

    def test_saves_at_autosave_interval(
        self, ctrl: WidgetController, pm: ProjectManager, svc: AppService
    ):
        p = pm.add("Tick Save Project")
        pm.switch(p.project_id)

        interval = ctrl.get_autosave_interval_ticks()
        timer = FakeTimer(interval * 1.0)

        # Drive the controller to exactly the autosave tick
        ctrl.tick_count = interval - 1
        ctrl.on_tick(timer)

        # Timer state should have been saved
        state = svc.load_timer_state()
        assert state is not None
        assert state["state"] == "running"

    def test_does_not_save_before_interval(
        self, ctrl: WidgetController, svc: AppService
    ):
        # No active project, tick_count starts at 0
        ctrl.on_tick(FakeTimer(5.0))
        # Should not have saved timer state yet (1 tick << 60 tick interval)
        assert svc.load_timer_state() is None


# ---------------------------------------------------------------------------
# flush_daily_at
# ---------------------------------------------------------------------------


class TestFlushDailyAt:
    def test_writes_delta_to_daily_log(
        self, ctrl: WidgetController, pm: ProjectManager, svc: AppService
    ):
        p = pm.add("Flush Daily Project")
        pm.switch(p.project_id)
        ctrl.last_saved_daily_elapsed = 0.0
        ctrl.flush_daily_at(120.0)
        by_project = svc.storage.get_daily_seconds_by_project(ctrl.current_date)
        assert abs(by_project.get(p.project_id, 0.0) - 120.0) < 0.01

    def test_updates_last_saved_daily_elapsed(
        self, ctrl: WidgetController, pm: ProjectManager
    ):
        p = pm.add("Flush Update Project")
        pm.switch(p.project_id)
        ctrl.last_saved_daily_elapsed = 30.0
        ctrl.flush_daily_at(90.0)
        assert ctrl.last_saved_daily_elapsed == 90.0

    def test_does_not_write_negative_delta(
        self, ctrl: WidgetController, pm: ProjectManager, svc: AppService
    ):
        p = pm.add("Flush Neg Project")
        pm.switch(p.project_id)
        ctrl.last_saved_daily_elapsed = 100.0
        ctrl.flush_daily_at(50.0)  # elapsed < last_saved -> delta is negative/zero
        by_project = svc.storage.get_daily_seconds_by_project(ctrl.current_date)
        assert by_project.get(p.project_id, 0.0) == 0.0

    def test_no_project_active_does_nothing(self, ctrl: WidgetController):
        """flush_daily_at should not raise when no project is active."""
        ctrl.last_saved_daily_elapsed = 0.0
        ctrl.flush_daily_at(60.0)  # no active project -> should be a no-op

    def test_daily_flush_callback_receives_project_id(
        self, svc: AppService, pm: ProjectManager
    ):
        p = pm.add("Callback Flush Project")
        pm.switch(p.project_id)
        observed: list[tuple[str, int, float]] = []
        c = WidgetController(
            app_service=svc,
            project_manager=pm,
            active_sub_callback=lambda: (None, None),
            daily_flush_callback=lambda day_text, project_id, delta: observed.append(
                (day_text, project_id, delta)
            ),
        )
        c.last_saved_daily_elapsed = 0.0

        c.flush_daily_at(75.0)

        assert observed
        day_text, project_id, delta = observed[0]
        assert day_text == c.current_date
        assert project_id == p.project_id
        assert delta == pytest.approx(75.0)


# ---------------------------------------------------------------------------
# save_active_elapsed - callback routing
# ---------------------------------------------------------------------------


class TestSaveActiveElapsed:
    def test_routes_to_project_when_no_sub(
        self, ctrl: WidgetController, pm: ProjectManager
    ):
        p = pm.add("Active Elapsed Project")
        pm.switch(p.project_id)
        ctrl.save_active_elapsed(250.0)
        pm.reload()
        updated = next(x for x in pm.projects if x.project_id == p.project_id)
        assert abs(updated.elapsed_seconds - 250.0) < 0.01

    def test_routes_to_sub_activity_via_callback(
        self, svc: AppService, pm: ProjectManager
    ):
        p = pm.add("Callback Route Project")
        mgr = svc.create_sub_manager(p.project_id)
        sa = mgr.add("Callback Sub Task")

        c = WidgetController(
            app_service=svc,
            project_manager=pm,
            active_sub_callback=lambda: (sa.sub_activity_id, mgr),
        )
        c.save_active_elapsed(400.0)

        subs = svc.list_sub_activities(p.project_id)
        updated = next(x for x in subs if x["id"] == sa.sub_activity_id)
        assert abs(updated["elapsed_seconds"] - 400.0) < 0.01

    def test_no_service_does_nothing(self):
        c = WidgetController(
            app_service=None,
            project_manager=None,
            active_sub_callback=lambda: (None, None),
        )
        c.save_active_elapsed(100.0)  # should not raise
