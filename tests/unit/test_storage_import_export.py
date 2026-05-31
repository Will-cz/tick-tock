"""Unit tests for Storage backup/export/import flows."""

import json
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

import pytest

from src.storage import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


class TestBackupManagement:
    def test_backup_creates_bak_file(self, storage):
        bak = storage.backup()
        assert bak is not None
        assert bak.exists()
        assert bak.name.endswith(".bak")

    def test_backup_creates_timestamped_file(self, storage):
        storage.backup()
        backups = storage.list_backups()
        assert len(backups) == 1
        assert ".backup." in backups[0].name

    def test_backup_returns_none_when_db_missing(self, tmp_path):
        s = Storage.__new__(Storage)
        s._db_path = tmp_path / "ghost.db"
        assert s.backup() is None

    def test_backup_content_matches_original(self, storage):
        storage.save_timer_state(42.0, "stopped")
        bak = storage.backup()
        assert bak is not None
        with closing(sqlite3.connect(bak)) as conn:
            row = conn.execute(
                "SELECT elapsed_seconds FROM timer_state WHERE id = 1"
            ).fetchone()
        assert row is not None
        assert row[0] == pytest.approx(42.0)

    def test_backup_prunes_old_timestamped_backups(self, storage):
        for _ in range(7):
            storage.backup(keep=3)
        assert len(storage.list_backups()) == 3

    def test_list_backups_returns_newest_first(self, storage):
        storage.backup()
        storage.backup()
        backups = storage.list_backups()
        assert len(backups) == 2
        assert backups[0].name > backups[1].name

    def test_backup_keep_zero_removes_all_timestamped(self, storage):
        storage.backup()
        storage.backup(keep=0)
        assert storage.list_backups() == []

    def test_bak_file_still_overwritten_on_second_backup(self, storage):
        storage.save_timer_state(10.0, "stopped")
        storage.backup()
        storage.save_timer_state(99.0, "stopped")
        bak = storage.backup()
        assert bak is not None
        with closing(sqlite3.connect(bak)) as conn:
            row = conn.execute(
                "SELECT elapsed_seconds FROM timer_state WHERE id = 1"
            ).fetchone()
        assert row[0] == pytest.approx(99.0)


class TestExportJson:
    def test_export_creates_file(self, storage, tmp_path):
        out = tmp_path / "export.json"
        storage.export_json(out)
        assert out.exists()

    def test_export_contains_required_keys(self, storage, tmp_path):
        out = tmp_path / "export.json"
        storage.export_json(out)
        data = json.loads(out.read_text())
        assert data["export_version"] == 1
        assert "projects" in data
        assert "daily_time_log" in data
        assert "activity_log" in data
        assert "exported_at" in data

    def test_export_includes_project_data(self, storage, tmp_path):
        pid = storage.create_project("Alpha", "first project")
        storage.save_project_elapsed(pid, 300.0)
        out = tmp_path / "export.json"
        storage.export_json(out)
        data = json.loads(out.read_text())
        names = [p["name"] for p in data["projects"]]
        assert "Alpha" in names

    def test_export_includes_daily_log(self, storage, tmp_path):
        pid = storage.create_project("Beta", "")
        storage.add_daily_seconds(pid, "2026-03-09", 900.0)
        out = tmp_path / "export.json"
        storage.export_json(out)
        data = json.loads(out.read_text())
        entry = next(
            (e for e in data["daily_time_log"] if e["project_id"] == pid), None
        )
        assert entry is not None
        assert entry["seconds"] == pytest.approx(900.0)

    def test_export_is_atomic(self, storage, tmp_path):
        out = tmp_path / "export.json"
        storage.export_json(out)
        assert not out.with_suffix(".tmp").exists()


