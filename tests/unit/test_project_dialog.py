"""Unit tests for ProjectManagementDialog."""

from pathlib import Path
from datetime import date

import pytest
import tkinter as tk

from src.ui.dialogs.project_dialog import ProjectManagementDialog
from src.projects import ProjectManager
from src.storage import Storage
from src.sub_activities import SubActivityManager
from src.ui.formatting import format_elapsed

pytestmark = pytest.mark.gui


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def root_tk():
    """One hidden Tk root shared across all dialog tests in this module."""
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


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "test.db")


@pytest.fixture
def pm(storage: Storage) -> ProjectManager:
    return ProjectManager(storage)


@pytest.fixture
def dlg(root_tk, pm):
    """Create a dialog, yield it, then close it."""
    d = ProjectManagementDialog(root_tk, pm)
    yield d
    try:
        d.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Instantiation - covers __init__, _build, _build_form, _refresh_list
# ---------------------------------------------------------------------------


class TestDialogInstantiation:
    def test_creates_window(self, dlg):
        assert dlg._win is not None
        assert dlg._win.winfo_exists()

    def test_listbox_exists(self, dlg):
        assert dlg._listbox is not None

    def test_toolbar_buttons_exist(self, dlg):
        assert dlg._edit_btn is not None
        assert dlg._del_btn is not None
        assert dlg._archive_btn is not None

    def test_form_frame_exists_but_not_packed(self, dlg):
        assert dlg._form_frame is not None
        # form is hidden initially - pack_info() raises if not packed
        with pytest.raises(tk.TclError):
            dlg._form_frame.pack_info()

    def test_name_entry_exists(self, dlg):
        assert dlg._name_entry is not None

    def test_notes_text_exists(self, dlg):
        assert dlg._notes_text is not None

    def test_color_btns_created(self, dlg):
        assert len(dlg._color_btns) == 9  # empty + 8 colours

    def test_listbox_shows_default_project(self, dlg, pm):
        items = dlg._listbox.get(0, tk.END)
        assert any(pm.active_project.name in item for item in items)

    def test_callback_optional(self, root_tk, pm):
        d = ProjectManagementDialog(root_tk, pm, on_projects_changed=None)
        d.close()

    def test_callback_wired(self, root_tk, pm):
        called = []
        d = ProjectManagementDialog(
            root_tk, pm, on_projects_changed=lambda: called.append(1)
        )
        d.close()


# ---------------------------------------------------------------------------
# List helpers
# ---------------------------------------------------------------------------


