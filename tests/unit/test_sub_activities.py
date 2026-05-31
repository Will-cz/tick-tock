"""Unit tests for SubActivityManager and sub-activity storage methods."""

from pathlib import Path

import pytest

from src.storage import Storage
from src.sub_activities import SubActivity, SubActivityManager


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


@pytest.fixture
def project_id(storage: Storage) -> int:
    return storage.create_project("Parent Project", "")


@pytest.fixture
def manager(storage: Storage, project_id: int) -> SubActivityManager:
    return SubActivityManager(storage, project_id)


# ---------------------------------------------------------------------------
# Storage: sub-activity CRUD
# ---------------------------------------------------------------------------


class TestStorageSubActivityCrud:
    def test_create_returns_int_id(self, storage, project_id):
        sid = storage.create_sub_activity(project_id, "Design", "some work")
        assert isinstance(sid, int)

    def test_list_empty_at_start(self, storage, project_id):
        assert storage.list_sub_activities(project_id) == []

    def test_create_and_list(self, storage, project_id):
        storage.create_sub_activity(project_id, "Design", "layout work")
        rows = storage.list_sub_activities(project_id)
        assert len(rows) == 1
        row = rows[0]
        assert row["name"] == "Design"
        assert row["description"] == "layout work"
        assert row["project_id"] == project_id
        assert row["elapsed_seconds"] == pytest.approx(0.0)
        assert row["archived"] is False

    def test_list_ordered_by_insertion(self, storage, project_id):
        storage.create_sub_activity(project_id, "Beta", "")
        storage.create_sub_activity(project_id, "Alpha", "")
        names = [r["name"] for r in storage.list_sub_activities(project_id)]
        assert names == ["Beta", "Alpha"]

    def test_list_scoped_to_project(self, storage, project_id):
        other_id = storage.create_project("Other", "")
        storage.create_sub_activity(project_id, "Mine", "")
        storage.create_sub_activity(other_id, "Theirs", "")
        mine = storage.list_sub_activities(project_id)
        assert len(mine) == 1
        assert mine[0]["name"] == "Mine"

    def test_update_name_and_description(self, storage, project_id):
        sid = storage.create_sub_activity(project_id, "Old", "old desc")
        storage.update_sub_activity(sid, "New", "new desc")
        row = storage.list_sub_activities(project_id)[0]
        assert row["name"] == "New"
        assert row["description"] == "new desc"

    def test_delete_removes_sub_activity(self, storage, project_id):
        sid = storage.create_sub_activity(project_id, "Temp", "")
        storage.delete_sub_activity(sid)
        assert storage.list_sub_activities(project_id) == []

    def test_save_and_reload_elapsed(self, storage, project_id):
        sid = storage.create_sub_activity(project_id, "Task", "")
        storage.save_sub_activity_elapsed(sid, 500.0)
        row = storage.list_sub_activities(project_id)[0]
        assert row["elapsed_seconds"] == pytest.approx(500.0)

    def test_save_elapsed_overwrites(self, storage, project_id):
        sid = storage.create_sub_activity(project_id, "Task", "")
        storage.save_sub_activity_elapsed(sid, 100.0)
        storage.save_sub_activity_elapsed(sid, 250.0)
        row = storage.list_sub_activities(project_id)[0]
        assert row["elapsed_seconds"] == pytest.approx(250.0)

    def test_set_archived_true(self, storage, project_id):
        sid = storage.create_sub_activity(project_id, "Done", "")
        storage.set_sub_activity_archived(sid, True)
        row = storage.list_sub_activities(project_id)[0]
        assert row["archived"] is True

    def test_set_archived_false(self, storage, project_id):
        sid = storage.create_sub_activity(project_id, "Done", "")
        storage.set_sub_activity_archived(sid, True)
        storage.set_sub_activity_archived(sid, False)
        row = storage.list_sub_activities(project_id)[0]
        assert row["archived"] is False

    def test_row_has_id(self, storage, project_id):
        sid = storage.create_sub_activity(project_id, "X", "")
        row = storage.list_sub_activities(project_id)[0]
        assert row["id"] == sid

    def test_created_at_is_populated(self, storage, project_id):
        storage.create_sub_activity(project_id, "X", "")
        row = storage.list_sub_activities(project_id)[0]
        assert row["created_at"] != ""


# ---------------------------------------------------------------------------
# SubActivityManager: add
# ---------------------------------------------------------------------------


