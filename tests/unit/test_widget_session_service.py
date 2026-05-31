from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from src.app.services.widget_session_service import (
    restore_saved_timer_state,
    switch_active_project_session,
    switch_within_project_target_session,
)
from src.timer import TimerState


def test_restore_saved_timer_state_rejects_zero_stopped() -> None:
    app_service = Mock()
    app_service.load_timer_state.return_value = {
        "elapsed_seconds": 0.0,
        "state": "stopped",
    }
    storage = Mock()
    timer = Mock()
    timer.state = TimerState.IDLE
    controller = Mock()

    restored = restore_saved_timer_state(
        app_service=app_service,
        storage=storage,
        timer=timer,
        controller=controller,
    )

    assert restored is False
    timer.restore.assert_not_called()
    controller.set_daily_anchor.assert_not_called()


def test_restore_saved_timer_state_anchors_running() -> None:
    app_service = Mock()
    app_service.load_timer_state.return_value = {
        "elapsed_seconds": 42.0,
        "state": "running",
    }
    timer = Mock()
    timer.state = TimerState.RUNNING
    timer.elapsed = 42.0
    controller = Mock()

    restored = restore_saved_timer_state(
        app_service=app_service,
        storage=None,
        timer=timer,
        controller=controller,
    )

    assert restored is True
    timer.restore.assert_called_once_with(42.0, "running")
    controller.set_daily_anchor.assert_called_once()


def test_switch_active_project_session_stopped_saves_elapsed() -> None:
    project_manager = Mock()
    project_manager.active_project = SimpleNamespace(project_id=1)
    project_manager.switch.return_value = SimpleNamespace(elapsed_seconds=0.0)
    timer = Mock()
    timer.state = TimerState.STOPPED
    timer.elapsed = 120.0
    controller = Mock()
    load_sub_activities = Mock()

    switch_active_project_session(
        new_id=3,
        project_manager=project_manager,
        app_service=None,
        timer=timer,
        controller=controller,
        load_sub_activities_for_project=load_sub_activities,
    )

    controller.save_active_elapsed.assert_called_once_with(120.0)
    project_manager.switch.assert_called_once_with(3)
    load_sub_activities.assert_called_once_with(3)
    timer.reset.assert_called_once()
    timer.continue_from_stopped.assert_not_called()
    timer.start.assert_not_called()


def test_switch_active_project_session_running_autostarts_after_switch() -> None:
    project_manager = Mock()
    project_manager.active_project = SimpleNamespace(project_id=1)
    app_service = Mock()
    app_service.switch_project.return_value = SimpleNamespace(elapsed_seconds=15.0)

    timer = Mock()
    timer.state = TimerState.RUNNING
    # Simulate timer being stopped by timer.stop() before restart decision.
    timer.stop.side_effect = lambda: setattr(timer, "state", TimerState.STOPPED)

    controller = Mock()
    load_sub_activities = Mock()

    switch_active_project_session(
        new_id=9,
        project_manager=project_manager,
        app_service=app_service,
        timer=timer,
        controller=controller,
        load_sub_activities_for_project=load_sub_activities,
    )

    timer.stop.assert_called_once()
    app_service.switch_project.assert_called_once_with(9)
    timer.restore.assert_called_once_with(15.0)
    app_service.save_timer_state.assert_called_once_with(15.0, "stopped")
    timer.continue_from_stopped.assert_called_once()
    timer.start.assert_not_called()


def test_switch_within_project_target_session_stops_applies_target_and_restores() -> (
    None
):
    timer = Mock()
    timer.state = TimerState.RUNNING
    timer.stop.side_effect = lambda: setattr(timer, "state", TimerState.STOPPED)
    controller = Mock()
    app_service = Mock()
    target_state = {"sub_id": 1}

    switch_within_project_target_session(
        timer=timer,
        controller=controller,
        app_service=app_service,
        apply_target=lambda: target_state.update({"sub_id": 2}),
        target_elapsed_seconds=35.0,
    )

    assert target_state["sub_id"] == 2
    timer.stop.assert_called_once()
    controller.set_switching_project.assert_any_call(True)
    controller.set_switching_project.assert_any_call(False)
    timer.reset.assert_called_once()
    timer.restore.assert_called_once_with(35.0)
    app_service.save_timer_state.assert_called_once_with(35.0, "stopped")
    timer.continue_from_stopped.assert_called_once()
    timer.start.assert_not_called()


def test_switch_within_project_target_session_no_restore_when_elapsed_zero() -> None:
    timer = Mock()
    timer.state = TimerState.PAUSED
    controller = Mock()
    app_service = Mock()

    switch_within_project_target_session(
        timer=timer,
        controller=controller,
        app_service=app_service,
        apply_target=lambda: None,
        target_elapsed_seconds=0.0,
    )

    timer.stop.assert_called_once()
    timer.restore.assert_not_called()
    app_service.save_timer_state.assert_not_called()
    timer.continue_from_stopped.assert_not_called()
    timer.start.assert_not_called()