class TestDialogListHelpers:
    def test_visible_projects_excludes_archived(self, root_tk, storage):
        pm = ProjectManager(storage)
        pm.add("Second", "")
        default = pm.projects[0]
        pm.set_archived(default.project_id, True)
        d = ProjectManagementDialog(root_tk, pm)
        visible = d._visible_projects()
        ids = [p.project_id for p in visible]
        assert default.project_id not in ids
        d.close()

    def test_visible_projects_shows_archived_when_toggled(self, root_tk, storage):
        pm = ProjectManager(storage)
        pm.add("Second", "")
        default = pm.projects[0]
        pm.set_archived(default.project_id, True)
        d = ProjectManagementDialog(root_tk, pm)
        d._show_archived_var.set(True)
        visible = d._visible_projects()
        ids = [p.project_id for p in visible]
        assert default.project_id in ids
        d.close()

    def test_selected_project_returns_none_when_nothing_selected(self, dlg):
        dlg._listbox.selection_clear(0, tk.END)
        assert dlg._selected_project() is None

    def test_selected_project_returns_correct_project(self, dlg, pm):
        dlg._listbox.selection_set(0)
        p = dlg._selected_project()
        assert p is not None
        assert p.project_id == dlg._visible_projects()[0].project_id

    def test_on_list_select_enables_buttons(self, dlg):
        dlg._listbox.selection_set(0)
        dlg._on_list_select()
        assert str(dlg._edit_btn["state"]) == "normal"
        assert str(dlg._del_btn["state"]) == "normal"
        assert str(dlg._archive_btn["state"]) == "normal"

    def test_on_list_select_disables_buttons_when_no_selection(self, dlg):
        dlg._listbox.selection_clear(0, tk.END)
        dlg._on_list_select()
        assert str(dlg._edit_btn["state"]) == "disabled"

    def test_refresh_list_shows_color_coding(self, root_tk, storage):
        pm = ProjectManager(storage)
        pm.update(pm.active_project.project_id, pm.active_project.name, color="#FF0000")
        d = ProjectManagementDialog(root_tk, pm)
        assert d._listbox.itemcget(0, "foreground") == "#FF0000"
        d.close()

    def test_refresh_list_archived_shown_dim(self, root_tk, storage):
        pm = ProjectManager(storage)
        pm.add("Second", "")
        default = pm.projects[0]
        pm.set_archived(default.project_id, True)
        d = ProjectManagementDialog(root_tk, pm)
        d._show_archived_var.set(True)
        d._refresh_list()
        # archived item is always first (id=1), find its index
        vis = d._visible_projects()
        idx = next(i for i, p in enumerate(vis) if p.project_id == default.project_id)
        assert d._listbox.itemcget(idx, "foreground") == "#00AA00"  # _FG_DIM
        d.close()

    def test_double_click_project_toggles_collapse(self, root_tk, storage):
        pm = ProjectManager(storage)
        mgr = SubActivityManager(storage, pm.active_project.project_id)
        mgr.add("sub1")
        d = ProjectManagementDialog(root_tk, pm, storage=storage)
        assert len(d._list_rows) == 2
        d._listbox.selection_clear(0, tk.END)
        d._listbox.selection_set(0)
        d._on_tree_double_click()
        assert len(d._list_rows) == 1
        d._listbox.selection_clear(0, tk.END)
        d._listbox.selection_set(0)
        d._on_tree_double_click()
        assert len(d._list_rows) == 2
        d.close()

    def test_sub_edit_row_hidden_until_edit_clicked(self, root_tk, storage):
        pm = ProjectManager(storage)
        mgr = SubActivityManager(storage, pm.active_project.project_id)
        mgr.add("sub1")
        d = ProjectManagementDialog(root_tk, pm, storage=storage)
        assert d._sub_form_frame is not None
        assert not d._sub_form_frame.winfo_manager()
        d._listbox.selection_clear(0, tk.END)
        d._listbox.selection_set(1)  # sub row
        d._on_list_select()
        assert not d._sub_form_frame.winfo_manager()
        d._on_sa_edit()
        assert d._sub_form_frame.winfo_manager()
        assert d._sa_edit_name_var.get() == "sub1"
        d.close()

    def test_refresh_list_includes_live_segment_overlay(self, root_tk, storage):
        pm = ProjectManager(storage)
        project_id = pm.active_project.project_id
        today_text = date.today().isoformat()
        storage.add_daily_seconds(project_id, today_text, 120.0)
        mgr = SubActivityManager(storage, project_id)
        sa = mgr.add("Live Sub")
        mgr.save_elapsed(sa.sub_activity_id, 300.0)

        d = ProjectManagementDialog(
            root_tk,
            pm,
            storage=storage,
            active_sub_id_getter=lambda: sa.sub_activity_id,
            live_segment_getter=lambda: (project_id, 45.0),
        )
        d._refresh_list()

        project_row = d._listbox.get(0)
        sub_row = d._listbox.get(1)
        assert format_elapsed(165.0, pad_hours=False) in project_row
        assert format_elapsed(345.0, pad_hours=False) in sub_row
        d.close()


# ---------------------------------------------------------------------------
# Form open / close
# ---------------------------------------------------------------------------


class TestDialogFormOpenClose:
    def test_open_add_shows_form(self, dlg):
        dlg._open_add()
        dlg._form_frame.pack_info()  # should not raise - form is packed

    def test_open_add_clears_fields(self, dlg):
        dlg._name_var.set("Old")
        dlg._open_add()
        assert dlg._name_var.get() == ""
        assert dlg._alias_var.get() == ""

    def test_open_add_clears_notes(self, dlg):
        dlg._notes_text.insert("1.0", "old notes")
        dlg._open_add()
        assert dlg._notes_text.get("1.0", tk.END).strip() == ""

    def test_open_edit_no_selection_sets_status(self, dlg):
        dlg._listbox.selection_clear(0, tk.END)
        dlg._open_edit()
        assert dlg._status_var.get() != ""

    def test_open_edit_populates_fields(self, dlg, pm):
        pm.update(
            pm.active_project.project_id,
            "EditMe",
            "d",
            alias="al",
            ref_number="R1",
            color="#FF0000",
            notes="note",
        )
        dlg._refresh_list()
        dlg._listbox.selection_set(0)
        dlg._open_edit()
        assert dlg._name_var.get() == "EditMe"
        assert dlg._alias_var.get() == "al"
        assert dlg._ref_var.get() == "R1"
        assert dlg._color_var.get() == "#FF0000"
        assert dlg._notes_text.get("1.0", tk.END).strip() == "note"

    def test_cancel_hides_form(self, dlg):
        dlg._open_add()
        dlg._on_cancel()
        with pytest.raises(tk.TclError):
            dlg._form_frame.pack_info()

    def test_cancel_clears_mode(self, dlg):
        dlg._open_add()
        assert dlg._mode == "add"
        dlg._on_cancel()
        assert dlg._mode is None


