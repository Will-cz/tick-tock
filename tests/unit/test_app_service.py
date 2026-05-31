"""Unit tests for AppService."""

from pathlib import Path

import pytest

from src.app_service import AppService
from src.projects import ProjectManager
from src.storage import Storage
from src.sub_activities import SubActivityManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


@pytest.fixture
def pm(storage: Storage) -> ProjectManager:
    return ProjectManager(storage)


@pytest.fixture
def svc(storage: Storage, pm: ProjectManager) -> AppService:
    return AppService(storage=storage, project_manager=pm)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


class TestProperties:
    def test_storage_property_returns_storage(self, svc: AppService, storage: Storage):
        assert svc.storage is storage

    def test_project_manager_property(self, svc: AppService, pm: ProjectManager):
        assert svc.project_manager is pm


# ---------------------------------------------------------------------------
# Timer state
# ---------------------------------------------------------------------------


class TestTimerState:
    def test_save_and_load_timer_state(self, svc: AppService):
        svc.save_timer_state(42.5, "running")
        state = svc.load_timer_state()
        assert state is not None
        assert abs(state["elapsed_seconds"] - 42.5) < 0.01
        assert state["state"] == "running"

    def test_clear_timer_state(self, svc: AppService):
        svc.save_timer_state(10.0, "paused")
        svc.clear_timer_state()
        assert svc.load_timer_state() is None

    def test_load_timer_state_when_empty_returns_none(self, svc: AppService):
        assert svc.load_timer_state() is None

    def test_log_activity_does_not_raise(self, svc: AppService):
        """log_activity should write without error."""
        svc.log_activity("start", "My Project")  # no assertion - fire and forget


# ---------------------------------------------------------------------------
# Daily time
# ---------------------------------------------------------------------------


class TestDailyTime:
    def test_add_daily_seconds(self, svc: AppService, pm: ProjectManager):
        p = pm.add("Daily Test")
        svc.add_daily_seconds(p.project_id, "2024-01-15", 3600.0)
        by_project = svc.storage.get_daily_seconds_by_project("2024-01-15")
        assert abs(by_project.get(p.project_id, 0.0) - 3600.0) < 0.01


# ---------------------------------------------------------------------------
# Project management
# ---------------------------------------------------------------------------


class TestProjectManagement:
    def test_switch_project_returns_project(self, svc: AppService, pm: ProjectManager):
        p = pm.add("Switch Test")
        result = svc.switch_project(p.project_id)
        assert result.project_id == p.project_id

    def test_save_project_elapsed(self, svc: AppService, pm: ProjectManager):
        p = pm.add("Elapsed Test")
        pm.switch(p.project_id)
        svc.save_project_elapsed(500.0)
        pm.reload()
        updated = next(x for x in pm.projects if x.project_id == p.project_id)
        assert abs(updated.elapsed_seconds - 500.0) < 0.01

    def test_reload_projects_refreshes_list(self, svc: AppService, pm: ProjectManager):
        initial_count = len(pm.projects)
        pm.add("Reload Test")
        # reload via service
        svc.reload_projects()
        assert len(pm.projects) == initial_count + 1


# ---------------------------------------------------------------------------
# Sub-activity management
# ---------------------------------------------------------------------------


class TestSubActivityManagement:
    def test_create_sub_manager_returns_manager(
        self, svc: AppService, pm: ProjectManager
    ):
        p = pm.add("SA Project")
        mgr = svc.create_sub_manager(p.project_id)
        assert isinstance(mgr, SubActivityManager)

    def test_list_sub_activities_empty_initially(
        self, svc: AppService, pm: ProjectManager
    ):
        p = pm.add("SA List Project")
        result = svc.list_sub_activities(p.project_id)
        assert result == []

    def test_list_sub_activities_after_add(self, svc: AppService, pm: ProjectManager):
        p = pm.add("SA Add Project")
        mgr = svc.create_sub_manager(p.project_id)
        mgr.add("Task A")
        result = svc.list_sub_activities(p.project_id)
        assert len(result) == 1
        assert result[0]["name"] == "Task A"


# ---------------------------------------------------------------------------
# save_elapsed routing
# ---------------------------------------------------------------------------


class TestSaveElapsedRouting:
    def test_routes_to_project_when_no_sub_activity(
        self, svc: AppService, pm: ProjectManager
    ):
        p = pm.add("Route Project")
        pm.switch(p.project_id)
        svc.save_elapsed(200.0)
        pm.reload()
        updated = next(x for x in pm.projects if x.project_id == p.project_id)
        assert abs(updated.elapsed_seconds - 200.0) < 0.01

    def test_routes_to_sub_activity_when_both_provided(
        self, svc: AppService, pm: ProjectManager
    ):
        p = pm.add("Sub Route Project")
        mgr = svc.create_sub_manager(p.project_id)
        sa = mgr.add("Sub Task")

        svc.save_elapsed(
            300.0, sub_activity_id=sa.sub_activity_id, sub_activity_mgr=mgr
        )

        subs = svc.list_sub_activities(p.project_id)
        updated = next(x for x in subs if x["id"] == sa.sub_activity_id)
        assert abs(updated["elapsed_seconds"] - 300.0) < 0.01

    def test_routes_to_project_when_only_sub_id_provided(
        self, svc: AppService, pm: ProjectManager
    ):
        """Only sub_activity_id without mgr should fall back to project."""
        p = pm.add("Fallback Project")
        pm.switch(p.project_id)
        svc.save_elapsed(100.0, sub_activity_id=99)  # no mgr supplied
        pm.reload()
        updated = next(x for x in pm.projects if x.project_id == p.project_id)
        assert abs(updated.elapsed_seconds - 100.0) < 0.01


# ---------------------------------------------------------------------------
# Data I/O
# ---------------------------------------------------------------------------


class TestDataIO:
    def test_backup_creates_file(self, svc: AppService, tmp_path: Path):
        """backup() should not raise and returns without error."""
        svc.backup(keep=3)

    def test_backup_uses_default_keep_when_omitted(
        self, storage: Storage, pm: ProjectManager, monkeypatch
    ):
        called: dict[str, int] = {}

        def fake_backup(*, keep=5):
            called["keep"] = keep

        monkeypatch.setattr(storage, "backup", fake_backup)
        configured = AppService(
            storage=storage,
            project_manager=pm,
            default_backup_keep=9,
        )
        configured.backup()
        assert called["keep"] == 9

    def test_export_and_import_json_roundtrip(
        self, svc: AppService, pm: ProjectManager, tmp_path: Path
    ):
        pm.add("Export Project")
        export_path = tmp_path / "export.json"
        svc.export_json(export_path)
        assert export_path.exists()

        # Import into a fresh service
        fresh_storage = Storage(tmp_path / "fresh.db")
        fresh_pm = ProjectManager(fresh_storage)
        fresh_svc = AppService(storage=fresh_storage, project_manager=fresh_pm)
        fresh_svc.import_json(export_path)
        fresh_pm.reload()
        names = [p.name for p in fresh_pm.projects]
        assert "Export Project" in names
