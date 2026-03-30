from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from src.app.services.data_transfer_service import export_data, import_data
from src.timer import TimerState


def test_export_data_persists_and_exports(tmp_path) -> None:
    app_service = Mock()
    controller = Mock()
    timer = SimpleNamespace(elapsed=123.0, state=SimpleNamespace(value="running"))
    export_path = tmp_path / "export.json"

    export_data(
        export_path=export_path,
        app_service=app_service,
        timer=timer,
        controller=controller,
    )

    app_service.save_timer_state.assert_called_once_with(123.0, "running")
    controller.save_active_elapsed.assert_called_once_with(123.0)
    controller.flush_daily_at.assert_called_once_with(123.0)
    app_service.export_json.assert_called_once_with(export_path)


def test_import_data_stops_running_timer_and_refreshes_ui(tmp_path) -> None:
    app_service = Mock()
    active_project = SimpleNamespace(project_id=7, elapsed_seconds=55.0)
    project_manager = SimpleNamespace(active_project=active_project)

    timer = Mock()
    timer.state = TimerState.RUNNING

    load_sub_activities_for_project = Mock()
    update_project_selector = Mock()
    refresh_today_base_total = Mock()
    apply_timer_display = Mock()

    import_data(
        import_path=tmp_path / "import.json",
        app_service=app_service,
        project_manager=project_manager,
        timer=timer,
        controller=None,
        load_sub_activities_for_project=load_sub_activities_for_project,
        update_project_selector=update_project_selector,
        refresh_today_base_total=refresh_today_base_total,
        apply_timer_display=apply_timer_display,
    )

    app_service.backup.assert_called_once()
    timer.stop.assert_called_once()
    app_service.import_json.assert_called_once()
    app_service.reload_projects.assert_called_once()
    load_sub_activities_for_project.assert_called_once_with(7)
    update_project_selector.assert_called_once()
    timer.restore.assert_called_once_with(55.0)
    timer.reset.assert_not_called()
    refresh_today_base_total.assert_called_once_with(force=True)
    apply_timer_display.assert_called_once()


def test_import_data_with_no_project_manager_imports_only(tmp_path) -> None:
    app_service = Mock()
    timer = Mock()
    timer.state = TimerState.STOPPED

    load_sub_activities_for_project = Mock()
    update_project_selector = Mock()
    refresh_today_base_total = Mock()
    apply_timer_display = Mock()

    import_data(
        import_path=tmp_path / "import.json",
        app_service=app_service,
        project_manager=None,
        timer=timer,
        controller=None,
        load_sub_activities_for_project=load_sub_activities_for_project,
        update_project_selector=update_project_selector,
        refresh_today_base_total=refresh_today_base_total,
        apply_timer_display=apply_timer_display,
    )

    app_service.backup.assert_called_once()
    timer.stop.assert_not_called()
    app_service.import_json.assert_called_once()
    app_service.reload_projects.assert_not_called()
    load_sub_activities_for_project.assert_not_called()
    update_project_selector.assert_not_called()
    timer.restore.assert_not_called()
    timer.reset.assert_not_called()
    refresh_today_base_total.assert_not_called()
    apply_timer_display.assert_not_called()


def test_import_data_prefers_imported_timer_state_when_controller_present(
    tmp_path,
) -> None:
    app_service = Mock()
    app_service.load_timer_state.return_value = {
        "elapsed_seconds": 77.0,
        "state": "paused",
        "saved_at": "2026-04-12T10:00:00",
    }
    active_project = SimpleNamespace(project_id=3, elapsed_seconds=15.0)
    project_manager = SimpleNamespace(active_project=active_project)

    timer = Mock()
    timer.state = TimerState.STOPPED

    controller = Mock()
    load_sub_activities_for_project = Mock()
    update_project_selector = Mock()
    refresh_today_base_total = Mock()
    apply_timer_display = Mock()

    import_data(
        import_path=tmp_path / "import.json",
        app_service=app_service,
        project_manager=project_manager,
        timer=timer,
        controller=controller,
        load_sub_activities_for_project=load_sub_activities_for_project,
        update_project_selector=update_project_selector,
        refresh_today_base_total=refresh_today_base_total,
        apply_timer_display=apply_timer_display,
    )

    timer.restore.assert_called_once_with(77.0, "paused")
    timer.reset.assert_not_called()
