"""Unit tests for ReportDialog."""

import calendar
from datetime import date, datetime, timedelta
from pathlib import Path
import tkinter as tk

import pytest

from src.projects import ProjectManager
from src.storage import Storage
from src.ui.dialogs.report_dialog import ReportDialog, _fmt, _fmt_total
from src.ui.dialogs.report_payload import compute_refresh_payload
from src.ui.themes import MATRIX

pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def root_tk():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk is not available in this environment: {exc}")
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def _wait_for_refresh(dialog: ReportDialog, timeout_iters: int = 40) -> None:
    """Wait until async refresh populates tree columns."""
    tree = dialog._tree
    assert tree is not None
    for _ in range(timeout_iters):
        dialog._win.update()
        if list(tree["columns"]):
            return
    raise AssertionError("report tree did not populate in time")


@pytest.fixture
def seeded(tmp_path: Path):
    storage = Storage(tmp_path / "report.db")
    pm = ProjectManager(storage)
    p2 = pm.add("Report Two", "")
    today = date.today()
    storage.add_daily_seconds(pm.active_project.project_id, today.isoformat(), 3600.0)
    storage.add_daily_seconds(p2.project_id, today.isoformat(), 1800.0)
    storage.add_daily_seconds(
        pm.active_project.project_id,
        (today - timedelta(days=1)).isoformat(),
        1200.0,
    )
    return storage, pm, p2


@pytest.fixture
def dlg(root_tk, seeded):
    storage, pm, _p2 = seeded
    d = ReportDialog(root_tk, storage, pm, MATRIX)
    _wait_for_refresh(d)
    yield d
    if not d._closed:
        d._close()


