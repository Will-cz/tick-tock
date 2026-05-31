"""Unit tests for Storage."""

from pathlib import Path

import pytest

from src.storage import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


@pytest.fixture
def project_ids(storage: Storage) -> tuple[int, int]:
    p1 = storage.create_project("P1", "")
    p2 = storage.create_project("P2", "")
    return p1, p2


class TestStorageInit:
    def test_creates_db_file(self, tmp_path):
        db_path = tmp_path / "sub" / "tick.db"
        Storage(db_path)
        assert db_path.exists()

    def test_default_db_path_is_path(self):
        assert isinstance(Storage.default_db_path(), Path)


class TestTimerState:
    def test_load_returns_none_when_empty(self, storage):
        assert storage.load_timer_state() is None

    def test_save_and_load_elapsed(self, storage):
        storage.save_timer_state(elapsed=123.5, state="stopped")
        result = storage.load_timer_state()
        assert result is not None
        # Seconds are persisted as INTEGER; fractional input is truncated.
        assert result["elapsed_seconds"] == 123

    def test_save_and_load_state(self, storage):
        storage.save_timer_state(elapsed=0.0, state="paused")
        assert storage.load_timer_state()["state"] == "paused"

    def test_save_overwrites_previous(self, storage):
        storage.save_timer_state(elapsed=10.0, state="running")
        storage.save_timer_state(elapsed=99.0, state="stopped")
        result = storage.load_timer_state()
        assert result["elapsed_seconds"] == pytest.approx(99.0)
        assert result["state"] == "stopped"

    def test_saved_at_is_populated(self, storage):
        storage.save_timer_state(elapsed=1.0, state="stopped")
        assert storage.load_timer_state()["saved_at"] != ""

    def test_clear_removes_state(self, storage):
        storage.save_timer_state(elapsed=5.0, state="stopped")
        storage.clear_timer_state()
        assert storage.load_timer_state() is None

    def test_clear_when_empty_is_safe(self, storage):
        storage.clear_timer_state()  # should not raise


class TestDailyTimeLog:
    def test_add_and_get_total(self, storage, project_ids):
        p1, _ = project_ids
        storage.add_daily_seconds(p1, "2026-03-09", 300.0)
        assert storage.get_daily_total("2026-03-09") == pytest.approx(300.0)

    def test_add_accumulates_multiple_calls(self, storage, project_ids):
        p1, _ = project_ids
        storage.add_daily_seconds(p1, "2026-03-09", 100.0)
        storage.add_daily_seconds(p1, "2026-03-09", 200.0)
        assert storage.get_daily_total("2026-03-09") == pytest.approx(300.0)

    def test_add_accumulates_across_projects(self, storage, project_ids):
        p1, p2 = project_ids
        storage.add_daily_seconds(p1, "2026-03-09", 100.0)
        storage.add_daily_seconds(p2, "2026-03-09", 50.0)
        assert storage.get_daily_total("2026-03-09") == pytest.approx(150.0)

    def test_total_is_zero_for_empty_date(self, storage):
        assert storage.get_daily_total("2026-01-01") == pytest.approx(0.0)

    def test_ignores_zero_and_negative_seconds(self, storage, project_ids):
        p1, _ = project_ids
        storage.add_daily_seconds(p1, "2026-03-09", 0.0)
        storage.add_daily_seconds(p1, "2026-03-09", -10.0)
        assert storage.get_daily_total("2026-03-09") == pytest.approx(0.0)

    def test_totals_are_date_isolated(self, storage, project_ids):
        p1, _ = project_ids
        storage.add_daily_seconds(p1, "2026-03-08", 500.0)
        storage.add_daily_seconds(p1, "2026-03-09", 100.0)
        assert storage.get_daily_total("2026-03-09") == pytest.approx(100.0)

    def test_get_by_project(self, storage, project_ids):
        p1, p2 = project_ids
        storage.add_daily_seconds(p1, "2026-03-09", 60.0)
        storage.add_daily_seconds(p2, "2026-03-09", 120.0)
        by_proj = storage.get_daily_seconds_by_project("2026-03-09")
        assert by_proj[p1] == pytest.approx(60.0)
        assert by_proj[p2] == pytest.approx(120.0)

    def test_get_daily_total_can_be_scoped_to_project(self, storage, project_ids):
        p1, p2 = project_ids
        storage.add_daily_seconds(p1, "2026-03-09", 60.0)
        storage.add_daily_seconds(p2, "2026-03-09", 120.0)
        assert storage.get_daily_total("2026-03-09", project_id=p1) == pytest.approx(
            60.0
        )
        assert storage.get_daily_total("2026-03-09", project_id=p2) == pytest.approx(
            120.0
        )

    def test_get_by_project_empty_date(self, storage):
        assert storage.get_daily_seconds_by_project("2026-01-01") == {}

    def test_different_projects_same_day_accumulate_independently(
        self, storage, project_ids
    ):
        p1, p2 = project_ids
        storage.add_daily_seconds(p1, "2026-03-09", 30.0)
        storage.add_daily_seconds(p1, "2026-03-09", 30.0)
        storage.add_daily_seconds(p2, "2026-03-09", 10.0)
        by_proj = storage.get_daily_seconds_by_project("2026-03-09")
        assert by_proj[p1] == pytest.approx(60.0)
        assert by_proj[p2] == pytest.approx(10.0)


# ------------------------------------------------------------------
# v0.1.0 - Stable data format (schema version guard)
# ------------------------------------------------------------------


class TestSchemaVersionStability:
    def test_existing_schema_is_stable_across_reopen(self, tmp_path):
        """Reopening a valid database does not alter schema_version records."""
        db_path = tmp_path / "test.db"
        s1 = Storage(db_path)
        s1.save_timer_state(elapsed=42.0, state="stopped")
        # Reopen - should not re-apply migrations or lose data.
        s2 = Storage(db_path)
        result = s2.load_timer_state()
        assert result is not None
        assert result["elapsed_seconds"] == pytest.approx(42.0)

    def test_future_schema_version_logged_as_warning(self, tmp_path, caplog):
        """A DB with schema_version higher than the app knows about is detected."""
        import logging
        import sqlite3

        db_path = tmp_path / "future.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at)"
            " VALUES (999, '2099-01-01T00:00:00')"
        )
        conn.commit()
        conn.close()

        with caplog.at_level(logging.WARNING, logger="src.storage"):
            Storage(db_path)  # should log a warning, not raise

        assert any("999" in rec.message for rec in caplog.records)

    def test_normal_schema_version_no_warning(self, tmp_path, caplog):
        """An up-to-date database should not produce any schema warning."""
        import logging

        db_path = tmp_path / "normal.db"
        with caplog.at_level(logging.WARNING, logger="src.storage"):
            Storage(db_path)

        schema_warnings = [r for r in caplog.records if "schema" in r.message.lower()]
        assert not schema_warnings

    def test_migrations_are_idempotent(self, tmp_path):
        """Re-opening an existing database never doubles migration records."""
        import sqlite3

        db_path = tmp_path / "idem.db"
        Storage(db_path)
        Storage(db_path)
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
        conn.close()
        versions = [r[0] for r in rows]
        assert len(versions) == len(set(versions)), "duplicate migration entries found"
