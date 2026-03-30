"""Today-total display helpers for the Tick-Tock widget."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.app_service import AppService


@dataclass
class TodayTotalCache:
    """Mutable cache for the active project's persisted today-total."""

    base_total: float = 0.0
    date: Optional[str] = None
    project_id: Optional[int] = None
    last_refresh: Optional[datetime] = None


_REFRESH_INTERVAL_SECONDS: float = 30.0


def refresh_today_total(
    *,
    cache: TodayTotalCache,
    app_service: "AppService",
    active_project_id: Optional[int],
    force: bool = False,
    refresh_interval_seconds: float = _REFRESH_INTERVAL_SECONDS,
) -> None:
    """Query storage and update *cache* when stale or forced.

    Throttled to one DB query per *refresh_interval_seconds* unless *force* is
    ``True`` or the active project or calendar date has changed.
    """
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    should_refresh = (
        force
        or cache.date != today
        or cache.project_id != active_project_id
        or cache.last_refresh is None
        or (now - cache.last_refresh).total_seconds() >= refresh_interval_seconds
    )
    if not should_refresh:
        return

    if active_project_id is None:
        cache.base_total = 0.0
    else:
        cache.base_total = app_service.storage.get_daily_total(
            today,
            project_id=active_project_id,
        )
    cache.date = today
    cache.project_id = active_project_id
    cache.last_refresh = now


def compute_today_display_total(
    *,
    cache: TodayTotalCache,
    timer_running: bool,
    timer_elapsed: float,
    last_saved_daily_elapsed: float,
) -> float:
    """Return the value to display: persisted base plus any live in-progress delta."""
    total = cache.base_total
    if timer_running:
        in_progress = timer_elapsed - last_saved_daily_elapsed
        if in_progress > 0:
            total += in_progress
    return total


def on_daily_flushed(
    *,
    cache: TodayTotalCache,
    date_str: str,
    project_id: int,
    delta: float,
) -> None:
    """Update *cache* incrementally when the controller flushes a daily segment."""
    if delta <= 0:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    if date_str != today or cache.project_id != project_id:
        return
    if cache.date != today:
        # Cache is stale for today; let the next refresh_today_total call re-sync.
        return
    cache.base_total += delta
