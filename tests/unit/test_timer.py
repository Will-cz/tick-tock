"""Unit tests for Timer - no GUI required."""

import time

import pytest

from src.timer import Timer, TimerEvent, TimerState


class TestTimerInitialState:
    def test_initial_state_is_idle(self):
        assert Timer().state == TimerState.IDLE

    def test_initial_elapsed_is_zero(self):
        assert Timer().elapsed == 0.0


class TestTimerStart:
    def test_start_changes_state_to_running(self):
        timer = Timer()
        timer.start()
        assert timer.state == TimerState.RUNNING
        timer.stop()

    def test_start_fires_started_event(self):
        timer = Timer()
        events: list[TimerState] = []
        timer.on(TimerEvent.STARTED, lambda t: events.append(t.state))
        timer.start()
        timer.stop()
        assert TimerState.RUNNING in events

    def test_start_when_running_is_ignored(self):
        timer = Timer()
        timer.start()
        state_before = timer.state
        timer.start()
        assert timer.state == state_before
        timer.stop()

    def test_start_when_paused_is_ignored(self):
        timer = Timer()
        timer.start()
        timer.pause()
        timer.start()
        assert timer.state == TimerState.PAUSED
        timer.reset()

    def test_elapsed_increases_while_running(self):
        timer = Timer()
        timer.start()
        time.sleep(0.05)
        assert timer.elapsed > 0.0
        timer.stop()

    def test_can_restart_after_stop(self):
        timer = Timer()
        timer.start()
        timer.stop()
        timer.start()
        assert timer.state == TimerState.RUNNING
        timer.stop()

    def test_restart_resets_elapsed(self):
        timer = Timer()
        timer.start()
        time.sleep(0.05)
        timer.stop()
        timer.reset()
        timer.start()
        time.sleep(0.02)
        # elapsed should be close to 0.02, not accumulated from before
        assert timer.elapsed < 0.1
        timer.stop()


class TestTimerPause:
    def test_pause_changes_state(self):
        timer = Timer()
        timer.start()
        timer.pause()
        assert timer.state == TimerState.PAUSED

    def test_pause_fires_paused_event(self):
        timer = Timer()
        events: list[TimerState] = []
        timer.on(TimerEvent.PAUSED, lambda t: events.append(t.state))
        timer.start()
        timer.pause()
        assert TimerState.PAUSED in events

    def test_pause_idle_timer_is_ignored(self):
        timer = Timer()
        timer.pause()
        assert timer.state == TimerState.IDLE

    def test_pause_stopped_timer_is_ignored(self):
        timer = Timer()
        timer.start()
        timer.stop()
        timer.pause()
        assert timer.state == TimerState.STOPPED

    def test_elapsed_frozen_while_paused(self):
        timer = Timer()
        timer.start()
        time.sleep(0.05)
        timer.pause()
        elapsed_at_pause = timer.elapsed
        time.sleep(0.05)
        assert timer.elapsed == pytest.approx(elapsed_at_pause, abs=0.001)


class TestTimerResume:
    def test_resume_changes_state_to_running(self):
        timer = Timer()
        timer.start()
        timer.pause()
        timer.resume()
        assert timer.state == TimerState.RUNNING
        timer.stop()

    def test_resume_fires_resumed_event(self):
        timer = Timer()
        events: list[TimerState] = []
        timer.on(TimerEvent.RESUMED, lambda t: events.append(t.state))
        timer.start()
        timer.pause()
        timer.resume()
        timer.stop()
        assert TimerState.RUNNING in events

    def test_resume_running_timer_is_ignored(self):
        timer = Timer()
        timer.start()
        timer.resume()
        assert timer.state == TimerState.RUNNING
        timer.stop()

    def test_elapsed_accumulates_across_pause_resume(self):
        timer = Timer()
        timer.start()
        time.sleep(0.05)
        timer.pause()
        elapsed_after_first_run = timer.elapsed
        timer.resume()
        time.sleep(0.05)
        assert timer.elapsed > elapsed_after_first_run
        timer.stop()


