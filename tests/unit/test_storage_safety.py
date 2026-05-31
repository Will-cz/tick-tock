"""Unit tests for v0.4.0 data-safety features in Storage."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from src.storage import RecoveryStatus, Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


# ---------------------------------------------------------------------------
# WAL mode
# ---------------------------------------------------------------------------


class TestWalMode:
    def test_wal_mode_enabled(self, storage):
        with closing(sqlite3.connect(storage._db_path)) as conn:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------


class TestBackup:
    def test_backup_creates_bak_file(self, storage):
        backup_path = storage.backup()
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.name.endswith(".bak")

    def test_backup_returns_none_when_db_missing(self, tmp_path):
        db_path = tmp_path / "new.db"
        # Build a Storage without actually touching the file system through Storage()
        s = Storage.__new__(Storage)
        s._db_path = db_path
        assert s.backup() is None

    def test_backup_content_matches_original(self, storage):
        storage.save_timer_state(42.0, "stopped")
        backup_path = storage.backup()
        assert backup_path is not None
        # Read the backed-up DB directly and verify the value
        with closing(sqlite3.connect(backup_path)) as conn:
            row = conn.execute(
                "SELECT elapsed_seconds FROM timer_state WHERE id = 1"
            ).fetchone()
        assert row is not None
        assert row[0] == pytest.approx(42.0)

    def test_backup_overwrites_previous_backup(self, storage):
        storage.save_timer_state(10.0, "stopped")
        storage.backup()
        storage.save_timer_state(99.0, "stopped")
        backup_path = storage.backup()
        assert backup_path is not None
        with closing(sqlite3.connect(backup_path)) as conn:
            row = conn.execute(
                "SELECT elapsed_seconds FROM timer_state WHERE id = 1"
            ).fetchone()
        assert row[0] == pytest.approx(99.0)


# ---------------------------------------------------------------------------
# Integrity check
# ---------------------------------------------------------------------------


class TestVerifyIntegrity:
    def test_healthy_db_reports_primary_ok(self, storage):
        _instance, status = Storage.open_or_recover_with_status(storage._db_path)
        assert status == RecoveryStatus.PRIMARY_OK

    def test_corrupt_db_is_not_primary_ok(self, tmp_path):
        db_path = tmp_path / "corrupt.db"
        # Write enough non-SQLite bytes that SQLite cannot treat the file as empty.
        db_path.write_bytes(b"\xff" * 4096)
        _instance, status = Storage.open_or_recover_with_status(db_path)
        assert status != RecoveryStatus.PRIMARY_OK


# ---------------------------------------------------------------------------
# open_or_recover
# ---------------------------------------------------------------------------


class TestOpenOrRecover:
    def test_healthy_db_reports_primary_ok(self, tmp_path):
        db_path = tmp_path / "good.db"
        # Create a healthy DB first
        Storage(db_path)
        instance, status = Storage.open_or_recover_with_status(db_path)
        assert isinstance(instance, Storage)
        assert status == RecoveryStatus.PRIMARY_OK

    def test_missing_db_creates_fresh_with_status(self, tmp_path):
        db_path = tmp_path / "nonexistent.db"
        instance, status = Storage.open_or_recover_with_status(db_path)
        assert isinstance(instance, Storage)
        assert status == RecoveryStatus.FRESH_DB_CREATED

    def test_corrupt_primary_recovers_from_backup(self, tmp_path):
        db_path = tmp_path / "main.db"

        # Create a good backup with known data
        good = Storage(db_path)
        good.save_timer_state(77.0, "stopped")
        good.backup()  # writes .bak

        # Corrupt the primary (large enough that SQLite won't silently reinitialise it)
        db_path.write_bytes(b"\xff" * 4096)

        instance, status = Storage.open_or_recover_with_status(db_path)
        assert status == RecoveryStatus.RECOVERED_FROM_BACKUP
        state = instance.load_timer_state()
        assert state is not None
        assert state["elapsed_seconds"] == pytest.approx(77.0)

    def test_corrupt_primary_and_backup_starts_fresh(self, tmp_path):
        db_path = tmp_path / "main.db"
        backup_path = Path(str(db_path) + ".bak")

        db_path.write_bytes(b"\xff" * 4096)
        backup_path.write_bytes(b"\xff" * 4096)

        instance, status = Storage.open_or_recover_with_status(db_path)
        assert status == RecoveryStatus.FRESH_DB_CREATED
        assert instance.load_timer_state() is None  # fresh DB
        instance.save_timer_state(1.0, "stopped")
        state = instance.load_timer_state()
        assert state is not None
        assert state["elapsed_seconds"] == pytest.approx(1.0)

    def test_corrupt_primary_no_backup_starts_fresh(self, tmp_path):
        db_path = tmp_path / "main.db"
        db_path.write_bytes(b"\xff" * 4096)

        instance, status = Storage.open_or_recover_with_status(db_path)
        assert status == RecoveryStatus.FRESH_DB_CREATED
        assert instance.load_timer_state() is None
        instance.save_timer_state(1.0, "stopped")
        state = instance.load_timer_state()
        assert state is not None
        assert state["elapsed_seconds"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Timer state validation
# ---------------------------------------------------------------------------


class TestTimerStateValidation:
    def test_negative_elapsed_is_corrected(self, storage):
        # Directly insert invalid data bypassing the save method
        with closing(sqlite3.connect(storage._db_path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO timer_state"
                " (id, elapsed_seconds, state, saved_at)"
                " VALUES (1, -5.0, 'stopped', '2000-01-01')"
            )
            conn.commit()
        state = storage.load_timer_state()
        assert state is not None
        assert state["elapsed_seconds"] == pytest.approx(0.0)

    def test_invalid_state_is_corrected(self, storage):
        with closing(sqlite3.connect(storage._db_path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO timer_state"
                " (id, elapsed_seconds, state, saved_at)"
                " VALUES (1, 10.0, 'invalid_state', '2000-01-01')"
            )
            conn.commit()
        state = storage.load_timer_state()
        assert state is not None
        assert state["state"] == "stopped"

    def test_valid_data_is_unchanged(self, storage):
        storage.save_timer_state(123.4, "paused")
        state = storage.load_timer_state()
        # Seconds are persisted as INTEGER; fractional input is truncated.
        assert state["elapsed_seconds"] == 123
        assert state["state"] == "paused"


# ---------------------------------------------------------------------------
# Project data validation
# ---------------------------------------------------------------------------


class TestProjectDataValidation:
    def test_negative_elapsed_is_corrected(self, storage):
        pid = storage.create_project("Test", "")
        with closing(sqlite3.connect(storage._db_path)) as conn:
            conn.execute(
                "UPDATE projects SET elapsed_seconds = -99.0 WHERE id = ?", (pid,)
            )
        rows = storage.list_projects()
        assert rows[0]["elapsed_seconds"] == pytest.approx(0.0)

    def test_valid_project_data_is_unchanged(self, storage):
        pid = storage.create_project("Work", "desc")
        storage.save_project_elapsed(pid, 500.0)
        rows = storage.list_projects()
        assert rows[0]["elapsed_seconds"] == pytest.approx(500.0)
        assert rows[0]["name"] == "Work"


class TestRecoveryStatusDetail:
    def test_detailed_status_reports_primary_ok(self, tmp_path):
        db_path = tmp_path / "good_detail.db"
        Storage(db_path)
        _instance, status = Storage.open_or_recover_with_status(db_path)
        assert status == RecoveryStatus.PRIMARY_OK

    def test_detailed_status_reports_recovered_from_backup(self, tmp_path):
        db_path = tmp_path / "recover_detail.db"
        storage = Storage(db_path)
        storage.save_timer_state(33.0, "stopped")
        storage.backup()
        db_path.write_bytes(b"\xff" * 4096)

        _instance, status = Storage.open_or_recover_with_status(db_path)
        assert status == RecoveryStatus.RECOVERED_FROM_BACKUP

    def test_detailed_status_reports_fresh_db_created(self, tmp_path):
        db_path = tmp_path / "fresh_detail.db"
        db_path.write_bytes(b"\xff" * 4096)
        backup_path = Path(str(db_path) + ".bak")
        backup_path.write_bytes(b"\xff" * 4096)

        _instance, status = Storage.open_or_recover_with_status(db_path)
        assert status == RecoveryStatus.FRESH_DB_CREATED


class TestWriteSideValidation:
    def test_save_timer_state_invalid_elapsed_is_clamped(self, storage):
        storage.save_timer_state(float("nan"), "running")
        state = storage.load_timer_state()
        assert state is not None
        assert state["elapsed_seconds"] == pytest.approx(0.0)

    def test_save_timer_state_invalid_state_is_sanitized(self, storage):
        storage.save_timer_state(10.0, "unexpected")
        state = storage.load_timer_state()
        assert state is not None
        assert state["state"] == "stopped"

    def test_save_project_elapsed_negative_is_clamped(self, storage):
        pid = storage.create_project("Clamp", "")
        storage.save_project_elapsed(pid, -5.0)
        project = next(p for p in storage.list_projects() if p["id"] == pid)
        assert project["elapsed_seconds"] == pytest.approx(0.0)

    def test_save_sub_elapsed_negative_is_clamped(self, storage):
        pid = storage.create_project("ClampSub", "")
        sid = storage.create_sub_activity(pid, "Sub")
        storage.save_sub_activity_elapsed(sid, -9.0)
        sub = next(s for s in storage.list_sub_activities(pid) if s["id"] == sid)
        assert sub["elapsed_seconds"] == pytest.approx(0.0)
