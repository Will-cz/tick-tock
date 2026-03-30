"""Unit tests for Storage schema migration/version behavior."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from src.storage import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


class TestSchemaVersioning:
    def test_schema_migrations_table_exists(self, storage):
        with closing(sqlite3.connect(storage._db_path)) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert "schema_migrations" in tables

    def test_all_migrations_applied_on_fresh_db(self, storage):
        with closing(sqlite3.connect(storage._db_path)) as conn:
            applied = {
                row[0]
                for row in conn.execute(
                    "SELECT version FROM schema_migrations"
                ).fetchall()
            }
        assert applied == {1}

    def test_migrations_table_has_applied_at(self, storage):
        with closing(sqlite3.connect(storage._db_path)) as conn:
            row = conn.execute(
                "SELECT applied_at FROM schema_migrations WHERE version = 1"
            ).fetchone()
        assert row is not None
        assert row[0]

    def test_schema_version_constant(self):
        assert Storage._SCHEMA_VERSION == 1

    def test_migrations_are_idempotent(self, tmp_path):
        db_path = tmp_path / "idempotent.db"
        Storage(db_path)
        Storage(db_path)