# ---------------------------------------------------------------------------
# Save (add / edit)
# ---------------------------------------------------------------------------


class TestDialogSave:
    def test_save_add_creates_project(self, dlg, pm):
        initial = len(pm.projects)
        dlg._open_add()
        dlg._name_var.set("BrandNew")
        dlg._on_save()
        assert len(pm.projects) == initial + 1
        names = [p.name for p in pm.projects]
        assert "BrandNew" in names

    def test_save_add_empty_name_shows_error(self, dlg):
        dlg._open_add()
        dlg._name_var.set("   ")
        dlg._on_save()
        assert dlg._status_var.get() != ""
        assert dlg._mode == "add"  # stayed in add mode

    def test_save_add_duplicate_name_shows_error(self, dlg, pm):
        existing = pm.projects[0].name
        dlg._open_add()
        dlg._name_var.set(existing)
        dlg._on_save()
        assert dlg._status_var.get() != ""

    def test_save_edit_updates_project(self, dlg, pm):
        dlg._refresh_list()
        dlg._listbox.selection_set(0)
        dlg._open_edit()
        dlg._name_var.set("UpdatedName")
        dlg._on_save()
        names = [p.name for p in pm.projects]
        assert "UpdatedName" in names

    def test_save_with_no_mode_is_noop(self, dlg):
        dlg._mode = None
        dlg._on_save()  # should not raise

    def test_save_fires_callback(self, root_tk, storage):
        pm = ProjectManager(storage)
        called = []
        d = ProjectManagementDialog(
            root_tk, pm, on_projects_changed=lambda: called.append(1)
        )
        d._open_add()
        d._name_var.set("CB Test")
        d._on_save()
        assert len(called) == 1
        d.close()

    def test_save_add_with_metadata(self, dlg, pm):
        dlg._open_add()
        dlg._name_var.set("MetaProject")
        dlg._alias_var.set("mp")
        dlg._ref_var.set("R99")
        dlg._color_var.set("#0F0")
        dlg._notes_text.insert("1.0", "some notes")
        dlg._on_save()
        p = next(x for x in pm.projects if x.name == "MetaProject")
        assert p.alias == "mp"
        assert p.ref_number == "R99"
        assert p.color == "#0F0"
        assert p.notes == "some notes"


# ---------------------------------------------------------------------------
# Archive toggle
# ---------------------------------------------------------------------------