class TestTimerStop:
    def test_stop_changes_state(self):
        timer = Timer()
        timer.start()
        timer.stop()
        assert timer.state == TimerState.STOPPED

    def test_stop_fires_stopped_event(self):
        timer = Timer()
        events: list[TimerState] = []
        timer.on(TimerEvent.STOPPED, lambda t: events.append(t.state))
        timer.start()
        timer.stop()
        assert TimerState.STOPPED in events

    def test_stop_idle_timer_is_ignored(self):
        timer = Timer()
        timer.stop()
        assert timer.state == TimerState.IDLE

    def test_stop_paused_timer_is_allowed(self):
        timer = Timer()
        timer.start()
        timer.pause()
        timer.stop()
        assert timer.state == TimerState.STOPPED

    def test_elapsed_preserved_after_stop(self):
        timer = Timer()
        timer.start()
        time.sleep(0.05)
        timer.stop()
        elapsed = timer.elapsed
        time.sleep(0.05)
        assert timer.elapsed == pytest.approx(elapsed, abs=0.001)


class TestTimerReset:
    def test_reset_clears_elapsed(self):
        timer = Timer()
        timer.start()
        time.sleep(0.05)
        timer.reset()
        assert timer.elapsed == 0.0

    def test_reset_changes_state_to_idle(self):
        timer = Timer()
        timer.start()
        timer.reset()
        assert timer.state == TimerState.IDLE

    def test_reset_fires_reset_event(self):
        timer = Timer()
        events: list[TimerState] = []
        timer.on(TimerEvent.RESET, lambda t: events.append(t.state))
        timer.start()
        timer.reset()
        assert TimerState.IDLE in events

    def test_can_start_again_after_reset(self):
        timer = Timer()
        timer.start()
        timer.stop()
        timer.reset()
        timer.start()
        assert timer.state == TimerState.RUNNING
        timer.stop()

    def test_reset_from_paused_state(self):
        timer = Timer()
        timer.start()
        timer.pause()
        timer.reset()
        assert timer.state == TimerState.IDLE
        assert timer.elapsed == 0.0


class TestTimerEvents:
    def test_multiple_callbacks_fire_in_order(self):
        timer = Timer()
        calls: list[str] = []
        timer.on(TimerEvent.STARTED, lambda t: calls.append("a"))
        timer.on(TimerEvent.STARTED, lambda t: calls.append("b"))
        timer.start()
        timer.stop()
        assert calls == ["a", "b"]

    def test_tick_events_fire_while_running(self):
        ticks: list[int] = []
        timer = Timer(tick_interval=0.1)
        timer.on(TimerEvent.TICK, lambda t: ticks.append(1))
        timer.start()
        time.sleep(0.45)
        timer.stop()
        assert len(ticks) >= 3

    def test_tick_events_stop_when_paused(self):
        ticks: list[int] = []
        timer = Timer(tick_interval=0.1)
        timer.on(TimerEvent.TICK, lambda t: ticks.append(1))
        timer.start()
        time.sleep(0.25)
        timer.pause()
        count_at_pause = len(ticks)
        time.sleep(0.3)
        assert len(ticks) == count_at_pause
        timer.reset()

    def test_tick_events_resume_after_resume(self):
        ticks: list[int] = []
        timer = Timer(tick_interval=0.1)
        timer.on(TimerEvent.TICK, lambda t: ticks.append(1))
        timer.start()
        time.sleep(0.15)
        timer.pause()
        count_at_pause = len(ticks)
        timer.resume()
        time.sleep(0.25)
        timer.stop()
        assert len(ticks) > count_at_pause


class TestTimerStopIdempotency:
    def test_stop_when_already_stopped_is_ignored(self):
        timer = Timer()
        timer.start()
        timer.stop()
        events: list[str] = []
        timer.on(TimerEvent.STOPPED, lambda t: events.append("stopped"))
        timer.stop()  # second stop - should be a no-op
        assert events == []

    def test_stop_does_not_alter_elapsed_when_already_stopped(self):
        timer = Timer()
        timer.start()
        time.sleep(0.05)
        timer.stop()
        elapsed_after_first_stop = timer.elapsed
        timer.stop()
        assert timer.elapsed == pytest.approx(elapsed_after_first_stop, abs=0.001)


