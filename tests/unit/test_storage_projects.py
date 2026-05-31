"""Unit tests for Storage project and app-state methods."""

from pathlib import Path

import pytest

from src.storage import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


class TestProjectCrud:
    def test_create_returns_int_id(self, storage):
        pid = storage.create_project("Alpha", "desc")
        assert isinstance(pid, int)

    def test_list_empty_at_start(self, storage):
        assert storage.list_projects() == []

    def test_create_and_list(self, storage):
        storage.create_project("Alpha", "first project")
        rows = storage.list_projects()
        assert len(rows) == 1
        assert rows[0]["name"] == "Alpha"
        assert rows[0]["description"] == "first project"
        assert rows[0]["elapsed_seconds"] == pytest.approx(0.0)

    def test_list_ordered_by_insertion(self, storage):
        storage.create_project("Beta", "")
        storage.create_project("Alpha", "")
        names = [r["name"] for r in storage.list_projects()]
        assert names == ["Beta", "Alpha"]

    def test_update_name_and_description(self, storage):
        pid = storage.create_project("Old", "old desc")
        storage.update_project(pid, "New", "new desc")
        row = storage.list_projects()[0]
        assert row["name"] == "New"
        assert row["description"] == "new desc"

    def test_delete_removes_project(self, storage):
        pid = storage.create_project("Temp", "")
        storage.delete_project(pid)
        assert storage.list_projects() == []

    def test_save_and_reload_elapsed(self, storage):
        pid = storage.create_project("Work", "")
        storage.save_project_elapsed(pid, 1234.5)
        row = storage.list_projects()[0]
        assert row["elapsed_seconds"] == pytest.approx(1234.5)

    def test_save_elapsed_overwrites(self, storage):
        pid = storage.create_project("Work", "")
        storage.save_project_elapsed(pid, 100.0)
        storage.save_project_elapsed(pid, 200.0)
        row = storage.list_projects()[0]
        assert row["elapsed_seconds"] == pytest.approx(200.0)

    def test_created_at_is_populated(self, storage):
        storage.create_project("X", "")
        row = storage.list_projects()[0]
        assert row["created_at"] != ""

    def test_project_row_has_id(self, storage):
        pid = storage.create_project("Y", "")
        row = storage.list_projects()[0]
        assert row["id"] == pid


class TestAppState:
    def test_get_missing_key_returns_none(self, storage):
        assert storage.get_app_state("missing") is None

    def test_set_and_get(self, storage):
        storage.set_app_state("active_project_id", "42")
        assert storage.get_app_state("active_project_id") == "42"

    def test_set_overwrites(self, storage):
        storage.set_app_state("k", "one")
        storage.set_app_state("k", "two")
        assert storage.get_app_state("k") == "two"

    def test_multiple_keys_are_independent(self, storage):
        storage.set_app_state("a", "1")
        storage.set_app_state("b", "2")
        assert storage.get_app_state("a") == "1"
        assert storage.get_app_state("b") == "2"


class TestProjectMetadata:
    def test_create_with_metadata(self, storage):
        pid = storage.create_project(
            "X", "d", ref_number="R1", alias="al", color="#FF0000", notes="n"
        )
        row = storage.list_projects()[0]
        assert row["id"] == pid
        assert row["ref_number"] == "R1"
        assert row["alias"] == "al"
        assert row["color"] == "#FF0000"
        assert row["notes"] == "n"
        assert row["archived"] is False

    def test_create_default_metadata_is_empty(self, storage):
        storage.create_project("Y", "")
        row = storage.list_projects()[0]
        assert row["ref_number"] == ""
        assert row["alias"] == ""
        assert row["color"] == ""
        assert row["notes"] == ""
        assert row["archived"] is False

    def test_update_with_metadata(self, storage):
        pid = storage.create_project("Old", "")
        storage.update_project(
            pid, "New", "d", ref_number="R2", alias="al2", color="#0F0"
        )
        row = storage.list_projects()[0]
        assert row["ref_number"] == "R2"
        assert row["alias"] == "al2"
        assert row["color"] == "#0F0"

    def test_set_project_archived_true(self, storage):
        pid = storage.create_project("A", "")
        storage.set_project_archived(pid, True)
        assert storage.list_projects()[0]["archived"] is True

    def test_set_project_archived_false(self, storage):
        pid = storage.create_project("A", "")
        storage.set_project_archived(pid, True)
        storage.set_project_archived(pid, False)
        assert storage.list_projects()[0]["archived"] is False