class TestDialogArchiveToggle:
    def test_archive_no_selection_sets_status(self, dlg):
        dlg._listbox.selection_clear(0, tk.END)
        dlg._on_archive_toggle()
        assert dlg._status_var.get() != ""

    def test_archive_archives_project(self, root_tk, storage):
        pm = ProjectManager(storage)
        pm.add("Second", "")
        d = ProjectManagementDialog(root_tk, pm)
        d._listbox.selection_set(0)
        project = d._visible_projects()[0]
        d._on_archive_toggle()
        assert project.archived is True
        d.close()

    def test_unarchive_unarchives_project(self, root_tk, storage):
        pm = ProjectManager(storage)
        pm.add("Second", "")
        default = pm.projects[0]
        pm.set_archived(default.project_id, True)
        d = ProjectManagementDialog(root_tk, pm)
        d._show_archived_var.set(True)
        d._refresh_list()
        # select the archived one
        vi = [p.project_id for p in d._visible_projects()].index(default.project_id)
        d._listbox.selection_set(vi)
        d._on_archive_toggle()
        assert default.archived is False
        d.close()

    def test_archive_fires_callback(self, root_tk, storage):
        pm = ProjectManager(storage)
        pm.add("Second", "")
        called = []
        d = ProjectManagementDialog(
            root_tk, pm, on_projects_changed=lambda: called.append(1)
        )
        d._listbox.selection_set(0)
        d._on_archive_toggle()
        assert len(called) == 1
        d.close()

    def test_archive_btn_text_shows_unarch_for_archived(self, root_tk, storage):
        pm = ProjectManager(storage)
        pm.add("Second", "")
        default = pm.projects[0]
        pm.set_archived(default.project_id, True)
        d = ProjectManagementDialog(root_tk, pm)
        d._show_archived_var.set(True)
        d._refresh_list()
        # Select the archived item
        vis = d._visible_projects()
        idx = next(i for i, p in enumerate(vis) if p.project_id == default.project_id)
        d._listbox.selection_set(idx)
        d._on_list_select()
        assert "Unarchive" in d._archive_btn["text"]
        d.close()


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDialogDelete:
    @staticmethod
    def _find_button_by_text(parent: tk.Misc, text: str) -> tk.Button | None:
        for child in parent.winfo_children():
            if isinstance(child, tk.Button) and child.cget("text") == text:
                return child
            found = TestDialogDelete._find_button_by_text(child, text)
            if found is not None:
                return found
        return None

    def test_delete_no_selection_sets_status(self, dlg):
        dlg._listbox.selection_clear(0, tk.END)
        dlg._confirm_delete()
        assert dlg._status_var.get() != ""

    def test_delete_last_active_project_blocked(self, dlg, pm):
        # Only one active project (Default) - deletion should be blocked
        count = sum(1 for p in pm.projects if not p.archived)
        if count <= 1:
            dlg._refresh_list()
            dlg._listbox.selection_set(0)
            dlg._confirm_delete()
            assert dlg._status_var.get() != ""

    def test_show_delete_confirm_cancel_closes_popup(self, root_tk, storage):
        pm = ProjectManager(storage)
        pm.add("Delete Candidate", "")
        d = ProjectManagementDialog(root_tk, pm)

        target = next(p for p in pm.projects if p.name == "Delete Candidate")
        before = [c for c in d._win.winfo_children() if isinstance(c, tk.Toplevel)]

        d._show_delete_confirm(target)
        d._win.update_idletasks()

        after = [c for c in d._win.winfo_children() if isinstance(c, tk.Toplevel)]
        assert len(after) == len(before) + 1
        popup = after[-1]
        cancel_btn = self._find_button_by_text(popup, "Cancel")
        assert cancel_btn is not None

        cancel_btn.invoke()
        d._win.update_idletasks()
        assert not popup.winfo_exists()
        d.close()

    def test_show_delete_confirm_delete_button_removes_project(self, root_tk, storage):
        pm = ProjectManager(storage)
        pm.add("Delete Via Popup", "")
        d = ProjectManagementDialog(root_tk, pm)

        target = next(p for p in pm.projects if p.name == "Delete Via Popup")
        d._show_delete_confirm(target)
        d._win.update_idletasks()

        popups = [c for c in d._win.winfo_children() if isinstance(c, tk.Toplevel)]
        assert popups
        delete_btn = self._find_button_by_text(popups[-1], "Delete")
        assert delete_btn is not None

        delete_btn.invoke()
        d._win.update_idletasks()
        assert not any(p.project_id == target.project_id for p in pm.projects)
        d.close()


# ---------------------------------------------------------------------------
# Color picker
# ---------------------------------------------------------------------------


class TestDialogColorPicker:
    def test_select_color_updates_var(self, dlg):
        dlg._select_color("#FF4444")
        assert dlg._color_var.get() == "#FF4444"

    def test_select_empty_color(self, dlg):
        dlg._select_color("")
        assert dlg._color_var.get() == ""

    def test_update_color_btns_highlights_selected(self, dlg):
        dlg._select_color("#FF4444")
        # Find the button for #FF4444
        from src.ui.dialogs.project_dialog import _COLOR_OPTIONS

        idx = _COLOR_OPTIONS.index("#FF4444")
        assert dlg._color_btns[idx]["relief"] == "solid"

    def test_update_color_btns_flat_for_unselected(self, dlg):
        dlg._select_color("#FF4444")
        from src.ui.dialogs.project_dialog import _COLOR_OPTIONS

        for i, col in enumerate(_COLOR_OPTIONS):
            if col != "#FF4444":
                assert dlg._color_btns[i]["relief"] == "flat"


# ---------------------------------------------------------------------------
# Dragging (smoke test - just verify no crash)
# ---------------------------------------------------------------------------


class TestDialogDragging:
    def test_drag_start_stores_coords(self, dlg):
        event = type("E", (), {"x_root": 100, "y_root": 200})()
        dlg._drag_start(event)
        assert dlg._drag_x == 100
        assert dlg._drag_y == 200

    def test_drag_motion_moves_window(self, dlg):
        event1 = type("E", (), {"x_root": 50, "y_root": 60})()
        dlg._drag_start(event1)
        event2 = type("E", (), {"x_root": 55, "y_root": 65})()
        dlg._drag_motion(event2)  # should not raise


