"""Session orchestration helpers shared by Tick-Tock widget flows."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Mapping, Optional

from src.app_service import AppService
from src.projects import Project, ProjectManager
from src.storage import Storage
from src.timer import Timer, TimerState
from src.ui.widget_controller import WidgetController


def restore_saved_timer_state(
    *,
    app_service: Optional[AppService],
    storage: Optional[Storage],
    timer: Timer,
    controller: WidgetController,
) -> bool:
    """Restore persisted timer state and re-anchor daily tracking when needed."""
    saved_timer_state: Optional[Mapping[str, object]] = None
    if app_service is not None:
        loaded = app_service.load_timer_state()
        if isinstance(loaded, dict):
            saved_timer_state = loaded
    elif storage is not None:
        loaded = storage.load_timer_state()
        if isinstance(loaded, dict):
            saved_timer_state = loaded

    if saved_timer_state is None:
        return False

    elapsed_raw = saved_timer_state.get("elapsed_seconds", 0.0)
    if isinstance(elapsed_raw, bool):
        elapsed = 0.0
    elif isinstance(elapsed_raw, (int, float, str)):
        try:
            elapsed = float(elapsed_raw)
        except ValueError:
            elapsed = 0.0
    else:
        elapsed = 0.0
    state = str(saved_timer_state.get("state", "stopped"))

    # Idle/stopped at zero has no visible startup effect.
    if elapsed <= 0 and state not in {"running", "paused"}:
        return False

    timer.restore(elapsed, state)

    # Anchor daily tracking so post-restart flushes only write new deltas.
    if timer.state in (TimerState.RUNNING, TimerState.PAUSED):
        controller.set_daily_anchor(
            timer.elapsed,
            datetime.now().strftime("%Y-%m-%d"),
        )

    return True


def switch_active_project_session(
    *,
    new_id: int,
    project_manager: ProjectManager,
    app_service: Optional[AppService],
    timer: Timer,
    controller: WidgetController,
    load_sub_activities_for_project: Callable[..., None],
) -> Project:
    """Persist current state, switch project context, and restore timer state."""
    active = project_manager.active_project
    was_running = timer.state == TimerState.RUNNING

    # Stop active timing so callbacks persist current target state.
    if timer.state in (TimerState.RUNNING, TimerState.PAUSED):
        timer.stop()
    elif timer.state == TimerState.STOPPED and active is not None:
        controller.save_active_elapsed(timer.elapsed)

    new_project = (
        app_service.switch_project(new_id)
        if app_service is not None
        else project_manager.switch(new_id)
    )
    load_sub_activities_for_project(new_id)

    # Reset without writing 0 to the new project.
    controller.set_switching_project(True)
    timer.reset()
    controller.set_switching_project(False)

    if new_project.elapsed_seconds > 0:
        timer.restore(new_project.elapsed_seconds)
        if app_service is not None:
            app_service.save_timer_state(new_project.elapsed_seconds, "stopped")

    # Preserve "auto-run on switch" behavior.
    if was_running:
        if timer.state == TimerState.STOPPED:
            timer.continue_from_stopped()
        else:
            timer.start()

    return new_project


def switch_within_project_target_session(
    *,
    timer: Timer,
    controller: WidgetController,
    app_service: Optional[AppService],
    apply_target: Callable[[], None],
    target_elapsed_seconds: float,
) -> None:
    """Switch tracking target within the same project without data loss.

    The sequence intentionally stops the timer before applying the new target so
    persistence callbacks can flush elapsed time to the old target, then performs
    a guarded reset/restore into the new target.
    """
    was_running = timer.state == TimerState.RUNNING

    if timer.state in (TimerState.RUNNING, TimerState.PAUSED):
        timer.stop()

    apply_target()

    controller.set_switching_project(True)
    timer.reset()
    controller.set_switching_project(False)

    if target_elapsed_seconds > 0:
        timer.restore(target_elapsed_seconds)
        if app_service is not None:
            app_service.save_timer_state(target_elapsed_seconds, "stopped")

    if was_running:
        if timer.state == TimerState.STOPPED:
            timer.continue_from_stopped()
        else:
            timer.start()
