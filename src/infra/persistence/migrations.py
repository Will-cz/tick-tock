"""Schema migration helpers for the SQLite storage backend."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from typing import Callable, ContextManager


def migration_v1(conn: sqlite3.Connection) -> None:
    """Baseline schema (replaces former v1-v6 chain).

    Seconds columns are declared INTEGER so persisted values are exact
    whole-second counts.  SQLite uses dynamic typing, but the declared
    type documents intent and supports future tooling.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS timer_state (
            id INTEGER PRIMARY KEY,
            elapsed_seconds INTEGER NOT NULL,
            state TEXT NOT NULL,
            saved_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            elapsed_seconds INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            ref_number TEXT NOT NULL DEFAULT '',
            alias TEXT NOT NULL DEFAULT '',
            color TEXT NOT NULL DEFAULT '',
            archived INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_time_log (
            date TEXT NOT NULL,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            seconds INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (date, project_id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_daily_time_project_date"
        " ON daily_time_log (project_id, date)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sub_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            elapsed_seconds INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            archived INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sub_activities_project_id"
        " ON sub_activities (project_id)"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_sub_activities_id_project"
        " ON sub_activities (id, project_id)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_sub_time_log (
            date TEXT NOT NULL,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            sub_activity_id INTEGER NOT NULL,
            seconds INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (date, sub_activity_id),
            FOREIGN KEY (sub_activity_id, project_id)
                REFERENCES sub_activities(id, project_id)
                ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_daily_sub_project_date"
        " ON daily_sub_time_log (project_id, date)"
    )


def migration_v2(conn: sqlite3.Connection) -> None:
    """Drop the event-stream activity_log table and add daily_time_log index.

    Existing per-day totals already capture every metric the app reports,
    so the per-event audit log was pure overhead.  Idempotent so it is
    safe to re-run against a partially-migrated database.
    """
    conn.execute("DROP TABLE IF EXISTS activity_log")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_daily_time_project_date"
        " ON daily_time_log (project_id, date)"
    )


def apply_migrations(
    *,
    connect: Callable[[], ContextManager[sqlite3.Connection]],
    schema_version: int,
    logger: logging.Logger,
) -> None:
    """Run any schema migrations that have not yet been applied."""
    migrations = [
        (1, "initial schema", migration_v1),
        (2, "drop activity_log event stream", migration_v2),
    ]

    with connect() as conn:
        applied = {
            row[0]
            for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
        }

    max_applied = max(applied, default=0)

    if max_applied > schema_version:
        logger.warning(
            "Database schema v%d is newer than this app expects (v%d). "
            "Consider upgrading the app to avoid potential data issues.",
            max_applied,
            schema_version,
        )

    for version, description, migrate_fn in migrations:
        if version in applied:
            continue
        logger.debug("Applying schema migration v%d: %s", version, description)
        with connect() as conn:
            migrate_fn(conn)
            conn.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at)"
                " VALUES (?, ?)",
                (version, datetime.now().isoformat()),
            )
        logger.info("Schema migration v%d applied: %s", version, description)
