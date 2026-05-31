"""Unit tests for ProjectManager."""

from pathlib import Path

import pytest

from src.projects import Project, ProjectManager
from src.storage import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


@pytest.fixture
def pm(storage: Storage) -> ProjectManager:
    return ProjectManager(storage)


# ---------------------------------------------------------------------------
# First-run bootstrap
# ---------------------------------------------------------------------------


class TestProjectManagerBootstrap:
    def test_creates_default_project_on_empty_db(self, pm):
        assert len(pm.projects) == 1
        assert pm.projects[0].name == "Default"

    def test_active_project_is_default(self, pm):
        assert pm.active_project is not None
        assert pm.active_project.name == "Default"

    def test_migrates_existing_timer_state(self, storage, tmp_path):
        # Simulate a v0.1.1 DB that already has saved timer state.
        storage.save_timer_state(300.0, "stopped")
        fresh_pm = ProjectManager(storage)
        assert fresh_pm.active_project is not None
        assert fresh_pm.active_project.elapsed_seconds == pytest.approx(300.0)

    def test_no_migration_when_timer_state_is_zero(self, storage):
        storage.save_timer_state(0.0, "stopped")
        fresh_pm = ProjectManager(storage)
        assert fresh_pm.active_project is not None
        assert fresh_pm.active_project.elapsed_seconds == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------


class TestProjectManagerAdd:
    def test_add_returns_project_instance(self, pm):
        p = pm.add("Work", "my work")
        assert isinstance(p, Project)
        assert p.name == "Work"
        assert p.description == "my work"
        assert p.elapsed_seconds == pytest.approx(0.0)

    def test_add_appears_in_project_list(self, pm):
        pm.add("Alpha", "")
        names = [x.name for x in pm.projects]
        assert "Alpha" in names

    def test_add_strips_whitespace(self, pm):
        p = pm.add("  Spaces  ", "  desc  ")
        assert p.name == "Spaces"
        assert p.description == "desc"

    def test_add_empty_name_raises(self, pm):
        with pytest.raises(ValueError, match="cannot be empty"):
            pm.add("   ")

    def test_add_overly_long_name_raises(self, pm):
        with pytest.raises(ValueError, match="cannot exceed"):
            pm.add("x" * 121)

    def test_add_name_with_control_chars_raises(self, pm):
        with pytest.raises(ValueError, match="control characters"):
            pm.add("Bad\nName")

    def test_add_duplicate_name_raises(self, pm):
        pm.add("Same", "")
        with pytest.raises(ValueError, match="already exists"):
            pm.add("Same", "different desc")

    def test_add_duplicate_name_case_insensitive(self, pm):
        pm.add("Work", "")
        with pytest.raises(ValueError):
            pm.add("work", "")

    def test_add_persisted_to_db(self, storage):
        pm = ProjectManager(storage)
        pm.add("DB Test", "test desc")
        # Reload from storage to verify persistence
        pm2 = ProjectManager(storage)
        names = [p.name for p in pm2.projects]
        assert "DB Test" in names


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestProjectManagerUpdate:
    def test_update_changes_name(self, pm):
        p = pm.add("Old", "")
        pm.update(p.project_id, "New", "")
        assert p.name == "New"

    def test_update_changes_description(self, pm):
        p = pm.add("X", "old desc")
        pm.update(p.project_id, "X", "new desc")
        assert p.description == "new desc"

    def test_update_empty_name_raises(self, pm):
        p = pm.add("Valid", "")
        with pytest.raises(ValueError, match="cannot be empty"):
            pm.update(p.project_id, "  ", "")

    def test_update_overly_long_name_raises(self, pm):
        p = pm.add("Valid", "")
        with pytest.raises(ValueError, match="cannot exceed"):
            pm.update(p.project_id, "x" * 121, "")

    def test_update_name_with_control_chars_raises(self, pm):
        p = pm.add("Valid", "")
        with pytest.raises(ValueError, match="control characters"):
            pm.update(p.project_id, "Bad\tName", "")

    def test_update_duplicate_name_raises(self, pm):
        a = pm.add("Alpha", "")
        pm.add("Beta", "")
        with pytest.raises(ValueError, match="already exists"):
            pm.update(a.project_id, "Beta", "")

    def test_update_same_name_is_allowed(self, pm):
        p = pm.add("Same", "")
        pm.update(p.project_id, "Same", "updated desc")
        assert p.description == "updated desc"

    def test_update_invalid_id_raises(self, pm):
        with pytest.raises(ValueError, match="not found"):
            pm.update(9999, "X", "")

    def test_update_persisted_to_db(self, storage):
        pm = ProjectManager(storage)
        p = pm.add("Before", "")
        pm.update(p.project_id, "After", "changed")
        pm2 = ProjectManager(storage)
        updated = next(x for x in pm2.projects if x.project_id == p.project_id)
        assert updated.name == "After"
        assert updated.description == "changed"


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestProjectManagerDelete:
    def test_delete_removes_from_list(self, pm):
        p = pm.add("Temp", "")
        pm.delete(p.project_id)
        assert all(x.project_id != p.project_id for x in pm.projects)

    def test_delete_invalid_id_raises(self, pm):
        with pytest.raises(ValueError, match="not found"):
            pm.delete(9999)

    def test_delete_active_project_shifts_active_to_first(self, pm):
        # Bootstrap gives us "Default"; add another
        second = pm.add("Second", "")
        default_id = pm.projects[0].project_id
        pm.switch(default_id)  # make Default active
        pm.delete(default_id)
        assert pm.active_project is not None
        assert pm.active_project.project_id == second.project_id

    def test_delete_persisted_to_db(self, storage):
        pm = ProjectManager(storage)
        p = pm.add("Gone", "")
        pm.delete(p.project_id)
        pm2 = ProjectManager(storage)
        assert all(x.project_id != p.project_id for x in pm2.projects)


