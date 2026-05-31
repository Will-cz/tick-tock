"""Timer-state persistence mixin for :class:`src.storage.Storage`."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from typing import Any, ContextManager, Optional, Protocol, cast

logger = logging.getLogger(__name__)


class _TimerStateStorage(Protocol):
    def connect(self) -> ContextManager[sqlite3.Connection]:
        """Yield a DB connection context."""
        raise NotImplementedError

    def sanitize_elapsed_for_write(self, value: object, field_name: str) -> int:
        """Validate elapsed values before writing to persistence."""
        raise NotImplementedError

    def sanitize_timer_state_for_write(self, state: object) -> str:
        """Normalize timer state values before writing to persistence."""
        raise NotImplementedError


class TimerStateMixin:
    """Mixin providing timer-state read/write methods."""

    def save_timer_state(self: _TimerStateStorage, elapsed: float, state: str) -> None:
        """Persist current timer state (overwrites any previous row)."""
        clean_elapsed = self.sanitize_elapsed_for_write(
            elapsed, "timer_state.elapsed_seconds"
        )
        clean_state = self.sanitize_timer_state_for_write(state)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO timer_state
                    (id, elapsed_seconds, state, saved_at)
                VALUES (1, ?, ?, ?)
                """,
                (clean_elapsed, clean_state, datetime.now().isoformat()),
            )

    def load_timer_state(self: _TimerStateStorage) -> Optional[dict[str, Any]]:
        """Return the last saved timer state, or ``None`` if nothing saved yet.

        Invalid field values are replaced with safe defaults and a warning is
        logged rather than raising an exception (graceful data recovery).
        """
        with self.connect() as conn:
            row = cast(
                Optional[tuple[Any, Any, Any]],
                conn.execute(
                    "SELECT elapsed_seconds, state, saved_at"
                    " FROM timer_state WHERE id = 1"
                ).fetchone(),
            )
        if row is None:
            return None
        elapsed = row[0]
        state_raw = row[1]
        if not isinstance(elapsed, (int, float)) or elapsed < 0 or elapsed != elapsed:
            logger.warning("Invalid elapsed_seconds %r in DB, resetting to 0", elapsed)
            elapsed = 0.0
        state = str(state_raw)
        _valid_states = {"idle", "running", "paused", "stopped"}
        if state not in _valid_states:
            logger.warning("Invalid timer state %r in DB, treating as stopped", state)
            state = "stopped"
        return {"elapsed_seconds": elapsed, "state": state, "saved_at": row[2]}

    def clear_timer_state(self: _TimerStateStorage) -> None:
        """Remove the saved timer state (e.g. after a reset)."""
        with self.connect() as conn:
            conn.execute("DELETE FROM timer_state WHERE id = 1")
