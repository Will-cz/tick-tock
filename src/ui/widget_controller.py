"""WidgetController — timer-event handler and persistence coordinator.

Contains zero tkinter imports; fully testable without a display.
The controller owns the timer-event-driven state (tick counter, daily elapsed
tracking, project-switch flag) and delegates all persistence to :class:`AppService`.
The hosting widget supplies an ``active_sub_callback`` so the controller can
route elapsed saves to the correct target without holding UI state directly.
"""

import logging
import threading
from datetime import datetime
from typing import Callable, Optional, Tuple

from src.app_service import AppService
from src.config import Config
from src.projects import ProjectManager
from src.sub_activities import SubActivityManager
from src.timer import Timer, TimerState

logger = logging.getLogger(__name__)


class WidgetController:
    """Coordinates timer events with AppService persistence.

    Responsibilities
    ----------------
    * Persist timer state on every timer event (started, paused, …).
    * Log activity events (start, pause, resume, stop, reset).
    * Track daily elapsed time and flush it to storage on each stop/pause.
    * Route elapsed saves to the active sub-activity or project.
    * Expose config-derived settings (autosave interval, rounding, backup count).

    The controller has **no tkinter imports** and can be unit-tested without a
    display.  All Tkinter-specific logic stays in :class:`TickTockWidget`.
    """

    def __init__(
        self,
        app_service: Optional[AppService],
        project_manager: Optional[ProjectManager],
        config: Optional[Config] = None,
        active_sub_callback: Optional[
            Callable[[], Tuple[Optional[int], Optional[SubActivityManager]]]
        ] = None,
        daily_flush_callback: Optional[Callable[[str, int, float], None]] = None,
    ) -> None:
        self._svc = app_service
        self._project_mgr = project_manager
        self._config = config
        # Callback that returns (active_sub_activity_id, sub_activity_mgr) from
        # the hosting widget at the time the callback is invoked.
        self._get_active_sub = active_sub_callback or (lambda: (None, None))
        self._on_daily_flushed = daily_flush_callback
        self._state_lock = threading.RLock()

        # --- Mutable controller state (owned here, not on the widget) ---
        self.tick_count: int = 0
        self.last_saved_daily_elapsed: float = 0.0
        self.current_date: str = datetime.now().strftime("%Y-%m-%d")
        self.switching_project: bool = False

    # ------------------------------------------------------------------
    # Timer event handlers (called directly from timer callbacks)
    # ------------------------------------------------------------------

    def on_started(self, timer: Timer) -> None:
        """Handle timer start: persist state and reset daily session anchors."""
        with self._state_lock:
            if self._svc is not None:
                self._svc.save_timer_state(timer.elapsed, "running")
                self._svc.log_activity("start", self.active_project_name())
            # timer.start() always resets elapsed to 0; start a fresh daily session.
            self.tick_count = 0
            self.last_saved_daily_elapsed = 0.0
            self.current_date = datetime.now().strftime("%Y-%m-%d")

    def on_paused(self, timer: Timer) -> None:
        """Handle timer pause: persist state and flush daily delta."""
        with self._state_lock:
            if self._svc is not None:
                self._svc.save_timer_state(timer.elapsed, "paused")
                self._svc.log_activity("pause", self.active_project_name())
            self.flush_daily_at(timer.elapsed)

    def on_resumed(self, timer: Timer) -> None:
        """Handle timer resume: persist state and re-anchor daily baseline."""
        with self._state_lock:
            if self._svc is not None:
                self._svc.save_timer_state(timer.elapsed, "running")
                self._svc.log_activity("resume", self.active_project_name())
            # Update date in case it changed while paused/stopped.
            self.current_date = datetime.now().strftime("%Y-%m-%d")
            # Anchor daily delta so we only count time from this point forward.
            self.last_saved_daily_elapsed = timer.elapsed

    def on_stopped(self, timer: Timer) -> None:
        """Handle timer stop: persist elapsed and flush pending daily delta."""
        with self._state_lock:
            if self._svc is not None:
                self._svc.save_timer_state(timer.elapsed, "stopped")
                self._svc.log_activity("stop", self.active_project_name())
            # Persist elapsed to the active sub-activity or project.
            self.save_active_elapsed(timer.elapsed)
            # Flush any running segment to today's log.
            self.flush_daily_at(timer.elapsed)

    def on_reset(self, _timer: Timer) -> None:
        """Handle timer reset and clear persisted state."""
        with self._state_lock:
            if self._svc is not None:
                self._svc.clear_timer_state()
                if not self.switching_project:
                    self._svc.log_activity("reset", self.active_project_name())
            # Reset the active tracking target's elapsed to zero (user-initiated only).
            if not self.switching_project:
                self.save_active_elapsed(0.0)
            # timer.elapsed is 0 after reset; sync daily tracker.
            self.tick_count = 0
            self.last_saved_daily_elapsed = 0.0

    def on_tick(self, timer: Timer) -> None:
        """Periodically persist running timer state to survive a force-close."""
        with self._state_lock:
            # Timer callbacks can race with pause/stop transitions when a previous
            # tick callback is still unwinding. Ignore stale tick deliveries.
            timer_state = getattr(timer, "state", TimerState.RUNNING)
            if timer_state != TimerState.RUNNING:
                return
            # Roll daily tracking when crossing midnight during long running
            # sessions so time is written to the correct calendar date.
            now_date = datetime.now().strftime("%Y-%m-%d")
            if now_date != self.current_date:
                self.flush_daily_at(timer.elapsed)
                self.current_date = now_date
            self.tick_count += 1
            if self.tick_count % self.get_autosave_interval_ticks() == 0:
                # Keep daily logs crash-resilient by checkpointing the in-progress
                # segment on the same cadence as periodic state autosave.
                self.flush_daily_at(timer.elapsed)
                if self._svc is not None:
                    self._svc.save_timer_state(timer.elapsed, "running")
                self.save_active_elapsed(timer.elapsed)

    # ------------------------------------------------------------------
    # Daily time tracking
    # ------------------------------------------------------------------

    def flush_daily_at(self, elapsed: float) -> None:
        """Persist unsaved seconds from the current running segment to daily log."""
        with self._state_lock:
            if self._svc is None or self._project_mgr is None:
                return
            active = self._project_mgr.active_project
            if active is None:
                return
            delta = elapsed - self.last_saved_daily_elapsed
            if delta > 0:
                self._svc.add_daily_seconds(active.project_id, self.current_date, delta)
                sub_id, _sub_mgr = self._get_active_sub()
                if sub_id is not None:
                    self._svc.add_daily_sub_activity_seconds(
                        active.project_id,
                        sub_id,
                        self.current_date,
                        delta,
                    )
                if self._on_daily_flushed is not None:
                    try:
                        self._on_daily_flushed(
                            self.current_date,
                            active.project_id,
                            delta,
                        )
                    except Exception:  # pylint: disable=broad-except
                        logger.exception("Daily flush callback failed")
            self.last_saved_daily_elapsed = elapsed

    def set_switching_project(self, switching: bool) -> None:
        """Set internal guard flag used during project-switch resets."""
        with self._state_lock:
            self.switching_project = switching

    def get_last_saved_daily_elapsed(self) -> float:
        """Return elapsed baseline already flushed to daily logs."""
        with self._state_lock:
            return self.last_saved_daily_elapsed

    def set_daily_anchor(
        self, elapsed: float, current_date: Optional[str] = None
    ) -> None:
        """Synchronize daily-tracking baseline values as one atomic update."""
        with self._state_lock:
            self.last_saved_daily_elapsed = elapsed
            if current_date is not None:
                self.current_date = current_date

    def handle_midnight_rollover(self, elapsed: float, now_date: str) -> None:
        """Flush elapsed and roll internal date when a day boundary is crossed."""
        with self._state_lock:
            if now_date == self.current_date:
                return
            self.flush_daily_at(elapsed)
            self.current_date = now_date

    # ------------------------------------------------------------------
    # Elapsed routing
    # ------------------------------------------------------------------

    def save_active_elapsed(self, elapsed: float) -> None:
        """Save *elapsed* (with optional rounding) to the active target."""
        if self._svc is None:
            return
        rounded = self.round_elapsed(elapsed)
        sub_id, sub_mgr = self._get_active_sub()
        self._svc.save_elapsed(
            rounded, sub_activity_id=sub_id, sub_activity_mgr=sub_mgr
        )

    # ------------------------------------------------------------------
    # Config-derived settings
    # ------------------------------------------------------------------

    def get_autosave_interval_ticks(self) -> int:
        """Return periodic save interval in ticks (seconds)."""
        if self._config is None:
            return 60
        minutes = int(self._config.get_timer_setting("autosave_interval_minutes", 1))
        return max(1, minutes * 60)

    def round_elapsed(self, elapsed: float) -> float:
        """Round *elapsed* seconds to the nearest configured minute increment."""
        if self._config is None:
            return elapsed
        rounding = int(self._config.get_timer_setting("time_rounding_minutes", 0))
        if rounding <= 0:
            return elapsed
        round_secs = rounding * 60
        return round(elapsed / round_secs) * round_secs

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def active_project_name(self) -> str:
        """Return active project name for activity-log labeling."""
        if self._project_mgr and self._project_mgr.active_project:
            return self._project_mgr.active_project.name
        return "default"