class TestTimerRestore:
    def test_restore_sets_elapsed(self):
        timer = Timer()
        timer.restore(42.5)
        assert timer.elapsed == pytest.approx(42.5)

    def test_restore_puts_timer_in_stopped_state(self):
        timer = Timer()
        timer.restore(10.0)
        assert timer.state == TimerState.STOPPED

    def test_restore_clamps_negative_to_zero(self):
        timer = Timer()
        timer.restore(-5.0)
        assert timer.elapsed == 0.0

    def test_can_start_after_restore(self):
        timer = Timer()
        timer.restore(30.0)
        timer.start()
        assert timer.state == TimerState.RUNNING
        timer.stop()

    def test_restore_ignored_when_running(self):
        timer = Timer()
        timer.start()
        time.sleep(0.05)
        elapsed_before = timer.elapsed
        timer.restore(999.0)
        # elapsed should not have jumped to 999
        assert timer.elapsed < elapsed_before + 1.0
        timer.stop()

    def test_restore_ignored_when_paused(self):
        timer = Timer()
        timer.start()
        timer.pause()
        original_elapsed = timer.elapsed
        timer.restore(999.0)
        assert timer.elapsed == pytest.approx(original_elapsed, abs=0.001)
        timer.reset()

    def test_restore_from_idle_state(self):
        timer = Timer()
        assert timer.state == TimerState.IDLE
        timer.restore(5.0)
        assert timer.state == TimerState.STOPPED
        assert timer.elapsed == pytest.approx(5.0)

    def test_restore_from_stopped_state(self):
        timer = Timer()
        timer.start()
        timer.stop()
        timer.restore(100.0)
        assert timer.elapsed == pytest.approx(100.0)

    def test_restore_running_state_resumes_counting(self):
        timer = Timer(tick_interval=0.1)
        timer.restore(10.0, "running")
        assert timer.state == TimerState.RUNNING
        time.sleep(0.05)
        assert timer.elapsed > 10.0
        timer.stop()

    def test_restore_paused_state_preserves_elapsed(self):
        timer = Timer()
        timer.restore(33.0, "paused")
        assert timer.state == TimerState.PAUSED
        elapsed_before = timer.elapsed
        time.sleep(0.02)
        assert timer.elapsed == pytest.approx(elapsed_before, abs=0.001)
        timer.reset()


class TestTimerContinueFromStopped:
    def test_continue_changes_state_to_running(self):
        timer = Timer()
        timer.restore(60.0)
        timer.continue_from_stopped()
        assert timer.state == TimerState.RUNNING
        timer.stop()

    def test_continue_preserves_elapsed(self):
        timer = Timer()
        timer.restore(500.0)
        timer.continue_from_stopped()
        assert timer.elapsed == pytest.approx(500.0, abs=0.1)
        timer.stop()

    def test_continue_elapsed_keeps_increasing(self):
        timer = Timer()
        timer.restore(100.0)
        timer.continue_from_stopped()
        time.sleep(0.05)
        assert timer.elapsed > 100.0
        timer.stop()

    def test_continue_fires_resumed_event(self):
        timer = Timer()
        events: list[TimerState] = []
        timer.on(TimerEvent.RESUMED, lambda t: events.append(t.state))
        timer.restore(10.0)
        timer.continue_from_stopped()
        timer.stop()
        assert TimerState.RUNNING in events

    def test_continue_ignored_when_idle(self):
        timer = Timer()
        timer.continue_from_stopped()
        assert timer.state == TimerState.IDLE

    def test_continue_ignored_when_running(self):
        timer = Timer()
        timer.start()
        timer.continue_from_stopped()  # no-op
        assert timer.state == TimerState.RUNNING
        timer.stop()

    def test_continue_ignored_when_paused(self):
        timer = Timer()
        timer.start()
        timer.pause()
        timer.continue_from_stopped()  # no-op
        assert timer.state == TimerState.PAUSED
        timer.reset()

    def test_continue_from_zero_elapsed_still_runs(self):
        """continue_from_stopped works when elapsed is 0 (stop() right after start)."""
        timer = Timer()
        timer.start()
        timer.stop()
        # elapsed is near-zero but STOPPED state is valid
        timer.continue_from_stopped()
        assert timer.state == TimerState.RUNNING
        timer.stop()