class TestSubActivityManagerAdd:
    def test_add_returns_instance(self, manager):
        sa = manager.add("Design")
        assert isinstance(sa, SubActivity)
        assert sa.name == "Design"
        assert sa.description == ""
        assert sa.elapsed_seconds == pytest.approx(0.0)
        assert sa.archived is False

    def test_add_with_description(self, manager):
        sa = manager.add("Coding", "write the feature")
        assert sa.description == "write the feature"

    def test_add_strips_whitespace(self, manager):
        sa = manager.add("  Task  ", "  desc  ")
        assert sa.name == "Task"
        assert sa.description == "desc"

    def test_add_empty_name_raises(self, manager):
        with pytest.raises(ValueError, match="cannot be empty"):
            manager.add("   ")

    def test_add_overly_long_name_raises(self, manager):
        with pytest.raises(ValueError, match="cannot exceed"):
            manager.add("x" * 121)

    def test_add_name_with_control_chars_raises(self, manager):
        with pytest.raises(ValueError, match="control characters"):
            manager.add("Bad\nTask")

    def test_add_duplicate_name_raises(self, manager):
        manager.add("Design")
        with pytest.raises(ValueError, match="already exists"):
            manager.add("Design")

    def test_add_duplicate_name_case_insensitive(self, manager):
        manager.add("Design")
        with pytest.raises(ValueError, match="already exists"):
            manager.add("DESIGN")

    def test_add_appears_in_list(self, manager):
        manager.add("Alpha")
        names = [sa.name for sa in manager.sub_activities]
        assert "Alpha" in names

    def test_add_sets_project_id(self, manager, project_id):
        sa = manager.add("Task")
        assert sa.project_id == project_id

    def test_same_name_in_different_projects(self, storage):
        pid1 = storage.create_project("P1", "")
        pid2 = storage.create_project("P2", "")
        m1 = SubActivityManager(storage, pid1)
        m2 = SubActivityManager(storage, pid2)
        m1.add("Design")
        sa2 = m2.add("Design")  # Should not raise
        assert sa2.name == "Design"


# ---------------------------------------------------------------------------
# SubActivityManager: update
# ---------------------------------------------------------------------------


