"""Design validation tests that enforce architecture and data guarantees."""

import ast
import sqlite3
from pathlib import Path

import pytest

from src.storage import Storage

pytestmark = pytest.mark.design_validation

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _top_level_imports(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_core_modules_do_not_depend_on_ui_layer() -> None:
    core_modules = [
        PROJECT_ROOT / "src" / "app_service.py",
        PROJECT_ROOT / "src" / "config.py",
        PROJECT_ROOT / "src" / "instance.py",
        PROJECT_ROOT / "src" / "projects.py",
        PROJECT_ROOT / "src" / "storage.py",
        PROJECT_ROOT / "src" / "sub_activities.py",
        PROJECT_ROOT / "src" / "timer.py",
    ]
    for module in core_modules:
        imports = _top_level_imports(module)
        offending = [name for name in imports if name.startswith("src.ui")]
        assert not offending, f"{module.name} imports UI layer modules: {offending}"


def test_timer_module_stays_pure_and_does_not_import_storage_or_ui() -> None:
    timer_imports = _top_level_imports(PROJECT_ROOT / "src" / "timer.py")
    forbidden = {"src.storage", "src.ui", "tkinter"}
    assert not any(
        name in forbidden or name.startswith("src.ui") for name in timer_imports
    )


def test_storage_enforces_foreign_keys_for_daily_time_log(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "design_fk.db")
    with pytest.raises(sqlite3.IntegrityError):
        with storage._connect() as conn:
            conn.execute(
                "INSERT INTO daily_time_log (date, project_id, seconds)"
                " VALUES (?, ?, ?)",
                ("2026-03-30", 999_999, 15.0),
            )


def test_storage_creates_required_tables(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "design_schema.db")
    with storage._connect() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    table_names = {row[0] for row in rows}
    required = {
        "timer_state",
        "activity_log",
        "projects",
        "daily_time_log",
        "sub_activities",
        "daily_sub_time_log",
        "schema_migrations",
        "app_state",
    }
    assert required.issubset(table_names)
