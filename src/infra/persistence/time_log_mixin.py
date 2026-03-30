"""Daily time-log persistence mixin for :class:`src.storage.Storage`."""

from __future__ import annotations

import calendar
import sqlite3
from datetime import date
from typing import Any, ContextManager, Optional, Protocol, cast


class _TimeLogStorage(Protocol):
    def connect(self) -> ContextManager[sqlite3.Connection]:
        """Yield a DB connection context."""
        raise NotImplementedError

    def get_date_range_data(
        self,
        start_date: date,
        end_date: date,
        project_ids: Optional[list[int]] = None,
    ) -> dict[int, dict[str, float]]:
        """Return project totals in a date range."""
        raise NotImplementedError

    def get_date_range_sub_activity_data(
        self,
        start_date: date,
        end_date: date,
        project_ids: Optional[list[int]] = None,
    ) -> dict[int, dict[int, dict[str, float]]]:
        """Return sub-activity totals in a date range."""
        raise NotImplementedError


class TimeLogMixin:
    """Mixin providing daily time-log read/write methods."""

    def add_daily_seconds(
        self: _TimeLogStorage, project_id: int, date_str: str, seconds: float
    ) -> None:
        """Add *seconds* to today's total for *project_id* on *date* (YYYY-MM-DD).

        Accumulates — safe to call multiple times per session.
        """
        if seconds <= 0:
            return
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO daily_time_log (date, project_id, seconds)"
                " VALUES (?, ?, ?)"
                " ON CONFLICT (date, project_id)"
                " DO UPDATE SET seconds = seconds + excluded.seconds",
                (date_str, project_id, seconds),
            )

    def add_daily_sub_activity_seconds(
        self: _TimeLogStorage,
        project_id: int,
        sub_activity_id: int,
        date_str: str,
        seconds: float,
    ) -> None:
        """Add *seconds* to sub-activity total for *date* (YYYY-MM-DD)."""
        if seconds <= 0:
            return
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO daily_sub_time_log"
                " (date, project_id, sub_activity_id, seconds)"
                " VALUES (?, ?, ?, ?)"
                " ON CONFLICT (date, sub_activity_id)"
                " DO UPDATE SET seconds = seconds + excluded.seconds",
                (date_str, project_id, sub_activity_id, seconds),
            )

    def get_daily_total(
        self: _TimeLogStorage, date_str: str, project_id: Optional[int] = None
    ) -> float:
        """Return total seconds logged on *date*.

        When *project_id* is provided, only that project's daily total is
        returned. Otherwise, totals across all projects are summed.
        """
        with self.connect() as conn:
            if project_id is None:
                row = cast(
                    Optional[tuple[Any]],
                    conn.execute(
                        "SELECT SUM(seconds) FROM daily_time_log WHERE date = ?",
                        (date_str,),
                    ).fetchone(),
                )
            else:
                row = cast(
                    Optional[tuple[Any]],
                    conn.execute(
                        "SELECT SUM(seconds) FROM daily_time_log"
                        " WHERE date = ? AND project_id = ?",
                        (date_str, project_id),
                    ).fetchone(),
                )
        if row is None or not row:
            return 0.0
        value = row[0]
        return float(value) if isinstance(value, (int, float)) else 0.0

    def get_daily_seconds_by_project(
        self: _TimeLogStorage, date_str: str
    ) -> dict[int, float]:
        """Return a mapping of {project_id: seconds} for *date*."""
        with self.connect() as conn:
            rows = cast(
                list[tuple[Any, Any]],
                conn.execute(
                    "SELECT project_id, seconds FROM daily_time_log WHERE date = ?",
                    (date_str,),
                ).fetchall(),
            )
        return {int(r[0]): float(r[1]) for r in rows}

    def get_monthly_data(
        self: _TimeLogStorage,
        year: int,
        month: int,
        project_ids: Optional[list[int]] = None,
    ) -> dict[int, dict[str, float]]:
        """Return ``{project_id: {date_str: seconds}}`` for the given month.

        *date_str* keys are ISO-format strings (``"YYYY-MM-DD"``).
        """
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        return self.get_date_range_data(start, end, project_ids=project_ids)

    def get_date_range_data(
        self: _TimeLogStorage,
        start_date: date,
        end_date: date,
        project_ids: Optional[list[int]] = None,
    ) -> dict[int, dict[str, float]]:
        """Return ``{project_id: {date_str: seconds}}`` for [start_date, end_date].

        *date_str* keys are ISO-format strings (``"YYYY-MM-DD"``).
        """
        if start_date > end_date:
            return {}

        params: list[object] = [start_date.isoformat(), end_date.isoformat()]
        query = (
            "SELECT project_id, date, seconds FROM daily_time_log"
            " WHERE date >= ? AND date <= ?"
        )
        if project_ids is not None:
            if not project_ids:
                return {}
            placeholders = ",".join("?" * len(project_ids))
            query += f" AND project_id IN ({placeholders})"
            params.extend(project_ids)
        query += " ORDER BY project_id, date"

        with self.connect() as conn:
            rows = cast(
                list[tuple[Any, Any, Any]],
                conn.execute(query, params).fetchall(),
            )

        result: dict[int, dict[str, float]] = {}
        for project_id, date_str, seconds in rows:
            result.setdefault(int(project_id), {})[str(date_str)] = float(seconds)
        return result

    def get_date_range_sub_activity_data(
        self: _TimeLogStorage,
        start_date: date,
        end_date: date,
        project_ids: Optional[list[int]] = None,
    ) -> dict[int, dict[int, dict[str, float]]]:
        """Return ``{project_id: {sub_id: {date_str: seconds}}}`` for date range."""
        if start_date > end_date:
            return {}

        params: list[object] = [start_date.isoformat(), end_date.isoformat()]
        query = (
            "SELECT project_id, sub_activity_id, date, seconds FROM daily_sub_time_log"
            " WHERE date >= ? AND date <= ?"
        )
        if project_ids is not None:
            if not project_ids:
                return {}
            placeholders = ",".join("?" * len(project_ids))
            query += f" AND project_id IN ({placeholders})"
            params.extend(project_ids)
        query += " ORDER BY project_id, sub_activity_id, date"

        with self.connect() as conn:
            rows = cast(
                list[tuple[Any, Any, Any, Any]],
                conn.execute(query, params).fetchall(),
            )

        result: dict[int, dict[int, dict[str, float]]] = {}
        for project_id, sub_id, date_str, seconds in rows:
            project_bucket = result.setdefault(int(project_id), {})
            sub_bucket = project_bucket.setdefault(int(sub_id), {})
            sub_bucket[str(date_str)] = float(seconds)
        return result

    def get_monthly_sub_activity_data(
        self: _TimeLogStorage,
        year: int,
        month: int,
        project_ids: Optional[list[int]] = None,
    ) -> dict[int, dict[int, dict[str, float]]]:
        """Return ``{project_id: {sub_id: {date_str: seconds}}}`` for one month."""
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        return self.get_date_range_sub_activity_data(
            start,
            end,
            project_ids=project_ids,
        )
