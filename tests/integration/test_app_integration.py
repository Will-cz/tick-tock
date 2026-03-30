"""Integration tests for cross-component data flows."""

from datetime import date
from pathlib import Path

import pytest

from src.app_service import AppService
from src.projects import ProjectManager
from src.storage import Storage

pytestmark = pytest.mark.integration


def test_project_and_sub_activity_flow_persists_across_reload(tmp_path: Path) -> None:
    db_path = tmp_path / "integration.db"
    storage = Storage(db_path)
    pm = ProjectManager(storage)
    svc = AppService(storage=storage, project_manager=pm)

    project = pm.add("Integration Project", "Cross-component flow")
    svc.switch_project(project.project_id)
    svc.save_elapsed(120.0)

    sub_mgr = svc.create_sub_manager(project.project_id)
    sub = sub_mgr.add("Design")
    svc.save_elapsed(
        45.0,
        sub_activity_id=sub.sub_activity_id,
        sub_activity_mgr=sub_mgr,
    )
    svc.add_daily_seconds(project.project_id, "2026-03-30", 120.0)
    svc.add_daily_sub_activity_seconds(
        project.project_id,
        sub.sub_activity_id,
        "2026-03-30",
        45.0,
    )

    pm.reload()
    reloaded_project = next(
        p for p in pm.projects if p.project_id == project.project_id
    )
    assert reloaded_project.elapsed_seconds == pytest.approx(120.0)

    sub_rows = svc.list_sub_activities(project.project_id)
    assert sub_rows and sub_rows[0]["elapsed_seconds"] == pytest.approx(45.0)

    by_project = storage.get_daily_seconds_by_project("2026-03-30")
    assert by_project[project.project_id] == pytest.approx(120.0)

    sub_data = storage.get_date_range_sub_activity_data(
        date(2026, 3, 30),
        date(2026, 3, 30),
        project_ids=[project.project_id],
    )
    assert sub_data[project.project_id][sub.sub_activity_id][
        "2026-03-30"
    ] == pytest.approx(45.0)


def test_export_import_preserves_project_and_sub_activity_relationships(
    tmp_path: Path,
) -> None:
    source_storage = Storage(tmp_path / "source.db")
    source_pm = ProjectManager(source_storage)
    source_svc = AppService(storage=source_storage, project_manager=source_pm)

    project = source_pm.add("Exported Project", "Will be imported")
    source_pm.switch(project.project_id)
    source_svc.save_project_elapsed(300.0)
    source_svc.save_timer_state(300.0, "stopped")
    sub_mgr = source_svc.create_sub_manager(project.project_id)
    sub = sub_mgr.add("Implementation")
    source_svc.add_daily_seconds(project.project_id, "2026-03-29", 300.0)
    source_svc.add_daily_sub_activity_seconds(
        project.project_id,
        sub.sub_activity_id,
        "2026-03-29",
        180.0,
    )

    export_path = tmp_path / "export" / "snapshot.json"
    source_svc.export_json(export_path)
    assert export_path.exists()

    dest_storage = Storage(tmp_path / "dest.db")
    dest_pm = ProjectManager(dest_storage)
    dest_svc = AppService(storage=dest_storage, project_manager=dest_pm)
    dest_svc.import_json(export_path)
    dest_pm.reload()

    imported_project = next(p for p in dest_pm.projects if p.name == "Exported Project")
    imported_subs = dest_svc.list_sub_activities(imported_project.project_id)
    assert len(imported_subs) == 1
    assert imported_subs[0]["name"] == "Implementation"
    assert imported_project.elapsed_seconds == pytest.approx(300.0)

    imported_state = dest_svc.load_timer_state()
    assert imported_state is not None
    assert imported_state["elapsed_seconds"] == pytest.approx(300.0)
