"""Application service for data import/export orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from src.app.services.widget_session_service import restore_saved_timer_state
from src.app_service import AppService
from src.projects import ProjectManager
from src.timer import Timer, TimerState
from src.ui.widget_controller import WidgetController


def export_data(
    *,
    export_path: Path,
    app_service: AppService,
    timer: Timer,
    controller: WidgetController,
) -> None:
    """Persist latest runtime state and export all app data to JSON."""
    app_service.save_timer_state(timer.elapsed, timer.state.value)
    controller.save_active_elapsed(timer.elapsed)
    controller.flush_daily_at(timer.elapsed)
    app_service.export_json(export_path)


def import_data(
    *,
    import_path: Path,
    app_service: AppService,
    project_manager: Optional[ProjectManager],
    timer: Timer,
    controller: Optional[WidgetController],
    load_sub_activities_for_project: Callable[[int], None],
    update_project_selector: Callable[[], None],
    refresh_today_base_total: Callable[..., None],
    apply_timer_display: Callable[[], None],
) -> None:
    """Import data and synchronize in-memory UI/runtime state."""
    app_service.backup()
    if timer.state in (TimerState.RUNNING, TimerState.PAUSED):
        timer.stop()

    app_service.import_json(import_path)

    if project_manager is None:
        return

    app_service.reload_projects()
    active = project_manager.active_project
    if active is not None:
        load_sub_activities_for_project(active.project_id)

    update_project_selector()

    restored = False
    if controller is not None:
        restored = restore_saved_timer_state(
            app_service=app_service,
            storage=None,
            timer=timer,
            controller=controller,
        )

    if not restored:
        if active and active.elapsed_seconds > 0:
            timer.restore(active.elapsed_seconds)
        else:
            timer.reset()

    refresh_today_base_total(force=True)
    apply_timer_display()
