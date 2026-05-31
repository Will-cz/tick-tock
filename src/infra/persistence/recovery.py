"""Backup/recovery helpers for SQLite storage."""

from __future__ import annotations

import logging
import shutil
import sqlite3
from enum import Enum
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")
_module_logger = logging.getLogger(__name__)


class RecoveryStatus(str, Enum):
    """Detailed outcome for storage open/recovery attempts."""

    PRIMARY_OK = "primary_ok"
    RECOVERED_FROM_BACKUP = "recovered_from_backup"
    FRESH_DB_CREATED = "fresh_db_created"


def atomic_copy2(src: Path, dst: Path) -> None:
    """Atomically copy *src* to *dst* using copy-to-temp then replace."""
    tmp = dst.with_name(dst.name + ".tmp")
    try:
        shutil.copy2(src, tmp)
        tmp.replace(dst)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError as exc:
                _module_logger.warning(
                    "Could not remove temporary backup file %s: %s",
                    tmp,
                    exc,
                )


def remove_db_files(db_path: Path) -> None:
    """Delete *db_path* and its WAL/SHM sidecar files if they exist."""
    for path in (db_path, Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")):
        if path.exists():
            try:
                path.unlink()
            except OSError as exc:
                _module_logger.warning(
                    "Could not remove database sidecar %s: %s", path, exc
                )


def check_integrity(db_path: Path, sqlite_timeout: float) -> bool:
    """Return True if *db_path* passes SQLite integrity_check."""
    conn = None
    try:
        conn = sqlite3.connect(str(db_path), timeout=sqlite_timeout)
        conn.execute("PRAGMA busy_timeout=10000")
        result = conn.execute("PRAGMA integrity_check").fetchone()
        return result is not None and result[0] == "ok"
    except sqlite3.DatabaseError:
        return False
    finally:
        if conn is not None:
            conn.close()


def open_or_recover_with_status(
    *,
    db_path: Path,
    storage_factory: Callable[[Path], T],
    sqlite_timeout: float,
    logger: logging.Logger,
) -> tuple[T, RecoveryStatus]:
    """Open database at *db_path* with backup recovery fallback."""
    backup_path = Path(str(db_path) + ".bak")

    if db_path.exists() and check_integrity(db_path, sqlite_timeout):
        return storage_factory(db_path), RecoveryStatus.PRIMARY_OK

    if db_path.exists():
        logger.warning("Primary database failed integrity check; attempting recovery.")

    if backup_path.exists():
        try:
            remove_db_files(db_path)
            atomic_copy2(backup_path, db_path)
            if check_integrity(db_path, sqlite_timeout):
                logger.info("Database recovered from backup: %s", backup_path)
                return storage_factory(db_path), RecoveryStatus.RECOVERED_FROM_BACKUP
        except OSError as exc:
            logger.error("Backup recovery also failed: %s", exc)

    remove_db_files(db_path)
    logger.warning("Starting with a fresh database (all previous data lost).")
    return storage_factory(db_path), RecoveryStatus.FRESH_DB_CREATED
