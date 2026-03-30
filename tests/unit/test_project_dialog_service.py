from __future__ import annotations

from unittest.mock import Mock

import src.app.services.project_dialog_service as service_mod
from src.app.services.project_dialog_service import ProjectDialogService


def test_service_unavailable_without_storage() -> None:
    svc = ProjectDialogService(None)

    assert svc.available is False
    assert svc.list_sub_activities(1) == []
    assert svc.get_daily_seconds_by_project("2026-01-01") == {}

    # No-ops when storage is unavailable.
    svc.add_sub_activity(1, "Task")
    svc.delete_sub_activity(10)
    svc.update_sub_activity(1, 10, "Task", "Desc")
    svc.set_sub_activity_archived(1, 10, True)


def test_storage_forwarding_methods() -> None:
    storage = Mock()
    storage.list_sub_activities.return_value = [{"id": 1, "name": "A"}]
    storage.get_daily_seconds_by_project.return_value = {1: 30.0}
    svc = ProjectDialogService(storage)

    assert svc.available is True
    assert svc.list_sub_activities(5) == [{"id": 1, "name": "A"}]
    assert svc.get_daily_seconds_by_project("2026-01-01") == {1: 30.0}

    storage.list_sub_activities.assert_called_once_with(5)
    storage.get_daily_seconds_by_project.assert_called_once_with("2026-01-01")

    svc.delete_sub_activity(11)
    storage.delete_sub_activity.assert_called_once_with(11)


def test_sub_activity_manager_operations(monkeypatch) -> None:
    storage = Mock()
    svc = ProjectDialogService(storage)
    fake_manager = Mock()

    def fake_ctor(storage_arg, project_id_arg):
        assert storage_arg is storage
        assert project_id_arg == 9
        return fake_manager

    monkeypatch.setattr(service_mod, "SubActivityManager", fake_ctor)

    svc.add_sub_activity(9, "Sub", "Desc")
    fake_manager.add.assert_called_once_with("Sub", "Desc")

    svc.update_sub_activity(9, 3, "Renamed", "Updated")
    fake_manager.update.assert_called_once_with(3, "Renamed", "Updated")

    svc.set_sub_activity_archived(9, 3, True)
    fake_manager.set_archived.assert_called_once_with(3, True)