# ---------------------------------------------------------------------------
# Switch
# ---------------------------------------------------------------------------


class TestProjectManagerSwitch:
    def test_switch_changes_active_project(self, pm):
        second = pm.add("Second", "")
        pm.switch(second.project_id)
        assert pm.active_project is not None
        assert pm.active_project.project_id == second.project_id

    def test_switch_invalid_id_raises(self, pm):
        with pytest.raises(ValueError, match="not found"):
            pm.switch(9999)

    def test_switch_persisted_across_reload(self, storage):
        pm = ProjectManager(storage)
        second = pm.add("Second", "")
        pm.switch(second.project_id)
        pm2 = ProjectManager(storage)
        assert pm2.active_project is not None
        assert pm2.active_project.project_id == second.project_id


# ---------------------------------------------------------------------------
# Save elapsed
# ---------------------------------------------------------------------------


class TestProjectManagerSaveElapsed:
    def test_save_elapsed_updates_in_memory(self, pm):
        pm.save_elapsed(123.0)
        assert pm.active_project is not None
        assert pm.active_project.elapsed_seconds == pytest.approx(123.0)

    def test_save_elapsed_persists_to_db(self, storage):
        pm = ProjectManager(storage)
        pm.save_elapsed(999.5)
        pm2 = ProjectManager(storage)
        assert pm2.active_project is not None
        assert pm2.active_project.elapsed_seconds == pytest.approx(999.5)

    def test_save_elapsed_no_active_project_is_safe(self, storage):
        # Create a PM with no active project (edge-case: all projects deleted)
        pm = ProjectManager(storage)
        default = pm.projects[0]
        pm.add("Second", "")
        pm.delete(default.project_id)
        # Manually wipe the remaining project active reference
        pm._active_id = None  # type: ignore[attr-defined]
        pm.save_elapsed(50.0)  # should not raise


# ---------------------------------------------------------------------------
# Persist active project across reload
# ---------------------------------------------------------------------------


class TestProjectManagerPersistence:
    def test_active_project_survives_reload(self, storage):
        pm = ProjectManager(storage)
        second = pm.add("Second", "")
        pm.switch(second.project_id)
        pm2 = ProjectManager(storage)
        assert pm2.active_project is not None
        assert pm2.active_project.name == "Second"

    def test_invalid_active_id_falls_back_to_first(self, storage):
        ProjectManager(storage)  # bootstrap default project
        storage.set_app_state("active_project_id", "9999")
        pm2 = ProjectManager(storage)
        assert pm2.active_project is not None
        assert pm2.active_project.project_id == pm2.projects[0].project_id

    def test_non_numeric_active_id_falls_back_to_first(self, storage):
        """Corrupt app_state value triggers ValueError fallback."""
        ProjectManager(storage)
        storage.set_app_state("active_project_id", "not-a-number")
        pm2 = ProjectManager(storage)
        assert pm2.active_project is not None
        assert pm2.active_project.project_id == pm2.projects[0].project_id

    def test_metadata_fields_survive_reload(self, storage):
        pm = ProjectManager(storage)
        p = pm.add(
            "X", "desc", ref_number="R1", alias="x-alias", color="#FF0000", notes="note"
        )
        pm2 = ProjectManager(storage)
        reloaded = next(x for x in pm2.projects if x.project_id == p.project_id)
        assert reloaded.ref_number == "R1"
        assert reloaded.alias == "x-alias"
        assert reloaded.color == "#FF0000"
        assert reloaded.notes == "note"

    def test_archived_flag_survives_reload(self, storage):
        pm = ProjectManager(storage)
        pm.add("Second", "")
        default = pm.projects[0]
        pm.set_archived(default.project_id, True)
        pm2 = ProjectManager(storage)
        archived = next(x for x in pm2.projects if x.project_id == default.project_id)
        assert archived.archived is True