class TestImportJson:
    def _make_export(self, storage, tmp_path) -> Path:
        storage.create_project("Project A", "desc A")
        out = tmp_path / "export.json"
        storage.export_json(out)
        return out

    def test_import_replaces_projects(self, tmp_path):
        src = Storage(tmp_path / "src.db")
        export_path = self._make_export(src, tmp_path)

        dst = Storage(tmp_path / "dst.db")
        dst.create_project("Old Project", "")
        dst.import_json(export_path)

        names = [p["name"] for p in dst.list_projects()]
        assert "Project A" in names
        assert "Old Project" not in names

    def test_import_restores_timer_state(self, tmp_path):
        src = Storage(tmp_path / "src.db")
        src.save_timer_state(123.0, "stopped")
        export_path = tmp_path / "e.json"
        src.export_json(export_path)

        dst = Storage(tmp_path / "dst.db")
        dst.import_json(export_path)
        state = dst.load_timer_state()
        assert state is not None
        assert state["elapsed_seconds"] == pytest.approx(123.0)

    def test_import_restores_daily_log(self, tmp_path):
        src = Storage(tmp_path / "src.db")
        pid = src.create_project("P", "")
        src.add_daily_seconds(pid, "2026-03-09", 450.0)
        export_path = tmp_path / "e.json"
        src.export_json(export_path)

        dst = Storage(tmp_path / "dst.db")
        dst.import_json(export_path)
        total = dst.get_daily_total("2026-03-09")
        assert total == pytest.approx(450.0)

    def test_import_raises_on_invalid_file(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"not_a_valid_export": True}))
        s = Storage(tmp_path / "s.db")
        with pytest.raises(ValueError, match="Invalid export file"):
            s.import_json(bad)

    def test_import_raises_on_wrong_version(self, tmp_path):
        bad = tmp_path / "bad_v.json"
        bad.write_text(json.dumps({"export_version": 99, "projects": []}))
        s = Storage(tmp_path / "s.db")
        with pytest.raises(ValueError, match="Unsupported export version"):
            s.import_json(bad)

    def test_import_rejects_newer_schema_version(self, tmp_path):
        bad = tmp_path / "bad_schema.json"
        bad.write_text(
            json.dumps(
                {
                    "export_version": 1,
                    "schema_version": 999,
                    "projects": [],
                }
            )
        )
        s = Storage(tmp_path / "s.db")
        with pytest.raises(ValueError, match="Unsupported schema_version"):
            s.import_json(bad)

    def test_import_clears_existing_timer_state_when_absent_in_payload(self, tmp_path):
        dst = Storage(tmp_path / "dst_clear_timer.db")
        dst.save_timer_state(88.0, "paused")

        payload = {
            "export_version": 1,
            "schema_version": 1,
            "projects": [],
            "daily_time_log": [],
            "daily_sub_time_log": [],
            "sub_activities": [],
            "activity_log": [],
            # timer_state intentionally omitted
        }
        path = tmp_path / "clear_timer.json"
        path.write_text(json.dumps(payload), encoding="utf-8")

        dst.import_json(path)
        assert dst.load_timer_state() is None

    def test_import_rejects_daily_sub_project_mismatch(self, tmp_path):
        bad = tmp_path / "bad_daily_sub.json"
        bad.write_text(
            json.dumps(
                {
                    "export_version": 1,
                    "schema_version": 1,
                    "projects": [
                        {"id": 1, "name": "P1", "description": "", "elapsed_seconds": 0}
                    ],
                    "sub_activities": [
                        {
                            "id": 10,
                            "project_id": 1,
                            "name": "SA",
                            "description": "",
                            "elapsed_seconds": 0,
                        }
                    ],
                    "daily_time_log": [],
                    "daily_sub_time_log": [
                        {
                            "date": "2026-04-08",
                            "project_id": 999,
                            "sub_activity_id": 10,
                            "seconds": 60,
                        }
                    ],
                    "activity_log": [],
                }
            ),
            encoding="utf-8",
        )
        s = Storage(tmp_path / "s_mismatch.db")
        with pytest.raises(ValueError, match="unknown project_id"):
            s.import_json(bad)

    def test_roundtrip_preserves_project_fields(self, tmp_path):
        src = Storage(tmp_path / "src.db")
        src.create_project(
            "Roundtrip",
            "desc",
            ref_number="REF-1",
            alias="rt",
            color="#FF0000",
            notes="some notes",
        )
        export_path = tmp_path / "rt.json"
        src.export_json(export_path)

        dst = Storage(tmp_path / "dst.db")
        dst.import_json(export_path)
        projects = dst.list_projects()
        p = next(p for p in projects if p["name"] == "Roundtrip")
        assert p["ref_number"] == "REF-1"
        assert p["alias"] == "rt"
        assert p["color"] == "#FF0000"
        assert p["notes"] == "some notes"

    def test_roundtrip_large_dataset_preserves_counts_and_samples(self, tmp_path):
        src = Storage(tmp_path / "src_large.db")
        day_text = "2026-06-01"

        created_project_ids: list[int] = []
        created_sub_ids: list[int] = []
        for idx in range(80):
            project_id = src.create_project(f"Bulk-{idx}", "")
            created_project_ids.append(project_id)
            src.add_daily_seconds(project_id, day_text, float(idx + 1))
            for sub_idx in range(2):
                sub_id = src.create_sub_activity(project_id, f"BSub-{idx}-{sub_idx}")
                created_sub_ids.append(sub_id)
                src.add_daily_sub_activity_seconds(
                    project_id,
                    sub_id,
                    day_text,
                    float((idx + 1) * (sub_idx + 1)),
                )

        src.save_timer_state(321.0, "paused")
        for idx in range(250):
            src.log_activity(f"bulk-{idx}", "Bulk")

        export_path = tmp_path / "bulk.json"
        src.export_json(export_path)

        dst = Storage(tmp_path / "dst_large.db")
        dst.import_json(export_path)

        projects = dst.list_projects()
        assert len(projects) == 80

        expected_total = sum(float(idx + 1) for idx in range(80))
        assert dst.get_daily_total(day_text) == pytest.approx(expected_total)

        sub_data = dst.get_date_range_sub_activity_data(
            date(2026, 6, 1),
            date(2026, 6, 1),
        )
        assert sum(len(project_map) for project_map in sub_data.values()) == len(
            created_sub_ids
        )

        state = dst.load_timer_state()
        assert state is not None
        assert state["elapsed_seconds"] == pytest.approx(321.0)
        assert state["state"] == "paused"

        log_rows = dst.get_activity_log(limit=300)
        assert len(log_rows) == 250
        assert log_rows[0]["action"] == "bulk-0"

    def test_import_rejects_large_payload_with_single_invalid_row(self, tmp_path):
        dst = Storage(tmp_path / "dst_invalid_large.db")
        existing_id = dst.create_project("Existing", "")

        projects = [
            {
                "id": idx + 1,
                "name": f"P{idx}",
                "description": "",
                "elapsed_seconds": 0,
                "created_at": "2026-06-01T00:00:00",
                "ref_number": "",
                "alias": "",
                "color": "",
                "archived": False,
                "notes": "",
            }
            for idx in range(120)
        ]
        daily_rows = [
            {
                "date": "2026-06-01",
                "project_id": idx + 1,
                "seconds": float(idx + 1),
            }
            for idx in range(120)
        ]
        daily_rows.append(
            {
                "date": "not-a-date",
                "project_id": 1,
                "seconds": 1.0,
            }
        )

        payload = {
            "export_version": 1,
            "schema_version": 1,
            "projects": projects,
            "sub_activities": [],
            "daily_time_log": daily_rows,
            "daily_sub_time_log": [],
            "activity_log": [],
            "timer_state": None,
        }
        path = tmp_path / "invalid_large.json"
        path.write_text(json.dumps(payload), encoding="utf-8")

        with pytest.raises(ValueError):
            dst.import_json(path)

        existing_projects = dst.list_projects()
        assert len(existing_projects) == 1
        assert existing_projects[0]["id"] == existing_id
        assert existing_projects[0]["name"] == "Existing"