# ---------------------------------------------------------------------------
# Close
# ---------------------------------------------------------------------------


class TestDialogClose:
    def test_close_destroys_window(self, root_tk, pm):
        d = ProjectManagementDialog(root_tk, pm)
        d.close()
        assert not d._win.winfo_exists()


class TestDialogSubActivityForm:
    def test_sa_add_sets_add_mode_and_shows_form(self, root_tk, storage):
        pm = ProjectManager(storage)
        d = ProjectManagementDialog(root_tk, pm, storage=storage)
        d._listbox.selection_set(0)  # project row
        d._on_sa_add()
        assert d._sub_form_mode == "add"
        assert d._sa_editing_project_id == pm.active_project.project_id
        assert d._sub_form_frame.winfo_manager()
        d.close()

    def test_sa_edit_save_add_creates_sub_activity(self, root_tk, storage):
        pm = ProjectManager(storage)
        d = ProjectManagementDialog(root_tk, pm, storage=storage)
        d._listbox.selection_set(0)  # project row
        d._on_sa_add()
        d._sa_edit_name_var.set("New Sub")
        d._on_sa_edit_save()
        rows = storage.list_sub_activities(pm.active_project.project_id)
        assert any(r["name"] == "New Sub" for r in rows)
        d.close()

    def test_sa_edit_save_edit_renames_sub_activity(self, root_tk, storage):
        pm = ProjectManager(storage)
        mgr = SubActivityManager(storage, pm.active_project.project_id)
        sa = mgr.add("Old Name")
        d = ProjectManagementDialog(root_tk, pm, storage=storage)
        d._listbox.selection_clear(0, tk.END)
        d._listbox.selection_set(1)  # first sub row
        d._on_sa_edit()
        d._sa_edit_name_var.set("Renamed")
        d._on_sa_edit_save()
        rows = storage.list_sub_activities(pm.active_project.project_id)
        assert any(
            r["id"] == sa.sub_activity_id and r["name"] == "Renamed" for r in rows
        )
        d.close()

    def test_archive_context_for_sub_activity(self, root_tk, storage):
        pm = ProjectManager(storage)
        mgr = SubActivityManager(storage, pm.active_project.project_id)
        sa = mgr.add("Archive Me")
        d = ProjectManagementDialog(root_tk, pm, storage=storage)
        d._listbox.selection_clear(0, tk.END)
        d._listbox.selection_set(1)
        d._on_archive_context()
        rows = storage.list_sub_activities(pm.active_project.project_id)
        row = next(r for r in rows if r["id"] == sa.sub_activity_id)
        assert row["archived"] is True
        d.close()

    def test_delete_context_for_sub_activity(self, root_tk, storage, monkeypatch):
        pm = ProjectManager(storage)
        mgr = SubActivityManager(storage, pm.active_project.project_id)
        sa = mgr.add("Delete Me")
        d = ProjectManagementDialog(root_tk, pm, storage=storage)
        d._listbox.selection_clear(0, tk.END)
        d._listbox.selection_set(1)
        monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *args, **kwargs: True)
        d._on_delete_context()
        rows = storage.list_sub_activities(pm.active_project.project_id)
        assert not any(r["id"] == sa.sub_activity_id for r in rows)
        d.close()

    def test_sub_activity_add_fires_callback(self, root_tk, storage):
        pm = ProjectManager(storage)
        called: list[int] = []
        d = ProjectManagementDialog(
            root_tk,
            pm,
            storage=storage,
            on_projects_changed=lambda: called.append(1),
        )
        d._listbox.selection_set(0)
        d._on_sa_add()
        d._sa_edit_name_var.set("Callback Sub")
        d._on_sa_edit_save()
        assert called
        d.close()

    def test_sub_activity_delete_fires_callback(self, root_tk, storage, monkeypatch):
        pm = ProjectManager(storage)
        mgr = SubActivityManager(storage, pm.active_project.project_id)
        mgr.add("Delete Callback")
        called: list[int] = []
        d = ProjectManagementDialog(
            root_tk,
            pm,
            storage=storage,
            on_projects_changed=lambda: called.append(1),
        )
        d._listbox.selection_clear(0, tk.END)
        d._listbox.selection_set(1)
        monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *args, **kwargs: True)
        d._on_delete_context()
        assert called
        d.close()
