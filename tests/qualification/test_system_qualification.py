"""Qualification tests for high-value user scenarios."""

from pathlib import Path

import pytest

from src.projects import ProjectManager
from src.storage import RecoveryStatus, Storage

pytestmark = pytest.mark.qualification


def test_first_run_creates_default_project_and_sets_it_active(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "qual_default.db")
    pm = ProjectManager(storage)

    assert len(pm.projects) == 1
    assert pm.projects[0].name == "Default"
    assert pm.active_project is not None
    assert pm.active_project.name == "Default"


def test_startup_migrates_saved_timer_elapsed_into_default_project(
    tmp_path: Path,
) -> None:
    storage = Storage(tmp_path / "qual_migrate.db")
    storage.save_timer_state(95.0, "stopped")

    pm = ProjectManager(storage)
    assert pm.active_project is not None
    assert pm.active_project.name == "Default"
    assert pm.active_project.elapsed_seconds == pytest.approx(95.0)


def test_restart_preserves_active_project_choice_and_elapsed(tmp_path: Path) -> None:
    db_path = tmp_path / "qual_restart.db"
    storage = Storage(db_path)
    pm = ProjectManager(storage)

    project = pm.add("Client A", "Restart qualification")
    pm.switch(project.project_id)
    pm.save_elapsed(720.0)

    restarted_pm = ProjectManager(Storage(db_path))
    assert restarted_pm.active_project is not None
    assert restarted_pm.active_project.project_id == project.project_id
    assert restarted_pm.active_project.elapsed_seconds == pytest.approx(720.0)


def test_open_or_recover_with_status_recovers_primary_db_from_backup_after_corruption(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "qual_recovery.db"
    storage = Storage(db_path)
    created_id = storage.create_project("Recovery Project", "Qualification")
    storage.save_project_elapsed(created_id, 111.0)
    backup_path = storage.backup()

    assert backup_path is not None and backup_path.exists()

    db_path.write_text("not-a-sqlite-db", encoding="utf-8")

    recovered_storage, status = Storage.open_or_recover_with_status(db_path)
    assert status == RecoveryStatus.RECOVERED_FROM_BACKUP

    names = [row["name"] for row in recovered_storage.list_projects()]
    assert "Recovery Project" in names
