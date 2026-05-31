"""SQLite-based persistence for timer state and activity log."""

import logging
import math
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import ContextManager, Optional

from src.infra.persistence.activity_log_mixin import ActivityLogMixin
from src.infra.persistence.import_export_mixin import ImportExportMixin
from src.infra.persistence.migrations import (
    apply_migrations as apply_schema_migrations,
)
from src.infra.persistence.project_mixin import ProjectMixin
from src.infra.persistence.recovery import (
    RecoveryStatus,
    atomic_copy2,
    open_or_recover_with_status,
)
from src.infra.persistence.sub_activity_mixin import SubActivityMixin
from src.infra.persistence.time_log_mixin import TimeLogMixin
from src.infra.persistence.timer_state_mixin import TimerStateMixin
from src.paths import repo_data_dir, user_data_dir

logger = logging.getLogger(__name__)


class Storage(
    TimerStateMixin,
    ActivityLogMixin,
    ProjectMixin,
    SubActivityMixin,
    TimeLogMixin,
    ImportExportMixin,
):
    """Persists timer state and activity log to a SQLite database.

    Two tables:

    - ``timer_state``: single row with current elapsed seconds and state.
    - ``activity_log``: append-only log of timer events with timestamps.

    Usage::

        storage = Storage(Path("tick_tock.db"))
        storage.save_timer_state(elapsed=42.7, state="stopped")
        state = storage.load_timer_state()  # {"elapsed_seconds": 42.7, ...}
        storage.log_activity("start")
    """

    # Current schema version.  Increment this and add a migration entry in
    # ``_MIGRATIONS`` whenever the database structure changes.
    _SCHEMA_VERSION = 1

    # Default number of timestamped backup files to keep.
    _DEFAULT_BACKUP_KEEP = 5
    # SQLite connection timeout (seconds) for lock contention.
    _SQLITE_TIMEOUT = 10.0

    def __init__(self, db_path: Path) -> None:
        TimerStateMixin.__init__(self)
        ActivityLogMixin.__init__(self)
        ProjectMixin.__init__(self)
        SubActivityMixin.__init__(self)
        TimeLogMixin.__init__(self)
        ImportExportMixin.__init__(self)
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @staticmethod
    def _current_env_mode() -> str:
        """Return the normalized runtime environment name."""
        env = os.environ.get("TICK_TOCK_ENV", "prod").lower()
        if env in {"dev", "test", "prototype", "prod"}:
            return env
        return "prod"

    @staticmethod
    def default_db_path() -> Path:
        """Default database path, isolated by runtime mode.

        Filenames and locations:
        - prod:      ``tick_tock.db``           under ``user_data_dir()``
        - prototype: ``tick_tock.prototype.db`` under ``user_data_dir()``
        - dev/test:  ``tick_tock.<env>.db``     under ``repo_data_dir()``
        """
        env = Storage._current_env_mode()
        if env in {"dev", "test"}:
            return repo_data_dir() / f"tick_tock.{env}.db"
        name = "tick_tock.db" if env == "prod" else f"tick_tock.{env}.db"
        return user_data_dir() / name

    # ------------------------------------------------------------------
    # Data safety
    # ------------------------------------------------------------------

    def backup(self, keep: int = _DEFAULT_BACKUP_KEEP) -> Optional[Path]:
        """Back up the current database.

        Creates or overwrites ``<db_path>.bak`` for crash recovery, and also
        writes a timestamped copy (``<db_path>.backup.YYYYMMDD-HHMMSS``) for
        rotation-based management.  Old timestamped backups beyond *keep* are
        pruned automatically.

        Performs a WAL checkpoint first so all committed data is in the main
        database file before copying.  Returns the ``.bak`` path, or ``None``
        if the DB file does not exist yet.
        """
        if not self._db_path.exists():
            return None
        # Flush WAL into the main db file so the copy is self-contained.
        conn = None
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=self._SQLITE_TIMEOUT)
            conn.execute("PRAGMA busy_timeout=10000")
            conn.execute("PRAGMA wal_checkpoint(FULL)")
        except sqlite3.DatabaseError as exc:
            logger.warning("WAL checkpoint failed before backup: %s", exc)
        finally:
            if conn is not None:
                conn.close()
        # Recovery backup — always keep this at the standard .bak path so that
        # open_or_recover() can find it.
        bak_path = Path(str(self._db_path) + ".bak")
        atomic_copy2(self._db_path, bak_path)
        logger.debug("Database backed up to %s", bak_path)
        # Timestamped backup for rotation management.
        ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        ts_path = Path(str(self._db_path) + f".backup.{ts}")
        atomic_copy2(self._db_path, ts_path)
        logger.debug("Timestamped backup written to %s", ts_path)
        self._prune_backups(keep)
        return bak_path

    def list_backups(self) -> list[Path]:
        """Return all timestamped backup files, sorted newest-first."""
        pattern = self._db_path.name + ".backup.*"
        backups = sorted(self._db_path.parent.glob(pattern))
        return list(reversed(backups))

    def _prune_backups(self, keep: int) -> None:
        """Delete old timestamped backups, keeping only the *keep* most recent."""
        backups = self.list_backups()  # newest first
        for old in backups[keep:]:
            try:
                old.unlink()
                logger.debug("Pruned old backup: %s", old)
            except OSError as exc:
                logger.warning("Could not prune old backup %s: %s", old, exc)

    @classmethod
    def open_or_recover_with_status(
        cls, db_path: Path
    ) -> tuple["Storage", RecoveryStatus]:
        """Open the database at *db_path* with detailed recovery status."""
        return open_or_recover_with_status(
            db_path=db_path,
            storage_factory=cls,
            sqlite_timeout=cls._SQLITE_TIMEOUT,
            logger=logger,
        )

    # ------------------------------------------------------------------
    # Timer state
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_elapsed_for_write(value: object, field_name: str) -> float:
        """Return a safe non-negative finite float for DB writes."""
        try:
            if isinstance(value, bool):
                raise ValueError("bool is not a valid elapsed value")
            if isinstance(value, (int, float, str)):
                elapsed = float(value)
            else:
                raise TypeError("unsupported elapsed value type")
        except (TypeError, ValueError):
            logger.warning("Invalid %s %r, writing 0.0", field_name, value)
            return 0.0
        if math.isnan(elapsed) or math.isinf(elapsed) or elapsed < 0:
            logger.warning("Invalid %s %r, writing 0.0", field_name, value)
            return 0.0
        return elapsed

    @staticmethod
    def sanitize_elapsed_for_write(value: object, field_name: str) -> float:
        """Public wrapper used by persistence mixins and type protocols."""
        return Storage._sanitize_elapsed_for_write(value, field_name)

    @staticmethod
    def _require_int(value: object, field_name: str) -> int:
        """Validate integer-like import fields (ids, schema versions)."""
        try:
            if isinstance(value, bool):
                raise ValueError("bool is not a valid integer value")
            if isinstance(value, int):
                return value
            if isinstance(value, (float, str)):
                return int(value)
            raise TypeError("unsupported integer value type")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid {field_name}: {value!r}") from exc

    @staticmethod
    def require_int(value: object, field_name: str) -> int:
        """Public wrapper used by persistence mixins and type protocols."""
        return Storage._require_int(value, field_name)

    @staticmethod
    def _sanitize_timer_state_for_write(state: object) -> str:
        """Return a validated timer state string for DB writes."""
        state_text = str(state).lower()
        valid = {"idle", "running", "paused", "stopped"}
        if state_text not in valid:
            logger.warning("Invalid timer state %r, writing 'stopped'", state)
            return "stopped"
        return state_text

    @staticmethod
    def sanitize_timer_state_for_write(state: object) -> str:
        """Public wrapper used by persistence mixins and type protocols."""
        return Storage._sanitize_timer_state_for_write(state)

    # ------------------------------------------------------------------
    # App state (key/value)
    # ------------------------------------------------------------------

    def get_app_state(self, key: str) -> Optional[str]:
        """Return app-state value for *key*, or None when absent."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM app_state WHERE key = ?", (key,)
            ).fetchone()
        return row[0] if row else None

    def set_app_state(self, key: str, value: str) -> None:
        """Persist app-state key/value pair."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
                (key, value),
            )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @contextmanager
    def _connect(self):
        """Yield a sqlite connection that always commits/rolls back and closes."""
        conn = sqlite3.connect(self._db_path, timeout=self._SQLITE_TIMEOUT)
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=10000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def connect(self) -> ContextManager[sqlite3.Connection]:
        """Public wrapper used by persistence mixins and type protocols."""
        return self._connect()

    def _init_db(self) -> None:
        with self._connect() as conn:
            # WAL mode provides crash-safety: writes never partially corrupt the DB.
            conn.execute("PRAGMA journal_mode=WAL")
            # Bootstrap the schema_migrations table before running any migrations.
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
        self._apply_migrations()

    # -----------------------------------------------------------------
    # Schema migrations
    # -----------------------------------------------------------------

    # Each tuple: (version: int, description: str, callable(conn) -> None)
    # Migrations MUST be idempotent — they may be run against a DB that already
    # has the changes (e.g. after a failed mid-migration crash).

    def _apply_migrations(self) -> None:
        """Run any schema migrations that have not yet been applied."""
        apply_schema_migrations(
            connect=self._connect,
            schema_version=self._SCHEMA_VERSION,
            logger=logger,
        )