class TestSubActivityManagerUpdate:
    def test_update_name(self, manager):
        sa = manager.add("Old Name")
        manager.update(sa.sub_activity_id, "New Name")
        assert manager.get(sa.sub_activity_id).name == "New Name"

    def test_update_description(self, manager):
        sa = manager.add("Task")
        manager.update(sa.sub_activity_id, "Task", "updated desc")
        assert manager.get(sa.sub_activity_id).description == "updated desc"

    def test_update_strips_whitespace(self, manager):
        sa = manager.add("Task")
        manager.update(sa.sub_activity_id, "  New  ", "  desc  ")
        updated = manager.get(sa.sub_activity_id)
        assert updated.name == "New"
        assert updated.description == "desc"

    def test_update_empty_name_raises(self, manager):
        sa = manager.add("Task")
        with pytest.raises(ValueError, match="cannot be empty"):
            manager.update(sa.sub_activity_id, "  ")

    def test_update_overly_long_name_raises(self, manager):
        sa = manager.add("Task")
        with pytest.raises(ValueError, match="cannot exceed"):
            manager.update(sa.sub_activity_id, "x" * 121)

    def test_update_name_with_control_chars_raises(self, manager):
        sa = manager.add("Task")
        with pytest.raises(ValueError, match="control characters"):
            manager.update(sa.sub_activity_id, "Bad\tTask")

    def test_update_duplicate_name_raises(self, manager):
        sa1 = manager.add("Alpha")
        manager.add("Beta")
        with pytest.raises(ValueError, match="already exists"):
            manager.update(sa1.sub_activity_id, "Beta")

    def test_update_same_name_on_same_item(self, manager):
        sa = manager.add("Same")
        manager.update(sa.sub_activity_id, "Same")  # should not raise

    def test_update_nonexistent_raises(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.update(9999, "Anything")

    def test_update_is_persisted(self, storage, project_id):
        m = SubActivityManager(storage, project_id)
        sa = m.add("Old")
        m.update(sa.sub_activity_id, "New", "desc")
        m2 = SubActivityManager(storage, project_id)
        reloaded = m2.get(sa.sub_activity_id)
        assert reloaded.name == "New"
        assert reloaded.description == "desc"


# ---------------------------------------------------------------------------
# SubActivityManager: delete
# ---------------------------------------------------------------------------


class TestSubActivityManagerDelete:
    def test_delete_removes_from_list(self, manager):
        sa = manager.add("Task")
        manager.delete(sa.sub_activity_id)
        assert manager.sub_activities == []

    def test_delete_nonexistent_raises(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.delete(9999)

    def test_delete_is_persisted(self, storage, project_id):
        m = SubActivityManager(storage, project_id)
        sa = m.add("Task")
        m.delete(sa.sub_activity_id)
        m2 = SubActivityManager(storage, project_id)
        assert m2.sub_activities == []

    def test_delete_does_not_affect_other_sub_activities(self, manager):
        sa1 = manager.add("Keep")
        sa2 = manager.add("Remove")
        manager.delete(sa2.sub_activity_id)
        assert len(manager.sub_activities) == 1
        assert manager.sub_activities[0].sub_activity_id == sa1.sub_activity_id


# ---------------------------------------------------------------------------
# SubActivityManager: archive
# ---------------------------------------------------------------------------


class TestSubActivityManagerArchive:
    def test_archive_sets_flag(self, manager):
        sa = manager.add("Task")
        manager.set_archived(sa.sub_activity_id, True)
        assert manager.get(sa.sub_activity_id).archived is True

    def test_unarchive_clears_flag(self, manager):
        sa = manager.add("Task")
        manager.set_archived(sa.sub_activity_id, True)
        manager.set_archived(sa.sub_activity_id, False)
        assert manager.get(sa.sub_activity_id).archived is False

    def test_archive_is_persisted(self, storage, project_id):
        m = SubActivityManager(storage, project_id)
        sa = m.add("Task")
        m.set_archived(sa.sub_activity_id, True)
        m2 = SubActivityManager(storage, project_id)
        assert m2.get(sa.sub_activity_id).archived is True

    def test_archive_nonexistent_raises(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.set_archived(9999, True)


# ---------------------------------------------------------------------------
# SubActivityManager: elapsed time
# ---------------------------------------------------------------------------


class TestSubActivityManagerElapsed:
    def test_save_elapsed_updates_in_memory(self, manager):
        sa = manager.add("Task")
        manager.save_elapsed(sa.sub_activity_id, 120.0)
        assert manager.get(sa.sub_activity_id).elapsed_seconds == pytest.approx(120.0)

    def test_save_elapsed_is_persisted(self, storage, project_id):
        m = SubActivityManager(storage, project_id)
        sa = m.add("Task")
        m.save_elapsed(sa.sub_activity_id, 300.0)
        m2 = SubActivityManager(storage, project_id)
        assert m2.get(sa.sub_activity_id).elapsed_seconds == pytest.approx(300.0)

    def test_save_elapsed_nonexistent_raises(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.save_elapsed(9999, 100.0)

    def test_elapsed_sum_empty(self, manager):
        total = sum(sa.elapsed_seconds for sa in manager.sub_activities)
        assert total == pytest.approx(0.0)

    def test_elapsed_sum_single(self, manager):
        sa = manager.add("Task")
        manager.save_elapsed(sa.sub_activity_id, 60.0)
        total = sum(item.elapsed_seconds for item in manager.sub_activities)
        assert total == pytest.approx(60.0)

    def test_elapsed_sum_multiple(self, manager):
        sa1 = manager.add("Task A")
        sa2 = manager.add("Task B")
        manager.save_elapsed(sa1.sub_activity_id, 100.0)
        manager.save_elapsed(sa2.sub_activity_id, 200.0)
        total = sum(item.elapsed_seconds for item in manager.sub_activities)
        assert total == pytest.approx(300.0)


# ---------------------------------------------------------------------------
# SubActivityManager: reload
# ---------------------------------------------------------------------------


class TestSubActivityManagerReload:
    def test_reload_picks_up_external_changes(self, storage, project_id):
        m = SubActivityManager(storage, project_id)
        storage.create_sub_activity(project_id, "External", "")
        m.reload()
        names = [sa.name for sa in m.sub_activities]
        assert "External" in names

    def test_reload_reflects_deletion(self, storage, project_id):
        m = SubActivityManager(storage, project_id)
        sa = m.add("Temp")
        storage.delete_sub_activity(sa.sub_activity_id)
        m.reload()
        assert m.sub_activities == []


# ---------------------------------------------------------------------------
# Storage: schema migration v4
# ---------------------------------------------------------------------------


class TestStorageSchemaMigrationV4:
    def test_sub_activities_table_exists(self, storage):
        """Current baseline schema should include the sub_activities table."""
        with storage._connect() as conn:  # noqa: SLF001
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert "sub_activities" in tables

    def test_schema_version_is_1(self, storage):
        with storage._connect() as conn:  # noqa: SLF001
            applied = {
                row[0]
                for row in conn.execute(
                    "SELECT version FROM schema_migrations"
                ).fetchall()
            }
        assert 1 in applied