class TestReportDialog:
    def test_format_helpers(self):
        assert _fmt(59) == ""
        assert _fmt(3600) == "1:00"
        assert _fmt_total(0).startswith("\u23f0 ")

    def test_build_and_refresh_monthly(self, dlg: ReportDialog):
        assert dlg._tree is not None
        _wait_for_refresh(dlg)
        assert len(dlg._tree["columns"]) >= 3
        assert len(dlg._tree.get_children()) >= 1

    def test_switch_mode_weekly_and_back(self, dlg: ReportDialog):
        dlg._switch_mode("weekly")
        _wait_for_refresh(dlg)
        assert dlg._view_mode == "weekly"
        assert "Weekly" in dlg._title_lbl.cget("text")
        dlg._switch_mode("monthly")
        _wait_for_refresh(dlg)
        assert dlg._view_mode == "monthly"
        assert "Monthly" in dlg._title_lbl.cget("text")

    def test_filter_changed_to_specific_project(self, dlg: ReportDialog, seeded):
        _storage, pm, p2 = seeded
        dlg._filter_var.set("Report Two")
        dlg._on_filter_changed()
        assert dlg._filter_project_id == p2.project_id
        dlg._filter_var.set("All Projects")
        dlg._on_filter_changed()
        assert dlg._filter_project_id is None

    def test_sorted_rows_and_sort_toggle(self, dlg: ReportDialog):
        rows = [
            {"name": "B", "d1": 10.0, "total": 10.0},
            {"name": "A", "d1": 20.0, "total": 20.0},
        ]
        dlg._sort_column = "name"
        dlg._sort_desc = False
        out = dlg._sorted_rows(rows)
        assert out[0]["name"] == "A"
        old_desc = dlg._sort_desc
        dlg._sort_by("name")
        _wait_for_refresh(dlg)
        assert dlg._sort_desc != old_desc

    def test_copy_summary_and_enter_copy(self, dlg: ReportDialog):
        dlg._refresh()
        _wait_for_refresh(dlg)
        dlg._copy_summary()
        clip = dlg._win.clipboard_get()
        assert "Project / Activity" in clip

    def test_shift_wheel_shortcut(self, dlg: ReportDialog):
        assert dlg._on_shift_wheel(type("E", (), {"delta": 120})()) == "break"

    def test_export_csv_and_txt_monthly(self, dlg: ReportDialog, tmp_path: Path):
        csv_file = tmp_path / "monthly.csv"
        txt_file = tmp_path / "monthly.txt"
        dlg._refresh()
        _wait_for_refresh(dlg)
        dlg._export_csv_monthly(str(csv_file), dlg._year, dlg._month)
        dlg._export_txt_monthly(str(txt_file), dlg._year, dlg._month)
        assert csv_file.exists()
        assert txt_file.exists()

    def test_export_csv_and_txt_weekly(self, dlg: ReportDialog, tmp_path: Path):
        csv_file = tmp_path / "weekly.csv"
        txt_file = tmp_path / "weekly.txt"
        dlg._switch_mode("weekly")
        dlg._export_csv_weekly(str(csv_file))
        dlg._export_txt_weekly(str(txt_file))
        assert csv_file.exists()
        assert txt_file.exists()

    def test_export_dispatch_uses_dialog_path(
        self, dlg: ReportDialog, tmp_path: Path, monkeypatch
    ):
        out = tmp_path / "out.csv"
        monkeypatch.setattr(
            "src.ui.dialogs.report_dialog.filedialog.asksaveasfilename",
            lambda **kwargs: str(out),
        )
        monkeypatch.setattr(
            "src.ui.dialogs.report_dialog.messagebox.showinfo", lambda *a, **k: None
        )
        monkeypatch.setattr(
            "src.ui.dialogs.report_dialog.messagebox.showerror", lambda *a, **k: None
        )
        dlg._export()
        assert out.exists()

    def test_week_helpers_and_date_controls(self, dlg: ReportDialog):
        assert isinstance(ReportDialog._weekend_days(2026, 3), list)
        dlg._week_start = date(2026, 3, 2)
        assert "," in dlg._week_label()
        dlg._year_var.set(str(datetime.now().year))
        dlg._month_var.set(calendar.month_name[3])
        dlg._on_date_changed()
        dlg._prev_month()
        dlg._next_month()
        dlg._prev_week()
        dlg._next_week()

    def test_presets(self, dlg: ReportDialog):
        dlg._switch_mode("monthly")
        dlg._preset_this_month()
        assert dlg._view_mode == "monthly"
        dlg._preset_last_month()
        dlg._preset_this_week()
        assert dlg._view_mode == "weekly"

    def test_close_marks_dialog_closed(self, root_tk, seeded):
        storage, pm, _p2 = seeded
        d = ReportDialog(root_tk, storage, pm, MATRIX)
        d._refresh()
        d._prev_month()
        d._next_month()
        d._close()
        assert d._closed is True

    def test_refresh_uses_live_segment_getter(self, root_tk, seeded, monkeypatch):
        storage, pm, _p2 = seeded
        captured: list[dict] = []

        def fake_compute_refresh_payload(_storage, request):
            captured.append(dict(request))
            return {
                "mode": "monthly",
                "columns": ["d1", "total"],
                "day_cols": ["d1"],
                "weekend_days": [],
                "rows": [{"name": "P", "d1": 0.0, "total": 0.0, "children": []}],
                "totals": {"d1": 0.0, "total": 0.0},
                "range_text": "Now",
                "rows_total": 1,
            }

        monkeypatch.setattr(
            "src.ui.dialogs.report_dialog.compute_refresh_payload",
            fake_compute_refresh_payload,
        )

        active_id = pm.active_project.project_id
        d = ReportDialog(
            root_tk,
            storage,
            pm,
            MATRIX,
            live_segment_getter=lambda: (active_id, 123.0),
            active_sub_id_getter=lambda: 42,
        )
        _wait_for_refresh(d)

        assert captured
        assert any(req.get("live_project_id") == active_id for req in captured)
        assert any(req.get("live_sub_activity_id") == 42 for req in captured)
        assert any(req.get("live_delta") == pytest.approx(123.0) for req in captured)
        d._close()

    def test_selection_persists_after_payload_refresh(self, dlg: ReportDialog):
        tree = dlg._tree
        assert tree is not None
        top_rows = [
            iid
            for iid in tree.get_children("")
            if tree.item(iid, "text") != "DAILY TOTALS"
        ]
        assert top_rows
        selected_iid = top_rows[0]
        selected_text = str(tree.item(selected_iid, "text"))
        tree.selection_set(selected_iid)

        live_project_id, live_sub_id, live_delta = dlg._resolve_live_segment()
        request = {
            "mode": dlg._view_mode,
            "year": dlg._year,
            "month": dlg._month,
            "week_start": dlg._week_start,
            "projects": [
                {"project_id": p.project_id, "name": p.name, "alias": p.alias}
                for p in dlg._filtered_projects()
            ],
            "live_project_id": live_project_id,
            "live_sub_activity_id": live_sub_id,
            "live_delta": live_delta,
        }
        payload = compute_refresh_payload(dlg._storage, request)
        dlg._apply_refresh_payload(payload)

        selected = tree.selection()
        assert selected
        assert str(tree.item(selected[0], "text")) == selected_text
