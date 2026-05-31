"""Project management dialog for Tick-Tock Widget."""

import functools
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from typing import Any, Callable, Optional, cast

from src.app.services.project_dialog_service import ProjectDialogService
from src.projects import Project, ProjectManager
from src.storage import Storage
from src.ui.base_dialog import BaseDialog
from src.ui.formatting import format_elapsed
from src.ui.themes import MATRIX, Theme


def _fmt_hms(seconds: float) -> str:
    """Format seconds as H:MM:SS (no leading zero on hours)."""
    return format_elapsed(seconds, pad_hours=False)


def _underline_text(text: str) -> str:
    """Render an underline-like marker without per-item Listbox font support."""
    return "".join(f"{ch}\u0332" if ch != " " else " " for ch in text)


_W = 600
_H_COMPACT = 540
_H_FORM = 640
_AUTO_REFRESH_MS = 1000

# Predefined project colour palette (empty string = default matrix green)
_COLOR_OPTIONS = [
    "",
    "#FF4444",
    "#FF8844",
    "#FFDD44",
    "#44FF88",
    "#44DDFF",
    "#4488FF",
    "#CC44FF",
    "#FF44CC",
]


class ProjectManagementDialog(BaseDialog):
    """Borderless project dialog for add/edit/archive/delete operations."""

    def __init__(
        self,
        parent: tk.Tk,
        project_manager: ProjectManager,
        on_projects_changed: Optional[Callable[[], None]] = None,
        storage: Optional[Storage] = None,
        theme: Optional[Theme] = None,
        active_sub_id_getter: Optional[Callable[[], Optional[int]]] = None,
        live_segment_getter: Optional[Callable[[], tuple[Optional[int], float]]] = None,
        on_before_project_change: Optional[Callable[[int], bool]] = None,
        on_before_sub_activity_delete: Optional[Callable[[int, int], bool]] = None,
    ) -> None:
        self._parent = parent
        self._pm = project_manager
        self._callback = on_projects_changed
        self._svc = ProjectDialogService(storage)
        self._t: Theme = theme if theme is not None else MATRIX
        self._get_active_sub_id = active_sub_id_getter or (lambda: None)
        self._get_live_segment = live_segment_getter
        self._on_before_project_change = on_before_project_change
        self._on_before_sub_activity_delete = on_before_sub_activity_delete
        self._mode: Optional[str] = None  # None | "add" | "edit"
        self._edit_id: Optional[int] = None
        super().__init__(parent, theme=self._t)
        self._win.title("Manage Projects")
        self._win.update_idletasks()
        px = parent.winfo_x()
        py = parent.winfo_y()
        self._win.geometry(f"{_W}x{_H_COMPACT}+{px + 45}+{py + 15}")

        # Widget refs (populated in _build)
        self._listbox: Optional[tk.Listbox] = None
        self._list_rows: list[tuple[str, int, Optional[int]]] = []
        self._add_project_btn: Optional[tk.Button] = None
        self._add_activity_btn: Optional[tk.Button] = None
        self._edit_btn: Optional[tk.Button] = None
        self._del_btn: Optional[tk.Button] = None
        self._archive_btn: Optional[tk.Button] = None
        self._expanded_project_ids: set[int] = set()
        self._expansion_initialized = False
        self._form_frame: Optional[tk.Frame] = None
        self._status_label: Optional[tk.Label] = None
        self._status_var = tk.StringVar(value="")

        # Form field variables
        self._name_var = tk.StringVar()
        self._alias_var = tk.StringVar()
        self._ref_var = tk.StringVar()
        self._desc_var = tk.StringVar()
        self._color_var = tk.StringVar(value="")
        self._show_archived_var = tk.BooleanVar(value=False)

        # Entry / Text refs
        self._name_entry: Optional[tk.Entry] = None
        self._notes_text: Optional[tk.Text] = None

        # Color swatch buttons
        self._color_btns: list[tk.Button] = []

        # Shared inline editor for sub-activity add/edit (hidden by default)
        self._sub_form_frame: Optional[tk.Frame] = None
        self._sub_form_title_var = tk.StringVar(value="")
        self._sa_edit_name_var = tk.StringVar()
        self._sa_edit_name_entry: Optional[tk.Entry] = None
        self._sa_editing_sub_id: Optional[int] = None
        self._sa_editing_project_id: Optional[int] = None
        self._sub_form_mode: Optional[str] = None  # None | "add" | "edit"
        self._auto_refresh_job: Optional[str] = None

        self._build()
        self._schedule_auto_refresh()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # Shadow module-level constants with current theme values
        t = self._t
        bg = t.bg
        fg = t.fg
        fg_dim = t.fg_dim
        sep = t.sep
        btn_bg = t.btn_bg
        btn_fg = t.btn_fg
        btn_active = t.btn_active
        close_bg = t.close_bg
        close_fg = t.close_fg
        sel_bg = t.sel_bg
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Matrix.Vertical.TScrollbar",
            background=t.btn_bg,
            troughcolor=t.bg,
            bordercolor=t.fg_dim,
            darkcolor=t.btn_bg,
            lightcolor=t.btn_bg,
            arrowcolor=t.fg_dim,
        )
        style.map(
            "Matrix.Vertical.TScrollbar",
            background=[("active", t.sel_bg), ("pressed", t.sel_bg)],
            arrowcolor=[("active", t.fg), ("pressed", t.fg)],
        )

        win = self._win
        outer = tk.Frame(win, bg=bg, highlightbackground=fg_dim, highlightthickness=1)
        outer.pack(fill="both", expand=True, padx=3, pady=3)

        # ---- Title bar ------------------------------------------------
        title_bar = tk.Frame(outer, bg=bg, height=28)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        title_icon_lbl = tk.Label(
            title_bar,
            text="\U0001f4ca",
            bg=bg,
            fg=fg_dim,
            font=("Arial", 11, "bold"),
        )
        title_icon_lbl.pack(side="left", padx=(6, 2))
        title_lbl = tk.Label(
            title_bar,
            text="Project Management",
            bg=bg,
            fg=fg_dim,
            font=("Arial", 10, "bold"),
        )
        title_lbl.pack(side="left", padx=(0, 6))
        tk.Button(
            title_bar,
            text="\u2715",
            bg=close_bg,
            fg=close_fg,
            font=("Arial", 10, "bold"),
            bd=0,
            width=2,
            command=self.close,
        ).pack(side="right", padx=2, pady=2)
        title_bar.bind("<Button-1>", self._drag_start)
        title_bar.bind("<B1-Motion>", self._drag_motion)
        title_icon_lbl.bind("<Button-1>", self._drag_start)
        title_icon_lbl.bind("<B1-Motion>", self._drag_motion)
        title_lbl.bind("<Button-1>", self._drag_start)
        title_lbl.bind("<B1-Motion>", self._drag_motion)
        tk.Frame(outer, bg=sep, height=1).pack(fill="x")

        # ---- Show-archived toggle ------------------------------------
        toggle_row = tk.Frame(outer, bg=bg, height=24)
        toggle_row.pack(fill="x", padx=8, pady=(4, 0))
        toggle_row.pack_propagate(False)
        tk.Checkbutton(
            toggle_row,
            text="Show archived",
            variable=self._show_archived_var,
            bg=bg,
            fg=fg_dim,
            selectcolor=btn_bg,
            activebackground=bg,
            activeforeground=fg_dim,
            font=("Arial", 8),
            command=self._refresh_list,
        ).pack(side="left")

        # ---- Project list --------------------------------------------
        list_frame = tk.Frame(outer, bg=bg)
        list_frame.pack(fill="both", expand=True, padx=8, pady=(4, 4))
        tk.Label(
            list_frame,
            text="Projects & Sub-Activities:",
            bg=bg,
            fg=fg_dim,
            font=("Arial", 9, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 2))
        tk.Label(
            list_frame,
            text=f"{'Alias':<12} {'DZ #':<8} {'Full Name':<20} {'Total Today':>10}",
            bg=bg,
            fg=fg_dim,
            font=("Consolas", 9, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 2))
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", style="Matrix.Vertical.TScrollbar"
        )
        scrollbar.pack(side="right", fill="y")
        self._listbox = tk.Listbox(
            list_frame,
            bg=bg,
            fg=fg,
            selectbackground=sel_bg,
            selectforeground=fg,
            font=("Consolas", 9),
            bd=1,
            relief="solid",
            highlightbackground=fg_dim,
            highlightthickness=1,
            yscrollcommand=scrollbar.set,
            activestyle="none",
            exportselection=False,
        )
        self._listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self._listbox.yview)  # pyright: ignore
        self._listbox.bind("<<ListboxSelect>>", lambda _e: self._on_list_select())
        self._listbox.bind("<Double-Button-1>", lambda _e: self._on_tree_double_click())
        self._listbox.bind("<Return>", lambda _e: self._on_tree_double_click())

        # ---- Toolbar --------------------------------------------------
        tk.Frame(outer, bg=sep, height=1).pack(fill="x")
        toolbar = tk.Frame(outer, bg=bg, height=34)
        toolbar.pack(fill="x", padx=8, pady=4)
        toolbar.pack_propagate(False)

        def _btn(parent: tk.Frame, **kw: object) -> tk.Button:
            defaults: dict[str, Any] = dict(
                bg=btn_bg,
                fg=btn_fg,
                activebackground=btn_active,
                activeforeground=btn_fg,
                font=("Arial", 9, "bold"),
                bd=1,
                relief="raised",
            )
            defaults.update(kw)
            return tk.Button(parent, **defaults)

        self._add_project_btn = _btn(
            toolbar, text="+ Project", width=9, command=self._open_add
        )
        self._add_project_btn.pack(side="left", padx=2)
        self._add_activity_btn = _btn(
            toolbar, text="+ Activity", width=9, command=self._on_add_activity
        )
        self._add_activity_btn.pack(side="left", padx=2)
        self._edit_btn = _btn(
            toolbar,
            text="Edit",
            width=7,
            command=self._on_edit_context,
            state="disabled",
        )
        self._edit_btn.pack(side="left", padx=2)
        self._archive_btn = _btn(
            toolbar,
            text="Archive",
            width=8,
            command=self._on_archive_context,
            state="disabled",
        )
        self._archive_btn.pack(side="left", padx=2)
        self._del_btn = _btn(
            toolbar,
            text="Delete",
            width=7,
            fg=t.stop_fg,
            activebackground=t.stop_active,
            activeforeground=t.stop_fg,
            command=self._on_delete_context,
            state="disabled",
        )
        self._del_btn.pack(side="left", padx=2)

        # ---- Inline form (hidden initially) ---------------------------
        tk.Frame(outer, bg=sep, height=1).pack(fill="x")
        self._form_frame = tk.Frame(outer, bg=bg)
        # Not packed yet — shown via _show_form()
        self._build_form()

        # ---- Inline sub-activity edit/add form (hidden initially) ----------
        self._sub_form_frame = tk.Frame(outer, bg=bg)
        self._build_sub_form()

        # ---- Status line ----------------------------------------------
        self._status_label = tk.Label(
            outer,
            textvariable=self._status_var,
            bg=bg,
            fg=t.stop_fg,
            font=("Arial", 8),
        )
        self._status_label.pack(side="bottom", pady=(0, 3))

        self._refresh_list()

    def _build_form(self) -> None:
        # Shadow module-level constants with current theme values
        t = self._t
        bg = t.bg
        fg = t.fg
        fg_dim = t.fg_dim
        btn_bg = t.btn_bg
        btn_fg = t.btn_fg
        btn_active = t.btn_active
        entry_bg = t.entry_bg

        assert self._form_frame is not None
        f = self._form_frame
        entry_kw: dict[str, Any] = dict(
            bg=entry_bg,
            fg=fg,
            insertbackground=fg,
            font=("Consolas", 9),
            bd=1,
            relief="solid",
            highlightbackground=fg_dim,
            highlightthickness=1,
        )

        def _lbl(parent: tk.Frame, text: str) -> tk.Label:
            return tk.Label(
                parent,
                text=text,
                bg=bg,
                fg=fg_dim,
                font=("Arial", 9),
                width=6,
                anchor="w",
            )

        # Name
        row_name = tk.Frame(f, bg=bg)
        row_name.pack(fill="x", padx=8, pady=(8, 2))
        _lbl(row_name, "Name:").pack(side="left")
        self._name_entry = tk.Entry(row_name, textvariable=self._name_var, **entry_kw)
        self._name_entry.pack(side="left", fill="x", expand=True)
        self._name_entry.bind("<Return>", lambda _e: self._on_save())

        # Alias
        row_alias = tk.Frame(f, bg=bg)
        row_alias.pack(fill="x", padx=8, pady=2)
        _lbl(row_alias, "Alias:").pack(side="left")
        alias_entry = tk.Entry(row_alias, textvariable=self._alias_var, **entry_kw)
        alias_entry.pack(side="left", fill="x", expand=True)
        alias_entry.bind("<Return>", lambda _e: self._on_save())

        # Ref #
        row_ref = tk.Frame(f, bg=bg)
        row_ref.pack(fill="x", padx=8, pady=2)
        _lbl(row_ref, "Ref #:").pack(side="left")
        ref_entry = tk.Entry(row_ref, textvariable=self._ref_var, **entry_kw)
        ref_entry.pack(side="left", fill="x", expand=True)
        ref_entry.bind("<Return>", lambda _e: self._on_save())

        # Color picker
        row_color = tk.Frame(f, bg=bg)
        row_color.pack(fill="x", padx=8, pady=2)
        _lbl(row_color, "Color:").pack(side="left")
        self._color_btns = []
        for col in _COLOR_OPTIONS:
            display_fg = col if col else fg_dim
            btn = tk.Button(
                row_color,
                text="\u25cf",
                bg=bg,
                fg=display_fg,
                activebackground=bg,
                activeforeground=display_fg,
                font=("Arial", 13),
                bd=2,
                relief="flat",
                width=1,
                command=functools.partial(self._select_color, col),
            )
            btn.pack(side="left", padx=1)
            self._color_btns.append(btn)

        # Description
        row_desc = tk.Frame(f, bg=bg)
        row_desc.pack(fill="x", padx=8, pady=2)
        _lbl(row_desc, "Desc:").pack(side="left")
        desc_entry = tk.Entry(row_desc, textvariable=self._desc_var, **entry_kw)
        desc_entry.pack(side="left", fill="x", expand=True)
        desc_entry.bind("<Return>", lambda _e: self._on_save())

        # Notes (multi-line)
        row_notes = tk.Frame(f, bg=bg)
        row_notes.pack(fill="x", padx=8, pady=2)
        _lbl(row_notes, "Notes:").pack(side="left", anchor="n")
        self._notes_text = tk.Text(
            row_notes,
            bg=entry_bg,
            fg=fg,
            insertbackground=fg,
            font=("Consolas", 9),
            bd=1,
            relief="solid",
            highlightbackground=fg_dim,
            highlightthickness=1,
            height=2,
            wrap="word",
        )
        self._notes_text.pack(side="left", fill="x", expand=True)

        # Save / Cancel buttons
        btn_row = tk.Frame(f, bg=bg)
        btn_row.pack(pady=(6, 8))
        tf: dict[str, Any] = dict(font=("Arial", 9, "bold"), bd=1, relief="raised")
        tk.Button(
            btn_row,
            text="Save",
            bg=btn_bg,
            fg=btn_fg,
            activebackground=btn_active,
            activeforeground=btn_fg,
            width=7,
            command=self._on_save,
            **tf,
        ).pack(side="left", padx=4)
        tk.Button(
            btn_row,
            text="Cancel",
            bg=t.stop_active,
            fg=t.stop_fg,
            activebackground=t.close_bg,
            activeforeground=t.stop_fg,
            width=7,
            command=self._on_cancel,
            **tf,
        ).pack(side="left", padx=4)

    # ------------------------------------------------------------------
    # Color picker helpers
    # ------------------------------------------------------------------

    def _select_color(self, color: str) -> None:
        self._color_var.set(color)
        self._update_color_btns()

    def _update_color_btns(self) -> None:
        selected = self._color_var.get()
        for btn, col in zip(self._color_btns, _COLOR_OPTIONS):
            btn.config(relief="solid" if col == selected else "flat")

    # ------------------------------------------------------------------
    # Sub-activities section
    # ------------------------------------------------------------------

    def _build_sub_form(self) -> None:
        """Build hidden inline form used for sub-activity add/edit."""
        t = self._t
        assert self._sub_form_frame is not None
        f = self._sub_form_frame
        tk.Frame(f, bg=t.sep, height=1).pack(fill="x")

        row = tk.Frame(f, bg=t.bg)
        row.pack(fill="x", padx=8, pady=(4, 4))
        tk.Label(
            row,
            textvariable=self._sub_form_title_var,
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 9, "bold"),
            width=10,
            anchor="w",
        ).pack(side="left")
        self._sa_edit_name_entry = tk.Entry(
            row,
            textvariable=self._sa_edit_name_var,
            bg=t.entry_bg,
            fg=t.fg,
            insertbackground=t.fg,
            font=("Consolas", 9),
            bd=1,
            relief="solid",
            highlightbackground=t.fg_dim,
            highlightthickness=1,
        )
        self._sa_edit_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 2))
        self._sa_edit_name_entry.bind("<Return>", lambda _e: self._on_sa_edit_save())
        tk.Button(
            row,
            text="Save",
            bg=t.btn_bg,
            fg=t.btn_fg,
            activebackground=t.btn_active,
            activeforeground=t.btn_fg,
            font=("Arial", 8, "bold"),
            bd=1,
            relief="raised",
            width=6,
            command=self._on_sa_edit_save,
        ).pack(side="left", padx=2)
        tk.Button(
            row,
            text="Cancel",
            bg=t.stop_active,
            fg=t.stop_fg,
            activebackground=t.close_bg,
            activeforeground=t.stop_fg,
            font=("Arial", 8, "bold"),
            bd=1,
            relief="raised",
            width=7,
            command=self._on_sa_edit_cancel,
        ).pack(side="left", padx=2)

    def _selected_sub_activity(self) -> Optional[dict[str, Any]]:
        """Return the selected sub-activity row dict, or None."""
        if self._listbox is None or not self._svc.available:
            return None
        sel = cast(tuple[int, ...], self._listbox.curselection())  # pyright: ignore
        if not sel:
            return None
        idx = sel[0]
        if idx >= len(self._list_rows):
            return None
        kind, project_id, sub_id = self._list_rows[idx]
        if kind != "sub" or sub_id is None:
            return None
        rows = self._svc.list_sub_activities(project_id)
        return next((row for row in rows if row["id"] == sub_id), None)

    def _on_sa_add(self) -> None:
        """Enter add-sub-activity mode for the selected project context."""
        if not self._svc.available:
            return
        row = self._selected_row_meta()
        if row is None:
            self._status_var.set("Select a project first")
            return
        _kind, project_id, _sub_id = row
        self._sub_form_mode = "add"
        self._sa_editing_project_id = project_id
        self._sa_editing_sub_id = None
        self._sa_edit_name_var.set("")
        self._sub_form_title_var.set("Add Activity:")
        self._show_sub_form()
        self._status_var.set("")

    def _on_sa_delete(self) -> None:
        """Delete the selected sub-activity after confirmation."""
        if not self._svc.available:
            return
        row = self._selected_sub_activity()
        if row is None:
            return
        p = self._selected_project()
        if p is None:
            return
        confirmed = messagebox.askyesno(
            "Delete Sub-activity",
            f"Delete sub-activity \"{row['name']}\"?\nThis removes all its time data.",
            parent=self._win,
        )
        if not confirmed:
            return
        if self._on_before_sub_activity_delete is not None:
            can_delete = self._on_before_sub_activity_delete(
                p.project_id,
                int(row["id"]),
            )
            if not can_delete:
                self._status_var.set(
                    "Could not prepare timer state for sub-activity deletion"
                )
                return
        try:
            self._svc.delete_sub_activity(int(row["id"]))
        except Exception as exc:  # pylint: disable=broad-except
            self._status_var.set(str(exc))
            return
        self._status_var.set("")
        if row["id"] == self._sa_editing_sub_id:
            self._on_sa_edit_cancel()
        self._refresh_list()
        if self._callback:
            self._callback()

    def _on_sa_edit(self) -> None:
        """Open inline edit controls for the selected sub-activity."""
        if not self._svc.available:
            return
        row = self._selected_sub_activity()
        if row is None:
            self._status_var.set("Select a sub-activity first")
            return
        p = self._selected_project()
        if p is None:
            self._status_var.set("Select a project first")
            return
        self._sub_form_mode = "edit"
        self._sa_editing_sub_id = int(row["id"])
        self._sa_editing_project_id = p.project_id
        self._sa_edit_name_var.set(str(row["name"]))
        self._sub_form_title_var.set("Edit Activity:")
        self._show_sub_form()
        if self._sa_edit_name_entry is not None:
            self._sa_edit_name_entry.focus_set()
            self._sa_edit_name_entry.selection_range(0, tk.END)
        self._status_var.set("")

    def _on_sa_edit_cancel(self) -> None:
        """Exit inline sub-activity edit mode."""
        self._sub_form_mode = None
        self._sa_editing_sub_id = None
        self._sa_editing_project_id = None
        self._sa_edit_name_var.set("")
        self._sub_form_title_var.set("")
        self._hide_sub_form()

    def _on_sa_edit_save(self) -> None:
        """Save inline sub-activity add/edit from the shared contextual form."""
        if not self._svc.available:
            return
        if self._sub_form_mode not in {"add", "edit"}:
            self._status_var.set("Click Add/Edit on an activity first")
            return
        if self._sa_editing_project_id is None:
            self._status_var.set("Select a project first")
            return
        new_name = self._sa_edit_name_var.get().strip()
        if not new_name:
            self._status_var.set("Sub-activity name cannot be empty")
            return
        if self._sub_form_mode == "add":
            try:
                self._svc.add_sub_activity(self._sa_editing_project_id, new_name)
            except ValueError as exc:
                self._status_var.set(str(exc))
                return
            self._status_var.set("")
            self._on_sa_edit_cancel()
            self._refresh_list()
            if self._callback:
                self._callback()
            return

        if self._sa_editing_sub_id is None:
            self._status_var.set("Click Edit on an activity first")
            return
        rows = self._svc.list_sub_activities(self._sa_editing_project_id)
        row = next((x for x in rows if int(x["id"]) == self._sa_editing_sub_id), None)
        if row is None:
            self._status_var.set("Selected sub-activity is no longer available")
            self._on_sa_edit_cancel()
            self._refresh_list()
            return
        if new_name == row["name"]:
            self._status_var.set("")
            self._on_sa_edit_cancel()
            return
        try:
            self._svc.update_sub_activity(
                self._sa_editing_project_id,
                int(row["id"]),
                new_name,
                str(row["description"]),
            )
        except ValueError as exc:
            self._status_var.set(str(exc))
            return
        self._status_var.set("")
        self._on_sa_edit_cancel()
        self._refresh_list()
        if self._callback:
            self._callback()

    def _show_sub_form(self) -> None:
        assert (
            self._sub_form_frame is not None
            and self._status_label is not None
            and self._form_frame is not None
        )
        self._form_frame.pack_forget()
        self._sub_form_frame.pack(fill="x", before=self._status_label)

    def _hide_sub_form(self) -> None:
        assert self._sub_form_frame is not None
        self._sub_form_frame.pack_forget()

    # ------------------------------------------------------------------
    # List helpers
    # ------------------------------------------------------------------

    def _visible_projects(self) -> list[Project]:
        show_arch = self._show_archived_var.get()
        return [p for p in self._pm.projects if show_arch or not p.archived]

    def _selected_row_meta(self) -> Optional[tuple[str, int, Optional[int]]]:
        """Return selected row metadata tuple from ``_list_rows``."""
        if self._listbox is None:
            return None
        sel = cast(tuple[int, ...], self._listbox.curselection())  # pyright: ignore
        if sel:
            idx = int(sel[0])
        else:
            try:
                idx = int(self._listbox.index("active"))
            except Exception:  # pylint: disable=broad-except
                return None
        if idx < 0 or idx >= len(self._list_rows):
            return None
        return self._list_rows[idx]

    def _toggle_project_expand(self, project_id: int) -> None:
        """Expand/collapse one project row in the mixed list."""
        if project_id in self._expanded_project_ids:
            self._expanded_project_ids.remove(project_id)
        else:
            self._expanded_project_ids.add(project_id)

    def _restore_selection(
        self,
        key: Optional[tuple[str, int, Optional[int]]],
        active_project_id: Optional[int],
    ) -> None:
        """Restore prior selection after list rebuild."""
        assert self._listbox is not None
        target_idx: Optional[int] = None
        if key is not None:
            for i, row in enumerate(self._list_rows):
                if row == key:
                    target_idx = i
                    break
        if target_idx is None and active_project_id is not None:
            for i, row in enumerate(self._list_rows):
                if row[0] == "project" and row[1] == active_project_id:
                    target_idx = i
                    break
        if target_idx is None and self._list_rows:
            target_idx = 0
        self._listbox.selection_clear(0, tk.END)
        if target_idx is not None:
            self._listbox.selection_set(target_idx)
            self._listbox.activate(target_idx)

    def _refresh_list(self) -> None:
        assert self._listbox is not None
        selected_key = self._selected_row_meta()
        self._listbox.delete(0, tk.END)
        self._list_rows = []
        active = self._pm.active_project
        active_sub_id = self._get_active_sub_id()
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self._svc.get_daily_seconds_by_project(today)
        live_project_id: Optional[int] = None
        live_delta = 0.0
        if self._get_live_segment is not None:
            live_project_id, live_delta = self._get_live_segment()
            live_delta = max(0.0, float(live_delta))
        show_arch = self._show_archived_var.get()
        visible_projects = self._visible_projects()
        visible_ids = {p.project_id for p in visible_projects}
        if not self._expansion_initialized:
            self._expanded_project_ids = set(visible_ids)
            self._expansion_initialized = True
        else:
            self._expanded_project_ids &= visible_ids

        for p in visible_projects:
            today_secs = daily.get(p.project_id, 0.0)
            if live_project_id == p.project_id:
                today_secs += live_delta
            alias_disp = (p.alias if p.alias else p.name)[:12]
            ref_disp = p.ref_number[:8] if p.ref_number else ""
            name_disp = p.name[:20]
            time_disp = _fmt_hms(today_secs) if self._svc.available else ""
            is_expanded = p.project_id in self._expanded_project_ids
            marker = "\u25be" if is_expanded else "\u25b8"
            if active is not None and active.project_id == p.project_id:
                alias_disp = _underline_text(alias_disp)
            self._listbox.insert(
                tk.END,
                (
                    f"{marker} {alias_disp:<12} {ref_disp:<8} "
                    f"{name_disp:<20} {time_disp:>10}"
                ),
            )
            idx = self._listbox.size() - 1
            self._list_rows.append(("project", p.project_id, None))
            if p.archived:
                item_fg = self._t.fg_dim
            elif p.color:
                item_fg = p.color
            else:
                item_fg = self._t.fg
            self._listbox.itemconfig(idx, fg=item_fg)  # pyright: ignore

            if not self._svc.available or not is_expanded:
                continue
            sub_today_map = self._svc.get_daily_seconds_by_sub_activity(
                today, p.project_id
            )
            for row in self._svc.list_sub_activities(p.project_id):
                if row["archived"] and not show_arch:
                    continue
                sa_name = row["name"][:20]
                sa_elapsed = float(sub_today_map.get(int(row["id"]), 0.0))
                if (
                    live_project_id == p.project_id
                    and active_sub_id is not None
                    and int(row["id"]) == active_sub_id
                ):
                    sa_elapsed += live_delta
                sa_time = _fmt_hms(sa_elapsed)
                sa_name_disp = (
                    _underline_text(sa_name)
                    if active_sub_id is not None and row["id"] == active_sub_id
                    else sa_name
                )
                self._listbox.insert(
                    tk.END,
                    f"  - {sa_name_disp:<12} {'':<8} {'':<20} {sa_time:>10}",
                )
                sa_idx = self._listbox.size() - 1
                self._list_rows.append(("sub", p.project_id, int(row["id"])))
                sa_fg = self._t.fg_dim if row["archived"] else self._t.fg
                self._listbox.itemconfig(sa_idx, fg=sa_fg)  # pyright: ignore

        self._restore_selection(selected_key, active.project_id if active else None)
        self._on_list_select()

    def _schedule_auto_refresh(self) -> None:
        if self._auto_refresh_job is None:
            self._auto_refresh_job = self._win.after(
                _AUTO_REFRESH_MS,
                self._on_auto_refresh_tick,
            )

    def _on_auto_refresh_tick(self) -> None:
        self._auto_refresh_job = None
        if not self._win.winfo_exists():
            return
        try:
            self._refresh_list()
        except tk.TclError:
            return
        self._schedule_auto_refresh()

    def _selected_project(self) -> Optional[Project]:
        assert self._listbox is not None
        sel = cast(tuple[int, ...], self._listbox.curselection())  # pyright: ignore
        if not sel:
            return None
        idx = sel[0]
        if idx >= len(self._list_rows):
            return None
        _kind, project_id, _sub_id = self._list_rows[idx]
        return next((p for p in self._pm.projects if p.project_id == project_id), None)

    def _on_list_select(self) -> None:
        row_meta: Optional[tuple[str, int, Optional[int]]] = None
        if self._listbox is not None:
            raw = self._listbox.curselection()  # pyright: ignore
            sel = cast(tuple[int, ...], raw)
            if sel and 0 <= sel[0] < len(self._list_rows):
                row_meta = self._list_rows[sel[0]]
        if self._edit_btn:
            self._edit_btn.config(
                state="normal" if row_meta is not None else "disabled"
            )
        if self._archive_btn:
            if row_meta is None:
                self._archive_btn.config(state="disabled", text="Archive")
            elif row_meta[0] == "project":
                p = self._selected_project()
                is_archived = p.archived if p else False
                self._archive_btn.config(
                    state="normal", text="Unarchive" if is_archived else "Archive"
                )
            else:
                row = self._selected_sub_activity()
                is_archived = bool(row["archived"]) if row is not None else False
                self._archive_btn.config(
                    state="normal", text="Unarchive" if is_archived else "Archive"
                )
        if self._del_btn:
            self._del_btn.config(state="normal" if row_meta is not None else "disabled")
        if row_meta is None:
            self._on_sa_edit_cancel()
        elif row_meta[0] == "sub" and self._sa_editing_sub_id is not None:
            if row_meta[2] != self._sa_editing_sub_id:
                self._on_sa_edit_cancel()
        elif row_meta[0] == "project" and self._sa_editing_sub_id is not None:
            self._on_sa_edit_cancel()

    def _on_tree_double_click(self) -> None:
        """Toggle project collapse on double-click for predictable UX."""
        row = self._selected_row_meta()
        if row is None:
            return
        kind, project_id, _sub_id = row
        if kind == "project":
            self._toggle_project_expand(project_id)
            self._refresh_list()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_add_activity(self) -> None:
        """Add an activity for selected project/sub-activity context."""
        row = self._selected_row_meta()
        if row is None:
            self._status_var.set("Select a project first")
            return
        self._on_sa_add()

    def _on_edit_context(self) -> None:
        """Edit action follows current selection context."""
        row = self._selected_row_meta()
        if row is None:
            self._status_var.set("Select a row to edit")
            return
        kind, _project_id, _sub_id = row
        if kind == "project":
            self._open_edit()
            return
        self._on_sa_edit()

    def _on_archive_context(self) -> None:
        """Archive action follows current selection context."""
        row = self._selected_row_meta()
        if row is None:
            self._status_var.set("Select a row to archive/unarchive")
            return
        kind, project_id, sub_id = row
        if kind == "project":
            self._on_archive_toggle()
            return
        if not self._svc.available or sub_id is None:
            return
        target = self._selected_sub_activity()
        is_archived = bool(target["archived"]) if target is not None else False
        self._svc.set_sub_activity_archived(project_id, sub_id, not is_archived)
        self._status_var.set("")
        self._refresh_list()
        if self._callback:
            self._callback()

    def _on_delete_context(self) -> None:
        """Delete action follows current selection context."""
        row = self._selected_row_meta()
        if row is None:
            self._status_var.set("Select a row to delete")
            return
        if row[0] == "project":
            self._confirm_delete()
            return
        self._on_sa_delete()

    def _open_add(self) -> None:
        self._mode = "add"
        self._edit_id = None
        self._name_var.set("")
        self._alias_var.set("")
        self._ref_var.set("")
        self._desc_var.set("")
        self._color_var.set("")
        if self._notes_text:
            self._notes_text.delete("1.0", tk.END)
        self._update_color_btns()
        self._status_var.set("")
        self._show_form()
        if self._name_entry:
            self._name_entry.focus_set()

    def _open_edit(self) -> None:
        p = self._selected_project()
        if p is None:
            self._status_var.set("Select a project to edit")
            return
        self._mode = "edit"
        self._edit_id = p.project_id
        self._name_var.set(p.name)
        self._alias_var.set(p.alias)
        self._ref_var.set(p.ref_number)
        self._desc_var.set(p.description)
        self._color_var.set(p.color)
        if self._notes_text:
            self._notes_text.delete("1.0", tk.END)
            self._notes_text.insert("1.0", p.notes)
        self._update_color_btns()
        self._status_var.set("")
        self._show_form()
        if self._name_entry:
            self._name_entry.focus_set()

    def _on_archive_toggle(self) -> None:
        p = self._selected_project()
        if p is None:
            self._status_var.set("Select a project to archive/unarchive")
            return
        if not p.archived and self._on_before_project_change is not None:
            can_archive = self._on_before_project_change(p.project_id)
            if not can_archive:
                self._status_var.set("Could not prepare timer state for archive")
                return
        try:
            self._pm.set_archived(p.project_id, not p.archived)
        except ValueError as exc:
            self._status_var.set(str(exc))
            return
        self._status_var.set("")
        self._refresh_list()
        self._on_list_select()
        if self._callback:
            self._callback()

    def _confirm_delete(self) -> None:
        p = self._selected_project()
        if p is None:
            self._status_var.set("Select a project to delete")
            return
        active_count = sum(1 for x in self._pm.projects if not x.archived)
        if active_count <= 1 and not p.archived:
            self._status_var.set("Cannot delete the last active project")
            return
        self._status_var.set("")
        self._show_delete_confirm(p)

    def _show_delete_confirm(self, project: Project) -> None:
        t = self._t
        dlg = tk.Toplevel(self._win)
        dlg.title("")
        dlg.configure(bg=t.bg)
        dlg.overrideredirect(True)
        dlg.attributes("-topmost", True)  # pyright: ignore
        wx = self._win.winfo_x() + 50
        wy = self._win.winfo_y() + 110
        dlg.geometry(f"270x84+{wx}+{wy}")

        outer = tk.Frame(
            dlg, bg=t.bg, highlightbackground=t.fg_dim, highlightthickness=1
        )
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        name_disp = project.name[:28] + ("\u2026" if len(project.name) > 28 else "")
        tk.Label(
            outer,
            text=f'Delete "{name_disp}"?',
            bg=t.bg,
            fg=t.fg,
            font=("Arial", 10),
        ).pack(pady=(12, 6))

        btn_f = tk.Frame(outer, bg=t.bg)
        btn_f.pack()

        def do_delete() -> None:
            dlg.destroy()
            if self._on_before_project_change is not None:
                can_delete = self._on_before_project_change(project.project_id)
                if not can_delete:
                    self._status_var.set("Could not prepare timer state for deletion")
                    return
            try:
                self._pm.delete(project.project_id)
            except ValueError as exc:
                self._status_var.set(str(exc))
                return
            self._refresh_list()
            self._on_list_select()
            if self._callback:
                self._callback()

        tk.Button(
            btn_f,
            text="Delete",
            bg=t.stop_active,
            fg=t.stop_fg,
            activebackground=t.close_bg,
            activeforeground=t.stop_fg,
            font=("Arial", 9, "bold"),
            width=7,
            bd=1,
            command=do_delete,
        ).pack(side="left", padx=4)
        tk.Button(
            btn_f,
            text="Cancel",
            bg=t.btn_bg,
            fg=t.btn_fg,
            activebackground=t.btn_active,
            activeforeground=t.btn_fg,
            font=("Arial", 9, "bold"),
            width=7,
            bd=1,
            command=dlg.destroy,
        ).pack(side="left", padx=4)
        dlg.grab_set()

    def _on_save(self) -> None:
        name = self._name_var.get()
        description = self._desc_var.get()
        alias = self._alias_var.get()
        ref_number = self._ref_var.get()
        color = self._color_var.get()
        notes = (
            self._notes_text.get("1.0", tk.END).rstrip("\n") if self._notes_text else ""
        )
        try:
            if self._mode == "add":
                self._pm.add(
                    name,
                    description,
                    alias=alias,
                    ref_number=ref_number,
                    color=color,
                    notes=notes,
                )
            elif self._mode == "edit" and self._edit_id is not None:
                self._pm.update(
                    self._edit_id,
                    name,
                    description,
                    alias=alias,
                    ref_number=ref_number,
                    color=color,
                    notes=notes,
                )
            else:
                return
        except ValueError as exc:
            self._status_var.set(str(exc))
            return
        self._status_var.set("")
        self._mode = None
        self._edit_id = None
        self._hide_form()
        self._refresh_list()
        if self._callback:
            self._callback()

    def _on_cancel(self) -> None:
        self._mode = None
        self._edit_id = None
        self._status_var.set("")
        self._hide_form()

    # ------------------------------------------------------------------
    # Form show/hide
    # ------------------------------------------------------------------

    def _show_form(self) -> None:
        assert self._form_frame is not None and self._status_label is not None
        self._on_sa_edit_cancel()
        self._form_frame.pack(fill="x", before=self._status_label)
        x, y = self._win.winfo_x(), self._win.winfo_y()
        self._win.geometry(f"{_W}x{_H_FORM}+{x}+{y}")

    def _hide_form(self) -> None:
        assert self._form_frame is not None
        self._form_frame.pack_forget()
        x, y = self._win.winfo_x(), self._win.winfo_y()
        self._win.geometry(f"{_W}x{_H_COMPACT}+{x}+{y}")

    def close(self) -> None:
        """Cancel timers and destroy the dialog window."""
        if self._auto_refresh_job is not None:
            try:
                self._win.after_cancel(self._auto_refresh_job)
            except tk.TclError:
                pass
            self._auto_refresh_job = None
        self._win.destroy()
