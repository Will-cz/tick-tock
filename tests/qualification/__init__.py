"""Qualification tests for realistic user interaction scenarios."""

from datetime import date
from pathlib import Path
from time import sleep

import pytest

from src.app_service import AppService
from src.projects import ProjectManager
from src.storage import Storage
from src.sub_activities import SubActivityManager
from src.timer import Timer

pytestmark = pytest.mark.qualification


def test_timer_session_project_switch_and_restart_persists_user_state(
    tmp_path: Path,
) -> None:
    """User journey: track time, switch project, restart app, resume state."""
    db_path = tmp_path / "scenario_restart.db"
    storage = Storage(db_path)
    pm = ProjectManager(storage)
    svc = AppService(storage=storage, project_manager=pm)
    timer = Timer(tick_interval=0.01)

    p1 = pm.active_project
    assert p1 is not None
    p2 = pm.add("Client Work", "secondary project")

    # Session on project 1: start -> pause -> resume -> stop
    timer.start()
    sleep(0.03)
    timer.pause()
    elapsed_after_pause = timer.elapsed
    assert elapsed_after_pause > 0.0
    timer.resume()
    sleep(0.03)
    timer.stop()
    first_session_elapsed = timer.elapsed
    svc.save_elapsed(first_session_elapsed)

    # Switch and track a short second session on project 2.
    svc.switch_project(p2.project_id)
    timer.reset()
    timer.start()
    sleep(0.02)
    timer.stop()
    second_session_elapsed = timer.elapsed
    svc.save_elapsed(second_session_elapsed)
    svc.save_timer_state(second_session_elapsed, "stopped")

    # Simulate app restart.
    restarted_storage = Storage(db_path)
    restarted_pm = ProjectManager(restarted_storage)
    restarted_svc = AppService(storage=restarted_storage, project_manager=restarted_pm)

    assert restarted_pm.active_project is not None
    assert restarted_pm.active_project.project_id == p2.project_id
    assert restarted_pm.active_project.elapsed_seconds == pytest.approx(
        second_session_elapsed,
        rel=0.2,
    )
    p1_reloaded = next(
        p for p in restarted_pm.projects if p.project_id == p1.project_id
    )
    assert p1_reloaded.elapsed_seconds == pytest.approx(first_session_elapsed, rel=0.2)
    persisted_timer_state = restarted_svc.load_timer_state()
    assert persisted_timer_state is not None
    assert persisted_timer_state["state"] == "stopped"


def test_project_and_sub_activity_lifecycle_preserves_tracked_time(
    tmp_path: Path,
) -> None:
    """User journey: create project/sub-activity, track time, archive/unarchive."""
    storage = Storage(tmp_path / "scenario_sub_activity.db")
    pm = ProjectManager(storage)
    svc = AppService(storage=storage, project_manager=pm)

    project = pm.add("Website Revamp", "qualification scenario")
    svc.switch_project(project.project_id)
    sub_mgr = SubActivityManager(storage, project.project_id)
    sub = sub_mgr.add("Wireframing", "initial UX wireframes")

    svc.save_elapsed(
        1800.0,
        sub_activity_id=sub.sub_activity_id,
        sub_activity_mgr=sub_mgr,
    )
    svc.add_daily_sub_activity_seconds(
        project.project_id,
        sub.sub_activity_id,
        "2026-03-30",
        1800.0,
    )

    pm.set_archived(project.project_id, True)
    archived_rows = storage.list_projects()
    archived_project = next(r for r in archived_rows if r["id"] == project.project_id)
    assert archived_project["archived"] is True

    pm.set_archived(project.project_id, False)
    sub_mgr.set_archived(sub.sub_activity_id, True)
    sub_mgr.set_archived(sub.sub_activity_id, False)

    subs = svc.list_sub_activities(project.project_id)
    sub_row = next(r for r in subs if r["id"] == sub.sub_activity_id)
    assert sub_row["archived"] is False
    assert sub_row["elapsed_seconds"] == pytest.approx(1800.0)

    by_sub = storage.get_date_range_sub_activity_data(
        date(2026, 3, 30),
        date(2026, 3, 30),
        project_ids=[project.project_id],
    )
    assert by_sub[project.project_id][sub.sub_activity_id][
        "2026-03-30"
    ] == pytest.approx(1800.0)


def test_export_import_keeps_report_totals_and_breakdowns_consistent(
    tmp_path: Path,
) -> None:
    """User journey: export from active DB, import into fresh DB, compare reports."""
    src_storage = Storage(tmp_path / "scenario_export_src.db")
    src_pm = ProjectManager(src_storage)

    p_a = src_pm.active_project
    assert p_a is not None
    p_b = src_pm.add("Client B", "")
    src_pm.switch(p_b.project_id)

    sa_mgr = SubActivityManager(src_storage, p_b.project_id)
    sa_b1 = sa_mgr.add("Implementation")
    sa_b2 = sa_mgr.add("QA")

    src_storage.add_daily_seconds(p_a.project_id, "2026-03-29", 1200.0)
    src_storage.add_daily_seconds(p_b.project_id, "2026-03-29", 3600.0)
    src_storage.add_daily_seconds(p_b.project_id, "2026-03-30", 1800.0)
    src_storage.add_daily_sub_activity_seconds(
        p_b.project_id,
        sa_b1.sub_activity_id,
        "2026-03-29",
        2400.0,
    )
    src_storage.add_daily_sub_activity_seconds(
        p_b.project_id,
        sa_b2.sub_activity_id,
        "2026-03-30",
        900.0,
    )

    export_path = tmp_path / "exports" / "scenario.json"
    src_storage.export_json(export_path)

    dst_storage = Storage(tmp_path / "scenario_export_dst.db")
    dst_storage.import_json(export_path)

    start = date(2026, 3, 29)
    end = date(2026, 3, 30)
    src_project_data = src_storage.get_date_range_data(start, end)
    dst_project_data = dst_storage.get_date_range_data(start, end)
    src_sub_data = src_storage.get_date_range_sub_activity_data(start, end)
    dst_sub_data = dst_storage.get_date_range_sub_activity_data(start, end)

    assert dst_project_data == src_project_data
    assert dst_sub_data == src_sub_data
    assert dst_storage.get_daily_total("2026-03-29") == pytest.approx(
        src_storage.get_daily_total("2026-03-29")
    )
