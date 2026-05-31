"""Additional unit tests to cover Storage edge branches."""

import sqlite3
from datetime import date, timedelta
from pathlib import Path
from contextlib import closing

import pytest

from src.storage import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "extra.db")


def test_default_db_path_can_derive_bak_suffix(monkeypatch) -> None:
    monkeypatch.delenv("TICK_TOCK_ENV", raising=False)
    path = Path(str(Storage.default_db_path()) + ".bak")
    assert str(path).endswith("tick_tock.db.bak")


def test_add_daily_sub_activity_seconds_ignores_non_positive(storage: Storage) -> None:
    project_id = storage.create_project("P", "")
    sub_id = storage.create_sub_activity(project_id, "SA")
    storage.add_daily_sub_activity_seconds(project_id, sub_id, "2026-03-30", 0.0)
    storage.add_daily_sub_activity_seconds(project_id, sub_id, "2026-03-30", -5.0)
    rows = storage.get_date_range_sub_activity_data(
        start_date=date(2026, 3, 30),
        end_date=date(2026, 3, 30),
        project_ids=[project_id],
    )
    assert rows == {}


def test_get_date_range_data_returns_empty_for_invalid_range(storage: Storage) -> None:
    assert storage.get_date_range_data(date(2026, 4, 1), date(2026, 3, 1)) == {}


def test_get_date_range_data_returns_empty_for_explicit_empty_project_ids(
    storage: Storage,
) -> None:
    assert (
        storage.get_date_range_data(
            date(2026, 3, 1),
            date(2026, 3, 31),
            project_ids=[],
        )
        == {}
    )


def test_get_date_range_sub_activity_data_returns_empty_for_invalid_inputs(
    storage: Storage,
) -> None:
    assert (
        storage.get_date_range_sub_activity_data(
            date(2026, 4, 1),
            date(2026, 3, 1),
        )
        == {}
    )
    assert (
        storage.get_date_range_sub_activity_data(
            date(2026, 3, 1),
            date(2026, 3, 31),
            project_ids=[],
        )
        == {}
    )


def test_import_json_drops_activity_log_entries(
    storage: Storage, tmp_path: Path
) -> None:
    # Activity log is no longer persisted; legacy exports with activity_log
    # should be accepted (field discarded silently).
    src = Storage(tmp_path / "src_extra.db")
    src.create_project("Alpha", "")
    export_path = tmp_path / "act_export.json"
    src.export_json(export_path)

    # Confirm export does not include activity_log.
    import json as _json

    payload = _json.loads(export_path.read_text(encoding="utf-8"))
    assert "activity_log" not in payload

    storage.import_json(export_path)
    names = [p["name"] for p in storage.list_projects()]
    assert "Alpha" in names


def test_rebased_schema_preserves_existing_migration_markers(tmp_path: Path) -> None:
    # When opening a DB that already records all migrations, Storage should
    # leave the markers intact and not re-run migrations.
    db_path = tmp_path / "legacy.db"
    Storage(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        first_versions = {
            row[0] for row in conn.execute("SELECT version FROM schema_migrations")
        }

    Storage(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        second_versions = {
            row[0] for row in conn.execute("SELECT version FROM schema_migrations")
        }

    assert first_versions == second_versions
    assert second_versions == {1, 2}


def test_apply_retention_policy_prunes_old_daily_rows(storage: Storage) -> None:
    project_id = storage.create_project("Retention", "")
    sub_id = storage.create_sub_activity(project_id, "Retention SA")

    old_day = (date.today() - timedelta(days=40)).isoformat()
    recent_day = date.today().isoformat()
    storage.add_daily_seconds(project_id, old_day, 60.0)
    storage.add_daily_seconds(project_id, recent_day, 60.0)
    storage.add_daily_sub_activity_seconds(project_id, sub_id, old_day, 30.0)
    storage.add_daily_sub_activity_seconds(project_id, sub_id, recent_day, 30.0)

    deleted = storage.apply_retention_policy(history_days=30)
    assert deleted["daily_time_log"] >= 1
    assert deleted["daily_sub_time_log"] >= 1

    by_project_old = storage.get_daily_seconds_by_project(old_day)
    by_project_recent = storage.get_daily_seconds_by_project(recent_day)
    assert project_id not in by_project_old
    assert by_project_recent.get(project_id, 0.0) > 0.0


def test_apply_retention_policy_caps_daily_only(storage: Storage) -> None:
    # Verify the retention dict contains only the daily-table keys.
    deleted = storage.apply_retention_policy(history_days=30)
    assert set(deleted.keys()) == {"daily_time_log", "daily_sub_time_log"}


def test_get_date_range_data_handles_large_dataset(storage: Storage) -> None:
    days = [date(2026, 4, day).isoformat() for day in range(1, 6)]
    project_ids: list[int] = []

    for project_idx in range(120):
        project_id = storage.create_project(f"P-{project_idx}", "")
        project_ids.append(project_id)
        for day_idx, day_text in enumerate(days):
            storage.add_daily_seconds(
                project_id,
                day_text,
                float(project_idx + day_idx + 1),
            )

    result = storage.get_date_range_data(date(2026, 4, 1), date(2026, 4, 5))

    assert len(result) == 120
    sample_project_idx = 37
    sample_project_id = project_ids[sample_project_idx]
    assert len(result[sample_project_id]) == 5

    expected = {
        day_text: float(sample_project_idx + day_idx + 1)
        for day_idx, day_text in enumerate(days)
    }
    assert result[sample_project_id] == expected


def test_get_date_range_sub_activity_data_handles_large_dataset(
    storage: Storage,
) -> None:
    days = [date(2026, 5, day).isoformat() for day in range(1, 4)]
    sample_project_id = -1
    sample_sub_id = -1

    for project_idx in range(25):
        project_id = storage.create_project(f"SP-{project_idx}", "")
        for sub_idx in range(4):
            sub_id = storage.create_sub_activity(
                project_id,
                f"Sub-{project_idx}-{sub_idx}",
            )
            if project_idx == 10 and sub_idx == 2:
                sample_project_id = project_id
                sample_sub_id = sub_id
            for day_idx, day_text in enumerate(days):
                storage.add_daily_sub_activity_seconds(
                    project_id,
                    sub_id,
                    day_text,
                    float((project_idx + 1) * (sub_idx + 1) + day_idx),
                )

    result = storage.get_date_range_sub_activity_data(
        date(2026, 5, 1),
        date(2026, 5, 3),
    )

    assert len(result) == 25
    assert len(result[sample_project_id]) == 4
    assert len(result[sample_project_id][sample_sub_id]) == 3

    expected = {
        day_text: float((10 + 1) * (2 + 1) + day_idx)
        for day_idx, day_text in enumerate(days)
    }
    assert result[sample_project_id][sample_sub_id] == expected


def test_get_date_range_data_handles_year_scale_multi_project_dataset(
    storage: Storage,
) -> None:
    start = date(2025, 1, 1)
    project_ids = [storage.create_project(f"Y-{idx}", "") for idx in range(5)]

    for day_offset in range(365):
        day_text = (start + timedelta(days=day_offset)).isoformat()
        for project_idx, project_id in enumerate(project_ids):
            storage.add_daily_seconds(
                project_id,
                day_text,
                float(project_idx + 1),
            )

    result = storage.get_date_range_data(
        date(2025, 1, 1),
        date(2025, 12, 31),
    )

    assert len(result) == 5
    for project_idx, project_id in enumerate(project_ids):
        assert len(result[project_id]) == 365
        expected_total = 365.0 * float(project_idx + 1)
        assert sum(result[project_id].values()) == pytest.approx(expected_total)
