"""Small additional tests for service/project edge branches."""

from pathlib import Path

from src.app_service import AppService
from src.projects import ProjectManager
from src.storage import Storage


def test_app_service_backup_without_keep_calls_default(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "svc.db")
    pm = ProjectManager(storage)
    svc = AppService(storage=storage, project_manager=pm)
    svc.backup()


def test_project_manager_invalid_active_project_id_falls_back_to_first(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "projects.db"
    storage = Storage(db_path)
    pm = ProjectManager(storage)
    p2 = pm.add("Second", "")
    storage.set_app_state("active_project_id", str(p2.project_id + 999))
    reloaded = ProjectManager(Storage(db_path))
    assert reloaded.active_project is not None
    assert reloaded.active_project.project_id == reloaded.projects[0].project_id