# ---------------------------------------------------------------------------
# Metadata (ref_number, alias, color, notes)
# ---------------------------------------------------------------------------


class TestProjectManagerMetadata:
    def test_add_with_all_metadata(self, pm):
        p = pm.add(
            "Work", "desc", ref_number="R-001", alias="wrk", color="#FF0000", notes="hi"
        )
        assert p.ref_number == "R-001"
        assert p.alias == "wrk"
        assert p.color == "#FF0000"
        assert p.notes == "hi"

    def test_add_strips_ref_and_alias(self, pm):
        p = pm.add("X", "", ref_number="  R1  ", alias="  al  ")
        assert p.ref_number == "R1"
        assert p.alias == "al"

    def test_add_duplicate_alias_raises(self, pm):
        pm.add("A", "", alias="shared")
        with pytest.raises(ValueError, match="already exists"):
            pm.add("B", "", alias="shared")

    def test_add_duplicate_alias_case_insensitive(self, pm):
        pm.add("A", "", alias="MyAlias")
        with pytest.raises(ValueError):
            pm.add("B", "", alias="myalias")

    def test_add_empty_alias_is_allowed_multiple_times(self, pm):
        pm.add("A", "", alias="")
        pm.add("B", "", alias="")  # empty alias is not unique-checked

    def test_update_sets_metadata(self, pm):
        p = pm.add("X", "")
        pm.update(
            p.project_id,
            "X",
            "",
            ref_number="R2",
            alias="al2",
            color="#00FF00",
            notes="n",
        )
        assert p.ref_number == "R2"
        assert p.alias == "al2"
        assert p.color == "#00FF00"
        assert p.notes == "n"

    def test_update_duplicate_alias_raises(self, pm):
        pm.add("A", "", alias="taken")
        b = pm.add("B", "")
        with pytest.raises(ValueError, match="already exists"):
            pm.update(b.project_id, "B", "", alias="taken")

    def test_update_same_alias_is_allowed(self, pm):
        p = pm.add("X", "", alias="myalias")
        pm.update(p.project_id, "X", "new desc", alias="myalias")
        assert p.alias == "myalias"
        assert p.description == "new desc"


# ---------------------------------------------------------------------------
# Archive
# ---------------------------------------------------------------------------


class TestProjectManagerArchive:
    def test_archive_sets_flag(self, pm):
        pm.add("Second", "")
        default = pm.projects[0]
        pm.set_archived(default.project_id, True)
        assert default.archived is True

    def test_unarchive_clears_flag(self, pm):
        pm.add("Second", "")
        default = pm.projects[0]
        pm.set_archived(default.project_id, True)
        pm.set_archived(default.project_id, False)
        assert default.archived is False

    def test_archive_invalid_id_raises(self, pm):
        with pytest.raises(ValueError, match="not found"):
            pm.set_archived(9999, True)

    def test_archive_active_project_switches_active(self, pm):
        second = pm.add("Second", "")
        default = pm.projects[0]
        pm.switch(default.project_id)
        pm.set_archived(default.project_id, True)
        assert pm.active_project is not None
        assert pm.active_project.project_id == second.project_id

    def test_archive_non_active_project_leaves_active_unchanged(self, pm):
        second = pm.add("Second", "")
        default = pm.projects[0]
        pm.switch(default.project_id)
        pm.set_archived(second.project_id, True)
        assert pm.active_project is not None
        assert pm.active_project.project_id == default.project_id

    def test_archive_all_projects_clears_active(self, pm):
        default = pm.projects[0]
        pm.switch(default.project_id)
        pm.set_archived(default.project_id, True)
        assert pm.active_project is None

    def test_archive_persisted_to_db(self, storage):
        pm = ProjectManager(storage)
        pm.add("Second", "")
        default = pm.projects[0]
        pm.set_archived(default.project_id, True)
        pm2 = ProjectManager(storage)
        reloaded = next(x for x in pm2.projects if x.project_id == default.project_id)
        assert reloaded.archived is True
