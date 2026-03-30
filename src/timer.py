"""Timer logic for Tick-Tock Widget — no GUI dependencies."""

import threading
import time
import logging
from collections.abc import Callable
from enum import Enum
from typing import Optional


class TimerState(Enum):
    """Timer lifecycle states used by UI and persistence logic."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class TimerEvent(Enum):
    """Events emitted by Timer to subscribed callbacks."""

    STARTED = "started"
    PAUSED = "paused"
    RESUMED = "resumed"
    STOPPED = "stopped"
    RESET = "reset"
    TICK = "tick"


class Timer:
    """Pure timer logic with a simple event/callback system.

    No GUI dependencies — safe to use in tests and headless environments.

    Usage::

        timer = Timer()
        timer.on(TimerEvent.TICK, lambda t: print(f"Elapsed: {t.elapsed:.1f}s"))
        timer.start()
        ...
        timer.stop()
    """

    def __init__(self, tick_interval: float = 1.0) -> None:
        self._logger = logging.getLogger(__name__)
        self._state = TimerState.IDLE
        self._start_time: Optional[float] = None
        self._elapsed_before_pause: float = 0.0
        self._tick_interval = tick_interval
        self._callbacks: dict[TimerEvent, list[Callable[["Timer"], None]]] = {
            event: [] for event in TimerEvent
        }
        self._tick_thread: Optional[threading.Thread] = None
        self._stop_tick: Optional[threading.Event] = None
        self._tick_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> TimerState:
        """Return the current timer lifecycle state."""
        return self._state

    @property
    def elapsed(self) -> float:
        """Elapsed time in seconds (excludes time spent paused)."""
        if self._state == TimerState.RUNNING and self._start_time is not None:
            return self._elapsed_before_pause + (time.monotonic() - self._start_time)
        return self._elapsed_before_pause

    def on(self, event: TimerEvent, callback: Callable[["Timer"], None]) -> None:
        """Register a callback for a timer event."""
        self._callbacks[event].append(callback)

    def start(self) -> None:
        """Start timer from scratch. Ignored if already running or paused."""
        if self._state not in (TimerState.IDLE, TimerState.STOPPED):
            return
        self._elapsed_before_pause = 0.0
        self._start_time = time.monotonic()
        self._state = TimerState.RUNNING
        self._emit(TimerEvent.STARTED)
        self._start_tick_thread()

    def pause(self, *, preserve_elapsed: bool = False) -> None:
        """Pause a running timer. Ignored if not running."""
        if self._state != TimerState.RUNNING:
            return
        pause_time = time.monotonic()
        self._stop_tick_thread()
        if not preserve_elapsed:
            self._elapsed_before_pause += (
                pause_time - self._start_time  # type: ignore[operator]
            )
        self._start_time = None
        self._state = TimerState.PAUSED
        self._emit(TimerEvent.PAUSED)

    def resume(self) -> None:
        """Resume a paused timer. Ignored if not paused."""
        if self._state != TimerState.PAUSED:
            return
        self._start_time = time.monotonic()
        self._state = TimerState.RUNNING
        self._emit(TimerEvent.RESUMED)
        self._start_tick_thread()

    def stop(self) -> None:
        """Stop the timer, preserving elapsed time. Ignored if idle or stopped."""
        if self._state in (TimerState.IDLE, TimerState.STOPPED):
            return
        self._stop_tick_thread()
        if self._state == TimerState.RUNNING and self._start_time is not None:
            self._elapsed_before_pause += time.monotonic() - self._start_time
        self._start_time = None
        self._state = TimerState.STOPPED
        self._emit(TimerEvent.STOPPED)

    def reset(self) -> None:
        """Stop the timer and reset elapsed time to zero."""
        self._stop_tick_thread()
        self._state = TimerState.IDLE
        self._start_time = None
        self._elapsed_before_pause = 0.0
        self._emit(TimerEvent.RESET)

    def restore(self, elapsed: float, state: str = "stopped") -> None:
        """Restore a previously saved elapsed time and timer state.

        ``state`` may be ``"idle"``, ``"running"``, ``"paused"``, or
        ``"stopped"``. Invalid values are treated as ``"stopped"``.

        Call this on startup to resume from where the app was closed.
        Ignored if the timer is currently running or paused.
        """
        if self._state in (TimerState.RUNNING, TimerState.PAUSED):
            return
        # Ensure no stale tick thread remains attached before restoring state.
        self._stop_tick_thread()
        self._elapsed_before_pause = max(0.0, elapsed)
        state_name = str(state).lower()
        valid_states = {s.value for s in TimerState}
        if state_name not in valid_states:
            state_name = TimerState.STOPPED.value
        # Avoid inconsistent "idle with elapsed" restore payloads.
        if state_name == TimerState.IDLE.value and self._elapsed_before_pause > 0:
            state_name = TimerState.STOPPED.value

        restored_state = TimerState(state_name)
        self._state = restored_state
        if restored_state == TimerState.RUNNING:
            self._start_time = time.monotonic()
            self._start_tick_thread()
        else:
            self._start_time = None

    def continue_from_stopped(self) -> None:
        """Resume counting from a STOPPED state without resetting accumulated elapsed.

        Unlike ``start()``, which always resets elapsed to zero, this method
        continues from the current ``elapsed`` value.  Emits ``RESUMED`` so
        that storage and daily-tracking callbacks update correctly.

        Ignored if the timer is not in the STOPPED state.
        """
        if self._state != TimerState.STOPPED:
            return
        self._start_time = time.monotonic()
        self._state = TimerState.RUNNING
        self._emit(TimerEvent.RESUMED)
        self._start_tick_thread()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit(self, event: TimerEvent) -> None:
        for callback in self._callbacks[event]:
            try:
                callback(self)
            except Exception:  # pylint: disable=broad-except
                # Isolate callback failures so one bad subscriber does not
                # break timer state transitions or kill the tick thread.
                self._logger.exception("Timer callback failed for event %s", event)

    def _start_tick_thread(self) -> None:
        # Ensure any previous thread is signalled before starting a fresh one.
        self._stop_tick_thread()
        stop_event = threading.Event()
        thread = threading.Thread(
            target=self._tick_loop,
            args=(stop_event,),
            daemon=True,
        )
        with self._tick_lock:
            self._stop_tick = stop_event
            self._tick_thread = thread
        thread.start()

    def _stop_tick_thread(self) -> None:
        with self._tick_lock:
            stop_event = self._stop_tick
            thread = self._tick_thread
            # Clear references first so re-entrant calls see a stopped state.
            self._stop_tick = None
            self._tick_thread = None
        if stop_event is not None:
            stop_event.set()
        if thread is not None and thread.is_alive():
            thread.join(timeout=self._tick_interval * 2)

    def _tick_loop(self, stop_event: threading.Event) -> None:
        # Use monotonic deadlines so callback runtime does not steadily drift
        # tick cadence later and later over long sessions.
        next_deadline = time.monotonic() + self._tick_interval
        while True:
            wait_for = max(0.0, next_deadline - time.monotonic())
            if stop_event.wait(wait_for):
                break
            if self._state == TimerState.RUNNING:
                self._emit(TimerEvent.TICK)
            next_deadline += self._tick_interval
            # If the callback workload overran badly, resync instead of
            # firing several immediate catch-up ticks back-to-back.
            now = time.monotonic()
            if now - next_deadline > self._tick_interval:
                next_deadline = now + self._tick_interval
