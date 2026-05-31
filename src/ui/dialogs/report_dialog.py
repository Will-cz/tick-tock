"""Monthly and weekly report dialog for Tick-Tock Widget."""

import calendar
import csv
import logging
import threading
import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import date, datetime, timedelta
from functools import partial
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Optional, cast

from src.projects import ProjectManager
from src.storage import Storage
from src.ui.base_dialog import BaseDialog
from src.ui.dialogs.report_payload import compute_refresh_payload
from src.ui.themes import Theme

_MONTHLY_MIN_W = 1100
_WEEKLY_MIN_W = 900
_DIALOG_H = 560
_AUTO_REFRESH_MS = 1000
RowData = dict[str, object]
logger = logging.getLogger(__name__)


def _fmt(seconds: float) -> str:
    """Format *seconds* as ``H:MM``; hide sub-minute values."""
    if seconds < 60:
        return ""
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    return f"{h}:{m:02d}"


def _fmt_total(seconds: float) -> str:
    """Format *seconds* as ``H:MM`` with a leading clock icon."""
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    return f"\u23f0 {h}:{m:02d}"


def _to_float(value: object) -> float:
    """Best-effort conversion to float for mixed-typed row dictionaries."""
    if not isinstance(value, (int, float, str, bytes, bytearray)):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class ReportDialog(BaseDialog):
    """Borderless monthly/weekly time-tracking report window."""

    def __init__(
        self,
        parent: tk.Tk,
        storage: Storage,
        project_mgr: ProjectManager,
        theme: Theme,
        live_project_id: Optional[int] = None,
        live_delta: float = 0.0,
        live_segment_getter: Optional[Callable[[], tuple[Optional[int], float]]] = None,
        active_sub_id_getter: Optional[Callable[[], Optional[int]]] = None,
    ) -> None:
        self._parent = parent
        self._storage = storage
        self._project_mgr = project_mgr
        self._theme = theme
        self._live_project_id = live_project_id
        self._live_delta = live_delta
        self._live_segment_getter = live_segment_getter
        self._active_sub_id_getter = active_sub_id_getter

        self._year = datetime.now().year
        self._month = datetime.now().month
        today = date.today()
        self._week_start: date = today - timedelta(days=today.weekday())
        self._view_mode = "monthly"
        self._filter_project_id: Optional[int] = None
        self._closed = False
        self._last_export_dir = str(Path.home())

        self._sort_column = "total"
        self._sort_desc = True

        self._tree: Optional[ttk.Treeview] = None
        self._title_icon_lbl: Optional[tk.Label] = None
        self._year_var: Optional[tk.StringVar] = None
        self._month_var: Optional[tk.StringVar] = None
        self._title_lbl: Optional[tk.Label] = None
        self._monthly_ctrl: Optional[tk.Frame] = None
        self._weekly_ctrl: Optional[tk.Frame] = None
        self._preset_frame: Optional[tk.Frame] = None
        self._week_lbl: Optional[tk.Label] = None
        self._week_year_var: Optional[tk.StringVar] = None
        self._week_num_var: Optional[tk.StringVar] = None
        self._week_combo: Optional[ttk.Combobox] = None
        self._filter_var: Optional[tk.StringVar] = None
        self._filter_combo: Optional[ttk.Combobox] = None
        self._mode_btn_monthly: Optional[tk.Button] = None
        self._mode_btn_weekly: Optional[tk.Button] = None
        self._show_non_zero_var: Optional[tk.BooleanVar] = None
        self._projects_only_var: Optional[tk.BooleanVar] = None
        self._summary_var: Optional[tk.StringVar] = None
        self._totals_by_column: dict[str, float] = {}
        self._shown_rows_count = 0
        self._pending_resize_job: Optional[str] = None
        self._last_window_size: Optional[tuple[int, int]] = None
        self._refresh_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="report-refresh"
        )
        self._refresh_future: Optional[Future[Any]] = None
        self._refresh_seq = 0
        self._refresh_future_seq = 0
        self._refresh_poll_job: Optional[str] = None
        self._auto_refresh_job: Optional[str] = None
        self._refresh_lock = threading.Lock()

        super().__init__(parent, theme=theme)
        self._setup_window()
        self._configure_styles()
        self._build_ui()
        self._refresh()
        self._schedule_auto_refresh()

        self._win.protocol("WM_DELETE_WINDOW", self._close)

    def _resolve_live_segment(self) -> tuple[Optional[int], Optional[int], float]:
        if self._live_segment_getter is None:
            project_id = self._live_project_id
            delta = max(0.0, float(self._live_delta))
        else:
            project_id, delta = self._live_segment_getter()
            delta = max(0.0, float(delta))
        sub_id = self._active_sub_id_getter() if self._active_sub_id_getter else None
        return project_id, sub_id, delta

    def _setup_window(self) -> None:
        self._win.title("Report")
        self._win.minsize(_WEEKLY_MIN_W, _DIALOG_H)
        self._resize(self._recommended_width("monthly"), _DIALOG_H, initial=True)
        self._win.bind("<Configure>", self._on_window_configure)

    def _recommended_width(self, mode: str) -> int:
        screen_w = self._win.winfo_screenwidth()
        max_w = max(_WEEKLY_MIN_W, screen_w - 80)
        target = 1460 if mode == "monthly" else 980
        min_w = _MONTHLY_MIN_W if mode == "monthly" else _WEEKLY_MIN_W
        return max(min_w, min(target, max_w))

    def _resize(self, w: int, h: int, initial: bool = False) -> None:
        self._win.update_idletasks()
        sw = self._win.winfo_screenwidth()
        sh = self._win.winfo_screenheight()
        if initial:
            try:
                px = self._parent.winfo_x()
                py = self._parent.winfo_y()
                x = min(px + 20, sw - w - 10)
                y = min(py + 20, sh - h - 10)
            except tk.TclError:
                x = max(0, (sw - w) // 2)
                y = max(0, (sh - h) // 2)
        else:
            x = self._win.winfo_x()
            y = self._win.winfo_y()
            x = min(x, sw - w - 10)
        x = max(0, x)
        y = max(0, y)
        self._win.geometry(f"{w}x{h}+{x}+{y}")

    def _configure_styles(self) -> None:
        t = self._theme
        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Report.Treeview",
            background=t.entry_bg,
            foreground=t.fg_dim,
            fieldbackground=t.entry_bg,
            selectbackground=t.sel_bg,
            selectforeground=t.fg,
            rowheight=22,
            font=("Arial", 8),
        )
        style.configure(
            "Report.Treeview.Heading",
            background=t.btn_bg,
            foreground=t.fg_dim,
            font=("Arial", 8, "bold"),
        )
        style.map(
            "Report.Treeview",
            background=[("selected", t.sel_bg)],
            foreground=[("selected", t.fg)],
        )

        style.configure(
            "Report.TCombobox",
            fieldbackground=t.bg,
            background=t.bg,
            foreground=t.fg,
            arrowcolor=t.fg_dim,
            selectbackground=t.bg,
            selectforeground=t.fg,
        )
        style.map(
            "Report.TCombobox",
            fieldbackground=[("readonly", t.bg), ("active", t.bg)],
            foreground=[("readonly", t.fg), ("active", t.fg)],
            selectbackground=[("readonly", t.bg), ("active", t.bg)],
            selectforeground=[("readonly", t.fg), ("active", t.fg)],
            background=[("readonly", t.bg), ("active", t.bg)],
        )

        style.configure(
            "Report.Vertical.TScrollbar",
            background=t.btn_bg,
            troughcolor=t.entry_bg,
            arrowcolor=t.fg_dim,
            darkcolor=t.btn_bg,
            lightcolor=t.btn_bg,
            bordercolor=t.bg,
            relief="flat",
        )
        style.map(
            "Report.Vertical.TScrollbar",
            background=[("active", t.sel_bg), ("pressed", t.sel_bg)],
            arrowcolor=[("active", t.fg), ("pressed", t.fg)],
        )
        # Combobox popdown scrollbars use the base ttk scrollbar style on
        # Windows, so mirror the same palette there for consistency.
        style.configure(
            "Vertical.TScrollbar",
            background=t.btn_bg,
            troughcolor=t.entry_bg,
            arrowcolor=t.fg_dim,
            darkcolor=t.btn_bg,
            lightcolor=t.btn_bg,
            bordercolor=t.bg,
            relief="flat",
        )
        style.map(
            "Vertical.TScrollbar",
            background=[("active", t.sel_bg), ("pressed", t.sel_bg)],
            arrowcolor=[("active", t.fg), ("pressed", t.fg)],
        )

        style.configure(
            "Report.Horizontal.TScrollbar",
            background=t.btn_bg,
            troughcolor=t.entry_bg,
            arrowcolor=t.fg_dim,
            darkcolor=t.btn_bg,
            lightcolor=t.btn_bg,
            bordercolor=t.bg,
            relief="flat",
        )
        style.map(
            "Report.Horizontal.TScrollbar",
            background=[("active", t.sel_bg), ("pressed", t.sel_bg)],
            arrowcolor=[("active", t.fg), ("pressed", t.fg)],
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=t.btn_bg,
            troughcolor=t.entry_bg,
            arrowcolor=t.fg_dim,
            darkcolor=t.btn_bg,
            lightcolor=t.btn_bg,
            bordercolor=t.bg,
            relief="flat",
        )
        style.map(
            "Horizontal.TScrollbar",
            background=[("active", t.sel_bg), ("pressed", t.sel_bg)],
            arrowcolor=[("active", t.fg), ("pressed", t.fg)],
        )

        # Style combobox dropdown popup listboxes consistently (same approach
        # as the main widget combobox styling).
        for widget in (self._parent, self._win):
            widget.option_add("*TCombobox*Listbox.background", t.bg)  # pyright: ignore
            widget.option_add("*TCombobox*Listbox.foreground", t.fg)  # pyright: ignore
            widget.option_add(  # pyright: ignore
                "*TCombobox*Listbox.selectBackground", t.sel_bg
            )
            widget.option_add(  # pyright: ignore
                "*TCombobox*Listbox.selectForeground", t.fg
            )

    def _build_ui(self) -> None:
        t = self._theme
        outer = tk.Frame(
            self._win,
            bg=t.bg,
            highlightbackground=t.fg_dim,
            highlightthickness=1,
        )
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        title_bar = tk.Frame(outer, bg=t.bg, height=28)
        title_bar.pack(fill="x", padx=4, pady=(1, 0))
        title_bar.pack_propagate(False)

        self._title_icon_lbl = tk.Label(
            title_bar,
            text="\U0001f4c8",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 11, "bold"),
        )
        self._title_icon_lbl.pack(side="left", padx=(6, 2))

        self._title_lbl = tk.Label(
            title_bar,
            text="Monthly Report",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 10, "bold"),
        )
        self._title_lbl.pack(side="left", padx=(0, 8))

        mode_frame = tk.Frame(title_bar, bg=t.bg)
        mode_frame.pack(side="left")
        self._mode_btn_monthly = tk.Button(
            mode_frame,
            text="Monthly",
            bg=t.sel_bg,
            fg=t.fg,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            font=("Arial", 8, "bold"),
            bd=1,
            relief="raised",
            padx=5,
            pady=0,
            command=lambda: self._switch_mode("monthly"),
        )
        self._mode_btn_monthly.pack(side="left", padx=(0, 2))
        self._mode_btn_weekly = tk.Button(
            mode_frame,
            text="Weekly",
            bg=t.btn_bg,
            fg=t.fg_dim,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            font=("Arial", 8),
            bd=1,
            relief="raised",
            padx=5,
            pady=0,
            command=lambda: self._switch_mode("weekly"),
        )
        self._mode_btn_weekly.pack(side="left")

        close_btn = tk.Button(
            title_bar,
            text="\u2715",
            bg=t.close_bg,
            fg=t.close_fg,
            font=("Arial", 10, "bold"),
            bd=0,
            width=2,
            command=self._close,
        )
        close_btn.pack(side="right", padx=2)

        for w in (title_bar, self._title_icon_lbl, self._title_lbl):
            w.bind("<Button-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_motion)

        ctrl_frame = tk.Frame(outer, bg=t.bg)
        ctrl_frame.pack(fill="x", padx=6, pady=(1, 3))

        self._monthly_ctrl = tk.Frame(ctrl_frame, bg=t.bg)
        self._monthly_ctrl.pack(side="left")
        self._build_monthly_controls(self._monthly_ctrl)

        self._weekly_ctrl = tk.Frame(ctrl_frame, bg=t.bg)
        self._build_weekly_controls(self._weekly_ctrl)

        self._preset_frame = tk.Frame(ctrl_frame, bg=t.bg)
        self._preset_frame.pack(side="left", padx=(10, 0))
        for label, handler in (
            ("This Week", self._preset_this_week),
            ("This Month", self._preset_this_month),
            ("Last Month", self._preset_last_month),
        ):
            tk.Button(
                self._preset_frame,
                text=label,
                command=handler,
                bg=t.btn_bg,
                fg=t.fg,
                activebackground=t.btn_active,
                activeforeground=t.fg,
                relief="raised",
                bd=1,
                font=("Arial", 8, "bold"),
                padx=5,
                pady=0,
            ).pack(side="left", padx=(0, 2))

        tk.Label(
            ctrl_frame,
            text="Filter:",
            bg=t.bg,
            fg=t.fg,
            font=("Arial", 9, "bold"),
        ).pack(side="left", padx=(10, 4))

        self._filter_var = tk.StringVar(value="All Projects")
        self._filter_combo = ttk.Combobox(
            ctrl_frame,
            textvariable=self._filter_var,
            state="readonly",
            width=18,
            style="Report.TCombobox",
            font=("Arial", 9),
            postcommand=lambda: self._style_combobox_popup(self._filter_combo),
        )
        self._filter_combo.pack(side="left")
        self._filter_combo.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._on_filter_changed(),
        )
        self._update_filter_options()

        self._show_non_zero_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            ctrl_frame,
            text="Non-zero only",
            variable=self._show_non_zero_var,
            command=self._refresh,
            bg=t.bg,
            fg=t.fg,
            activebackground=t.bg,
            activeforeground=t.fg,
            selectcolor=t.bg,
            font=("Arial", 9),
        ).pack(side="left", padx=(10, 0))
        self._projects_only_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            ctrl_frame,
            text="Projects only",
            variable=self._projects_only_var,
            command=self._refresh,
            bg=t.bg,
            fg=t.fg,
            activebackground=t.bg,
            activeforeground=t.fg,
            selectcolor=t.bg,
            font=("Arial", 9),
        ).pack(side="left", padx=(10, 0))

        action_frame = tk.Frame(ctrl_frame, bg=t.bg)
        action_frame.pack(side="right")
        tk.Button(
            action_frame,
            text="Copy",
            command=self._copy_summary,
            bg=t.btn_bg,
            fg=t.fg,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            relief="raised",
            bd=1,
            font=("Arial", 9, "bold"),
            width=7,
        ).pack(side="left", padx=(0, 4))
        tk.Button(
            action_frame,
            text="Export",
            command=self._export,
            bg=t.btn_bg,
            fg=t.fg,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            relief="raised",
            bd=1,
            font=("Arial", 9, "bold"),
            width=7,
        ).pack(side="left")

        tk.Frame(outer, bg=t.sep, height=1).pack(fill="x", pady=(1, 4))

        table_frame = tk.Frame(outer, bg=t.bg, relief="sunken", bd=1)
        table_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self._tree = ttk.Treeview(
            table_frame,
            style="Report.Treeview",
            show="tree headings",
            height=18,
        )
        y_sb = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self._tree.yview,  # pyright: ignore
            style="Report.Vertical.TScrollbar",
        )
        x_sb = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self._tree.xview,  # pyright: ignore
            style="Report.Horizontal.TScrollbar",
        )
        self._tree.configure(yscrollcommand=y_sb.set, xscrollcommand=x_sb.set)
        y_sb.pack(side="right", fill="y")
        x_sb.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)

        self._tree.bind("<Shift-MouseWheel>", self._on_shift_wheel)

        # Footer summary label removed to keep the table area clean.
        self._summary_var = None

    def _build_monthly_controls(self, parent: tk.Frame) -> None:
        t = self._theme
        tk.Label(
            parent,
            text="Year:",
            bg=t.bg,
            fg=t.fg,
            font=("Arial", 9, "bold"),
        ).pack(side="left", padx=(0, 4))
        self._year_var = tk.StringVar(value=str(self._year))
        year_spin = tk.Spinbox(
            parent,
            from_=2000,
            to=2100,
            width=6,
            textvariable=self._year_var,
            command=self._on_date_changed,
            bg=t.btn_bg,
            fg=t.fg,
            buttonbackground=t.btn_bg,
            insertbackground=t.fg,
            relief="solid",
            bd=1,
            font=("Arial", 9),
        )
        year_spin.pack(side="left")

        tk.Label(
            parent,
            text="  Month:",
            bg=t.bg,
            fg=t.fg,
            font=("Arial", 9, "bold"),
        ).pack(side="left", padx=(8, 4))
        month_names = [calendar.month_name[i] for i in range(1, 13)]
        self._month_var = tk.StringVar(value=calendar.month_name[self._month])
        month_combo = ttk.Combobox(
            parent,
            textvariable=self._month_var,
            values=month_names,
            state="readonly",
            width=12,
            style="Report.TCombobox",
            font=("Arial", 9),
            postcommand=lambda: self._style_combobox_popup(month_combo),
        )
        month_combo.pack(side="left")
        month_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_date_changed())

        for text, cmd in (("\u25c4", self._prev_month), ("\u25ba", self._next_month)):
            tk.Button(
                parent,
                text=text,
                command=cmd,
                bg=t.btn_bg,
                fg=t.fg,
                activebackground=t.btn_active,
                activeforeground=t.fg,
                relief="raised",
                bd=1,
                font=("Arial", 9, "bold"),
                width=3,
                pady=0,
            ).pack(side="left", padx=2)

    def _build_weekly_controls(self, parent: tk.Frame) -> None:
        t = self._theme
        iso = self._week_start.isocalendar()
        tk.Label(
            parent,
            text="Week:",
            bg=t.bg,
            fg=t.fg,
            font=("Arial", 9, "bold"),
        ).pack(side="left", padx=(0, 4))
        self._week_year_var = tk.StringVar(value=str(iso.year))
        year_spin = tk.Spinbox(
            parent,
            from_=2000,
            to=2100,
            width=6,
            textvariable=self._week_year_var,
            command=self._on_week_selector_changed,
            bg=t.btn_bg,
            fg=t.fg,
            buttonbackground=t.btn_bg,
            insertbackground=t.fg,
            relief="solid",
            bd=1,
            font=("Arial", 9),
        )
        year_spin.pack(side="left", padx=(0, 4))
        year_spin.bind("<Return>", lambda _e: self._on_week_selector_changed())
        year_spin.bind("<FocusOut>", lambda _e: self._on_week_selector_changed())

        self._week_num_var = tk.StringVar(value=f"CW{iso.week:02d}")
        self._week_combo = ttk.Combobox(
            parent,
            textvariable=self._week_num_var,
            state="readonly",
            width=6,
            style="Report.TCombobox",
            font=("Arial", 9),
            postcommand=lambda: self._style_combobox_popup(self._week_combo),
        )
        self._week_combo.pack(side="left", padx=(0, 4))
        self._week_combo.bind(
            "<<ComboboxSelected>>", lambda _e: self._on_week_selector_changed()
        )
        self._update_week_combo_values(iso.year)

        self._week_lbl = tk.Label(
            parent,
            text=self._week_label(),
            bg=t.bg,
            fg=t.fg,
            font=("Arial", 9),
            width=18,
            anchor="w",
        )
        self._week_lbl.pack(side="left", padx=(0, 4))
        for text, cmd in (("\u25c4", self._prev_week), ("\u25ba", self._next_week)):
            tk.Button(
                parent,
                text=text,
                command=cmd,
                bg=t.btn_bg,
                fg=t.fg,
                activebackground=t.btn_active,
                activeforeground=t.fg,
                relief="raised",
                bd=1,
                font=("Arial", 9, "bold"),
                width=3,
                pady=0,
            ).pack(side="left", padx=2)

    def _switch_mode(self, mode: str) -> None:
        if mode == self._view_mode:
            return
        t = self._theme
        self._view_mode = mode
        before = self._preset_frame if self._preset_frame is not None else None
        if mode == "monthly":
            if self._weekly_ctrl is not None:
                self._weekly_ctrl.pack_forget()
            if self._monthly_ctrl is not None:
                if before is not None:
                    self._monthly_ctrl.pack(side="left", before=before)
                else:
                    self._monthly_ctrl.pack(side="left")
            if self._title_lbl is not None:
                self._title_lbl.config(text="Monthly Report")
            if self._mode_btn_monthly is not None:
                self._mode_btn_monthly.config(
                    bg=t.sel_bg,
                    fg=t.fg,
                    font=("Arial", 8, "bold"),
                )
            if self._mode_btn_weekly is not None:
                self._mode_btn_weekly.config(
                    bg=t.btn_bg,
                    fg=t.fg_dim,
                    font=("Arial", 8),
                )
        else:
            if self._monthly_ctrl is not None:
                self._monthly_ctrl.pack_forget()
            if self._weekly_ctrl is not None:
                if before is not None:
                    self._weekly_ctrl.pack(side="left", before=before)
                else:
                    self._weekly_ctrl.pack(side="left")
            if self._title_lbl is not None:
                self._title_lbl.config(text="Weekly Report")
            if self._mode_btn_monthly is not None:
                self._mode_btn_monthly.config(
                    bg=t.btn_bg,
                    fg=t.fg_dim,
                    font=("Arial", 8),
                )
            if self._mode_btn_weekly is not None:
                self._mode_btn_weekly.config(
                    bg=t.sel_bg,
                    fg=t.fg,
                    font=("Arial", 8, "bold"),
                )
        self._refresh()

    def _preset_this_week(self) -> None:
        self._week_start = date.today() - timedelta(days=date.today().weekday())
        if self._view_mode == "weekly":
            self._refresh()
        else:
            self._switch_mode("weekly")

    def _preset_this_month(self) -> None:
        now = datetime.now()
        self._year = now.year
        self._month = now.month
        if self._year_var is not None:
            self._year_var.set(str(self._year))
        if self._month_var is not None:
            self._month_var.set(calendar.month_name[self._month])
        if self._view_mode == "monthly":
            self._refresh()
        else:
            self._switch_mode("monthly")

    def _preset_last_month(self) -> None:
        now = datetime.now()
        if now.month == 1:
            self._year = now.year - 1
            self._month = 12
        else:
            self._year = now.year
            self._month = now.month - 1
        if self._year_var is not None:
            self._year_var.set(str(self._year))
        if self._month_var is not None:
            self._month_var.set(calendar.month_name[self._month])
        if self._view_mode == "monthly":
            self._refresh()
        else:
            self._switch_mode("monthly")

    def _update_filter_options(self) -> None:
        projects = [p for p in self._project_mgr.projects if not p.archived]
        options = ["All Projects"] + [p.alias or p.name for p in projects]
        if self._filter_combo is not None:
            self._filter_combo["values"] = options
        if self._filter_var is not None and self._filter_var.get() not in options:
            self._filter_var.set("All Projects")
            self._filter_project_id = None

    def _style_combobox_popup(self, combo: Optional[ttk.Combobox]) -> None:
        """Force popup listbox/scrollbar colors for a ttk Combobox."""
        if combo is None:
            return
        t = self._theme
        try:
            popdown = combo.tk.eval(f"ttk::combobox::PopdownWindow {combo}")
            listbox = f"{popdown}.f.l"
            scrollbar = f"{popdown}.f.sb"
            combo.tk.call(
                listbox,
                "configure",
                "-background",
                t.bg,
                "-foreground",
                t.fg,
                "-selectbackground",
                t.sel_bg,
                "-selectforeground",
                t.fg,
            )
            combo.tk.call(
                scrollbar,
                "configure",
                "-background",
                t.btn_bg,
                "-troughcolor",
                t.entry_bg,
                "-activebackground",
                t.btn_active,
            )
        except tk.TclError:
            # Popup internals vary by platform/theme; ignore unsupported options.
            pass

    def _on_filter_changed(self) -> None:
        if self._filter_var is None:
            return
        selected = self._filter_var.get()
        if selected == "All Projects":
            self._filter_project_id = None
        else:
            self._filter_project_id = None
            for p in self._project_mgr.projects:
                if (p.alias or p.name) == selected:
                    self._filter_project_id = p.project_id
                    break
        self._refresh()

    def _filtered_projects(self) -> list[Any]:
        projects = [p for p in self._project_mgr.projects if not p.archived]
        if self._filter_project_id is not None:
            projects = [p for p in projects if p.project_id == self._filter_project_id]
        return projects

    def _refresh(self) -> None:
        if self._closed or self._tree is None:
            return
        self._update_filter_options()
        if self._view_mode == "weekly":
            if self._week_lbl is not None:
                self._week_lbl.config(text=self._week_label())
            self._sync_week_selector()

        live_project_id, live_sub_activity_id, live_delta = self._resolve_live_segment()

        projects = self._filtered_projects()
        projects_payload = [
            {"project_id": p.project_id, "name": p.name, "alias": p.alias}
            for p in projects
        ]
        request: dict[str, Any] = {
            "mode": self._view_mode,
            "year": self._year,
            "month": self._month,
            "week_start": self._week_start,
            "projects": projects_payload,
            "live_project_id": live_project_id,
            "live_sub_activity_id": live_sub_activity_id,
            "live_delta": live_delta,
        }
        self._refresh_seq += 1
        seq = self._refresh_seq
        with self._refresh_lock:
            if self._refresh_future is not None and not self._refresh_future.done():
                self._refresh_future.cancel()
            self._refresh_future = self._refresh_executor.submit(
                compute_refresh_payload, self._storage, request
            )
            self._refresh_future_seq = seq
        self._ensure_refresh_polling()

    def _schedule_auto_refresh(self) -> None:
        if self._auto_refresh_job is None:
            self._auto_refresh_job = self._win.after(
                _AUTO_REFRESH_MS,
                self._on_auto_refresh_tick,
            )

    def _on_auto_refresh_tick(self) -> None:
        self._auto_refresh_job = None
        if self._closed:
            return
        self._refresh()
        self._schedule_auto_refresh()

    def _ensure_refresh_polling(self) -> None:
        if self._refresh_poll_job is None:
            self._refresh_poll_job = self._win.after(20, self._poll_refresh_future)

    def _poll_refresh_future(self) -> None:
        self._refresh_poll_job = None
        if self._closed:
            return
        future = self._refresh_future
        if future is None:
            return
        if not future.done():
            self._refresh_poll_job = self._win.after(20, self._poll_refresh_future)
            return
        seq = self._refresh_future_seq
        try:
            payload = future.result()
        except Exception:  # pylint: disable=broad-except
            logger.exception("Report refresh worker failed")
            return
        if seq != self._refresh_seq or self._tree is None:
            return
        self._apply_refresh_payload(payload)

    def _apply_refresh_payload(self, payload: dict[str, Any]) -> None:
        mode = str(payload.get("mode", "monthly"))
        columns = list(payload.get("columns", []))
        weekend_days = (
            list(payload.get("weekend_days", [])) if mode == "monthly" else None
        )
        self._configure_table_columns(columns, weekend_days=weekend_days)
        self._totals_by_column = dict(payload.get("totals", {}))
        day_cols = list(payload.get("day_cols", []))
        rows = list(payload.get("rows", []))
        self._render_rows(rows, day_cols)
        self._set_summary(
            range_text=str(payload.get("range_text", "")),
            total=_to_float(self._totals_by_column.get("total", 0.0)),
            rows_total=int(payload.get("rows_total", 0)),
        )

    def _configure_table_columns(
        self,
        columns: list[str],
        weekend_days: Optional[list[int]] = None,
    ) -> None:
        tree = self._tree
        assert tree is not None
        tree["columns"] = columns
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekend_days = weekend_days or []

        tree.heading("#0", text="Project / Activity", anchor="w")
        tree.heading("#0", command=lambda: self._sort_by("name"))

        for col in columns:
            if col == "total":
                tree.heading(col, text="Total", anchor="center")
            elif self._view_mode == "monthly":
                day_num = int(col[1:])
                label = f"[{day_num}]" if day_num in weekend_days else str(day_num)
                tree.heading(col, text=label, anchor="center")
            else:
                idx = int(col[1:])
                day_date = self._week_start + timedelta(days=idx)
                label = f"{day_names[day_date.weekday()]} {day_date.day}"
                if day_date.weekday() >= 5:
                    label = f"[{label}]"
                tree.heading(col, text=label, anchor="center")

        for col in columns:
            tree.heading(col, command=partial(self._sort_by, col))

        self._apply_column_widths()

    def _apply_column_widths(self) -> None:
        tree = self._tree
        if tree is None:
            return
        columns = list(tree["columns"])
        if not columns:
            return
        width = tree.winfo_width()
        if width <= 1:
            width = self._win.winfo_width() - 40
        width = max(_WEEKLY_MIN_W - 60, width)
        day_count = max(0, len(columns) - 1)
        if self._view_mode == "monthly":
            # Keep all days visible in one monthly view when possible.
            name_w = max(220, int(width * 0.20))
            total_w = 72
            usable = max(280, width - name_w - total_w - 24)
            day_w = 40 if day_count == 0 else max(30, min(44, usable // day_count))
        else:
            name_w = max(280, int(width * 0.34))
            remaining = max(260, width - name_w - 24)
            total_w = 96
            day_w = 96
            if day_count > 0:
                day_w = max(76, min(128, (remaining - total_w) // day_count))
        tree.column("#0", width=name_w, minwidth=200, anchor="w", stretch=True)
        for col in columns:
            if col == "total":
                continue
            min_w = 30 if self._view_mode == "monthly" else 48
            tree.column(
                col, width=day_w, minwidth=min_w, anchor="center", stretch=False
            )
        tree.column("total", width=total_w, minwidth=60, anchor="center", stretch=False)

    def _capture_selection_key(self) -> Optional[tuple[str, str, Optional[str]]]:
        """Capture selected row identity so it can be restored after refresh."""
        tree = self._tree
        if tree is None:
            return None
        selected = tree.selection()
        if not selected:
            return None
        iid = selected[0]
        parent_iid = tree.parent(iid)
        text = str(tree.item(iid).get("text", ""))
        if parent_iid == "":
            tags = tuple(str(tag) for tag in tree.item(iid).get("tags", ()))
            if "totals" in tags:
                return ("totals", text, None)
            return ("project", text, None)
        parent_text = str(tree.item(parent_iid).get("text", ""))
        return ("sub", text, parent_text)

    def _restore_selection_key(
        self,
        key: Optional[tuple[str, str, Optional[str]]],
    ) -> None:
        """Restore previously selected row by semantic identity."""
        if key is None:
            return
        tree = self._tree
        if tree is None:
            return
        kind, text, parent_text = key
        target_iid: Optional[str] = None
        for iid in tree.get_children(""):
            row_text = str(tree.item(iid).get("text", ""))
            if kind == "project" and row_text == text:
                target_iid = iid
                break
            if kind == "totals" and row_text == text:
                tags = tuple(str(tag) for tag in tree.item(iid).get("tags", ()))
                if "totals" in tags:
                    target_iid = iid
                    break
            if kind == "sub" and row_text == parent_text:
                for child_iid in tree.get_children(iid):
                    child_text = str(tree.item(child_iid).get("text", ""))
                    if child_text == text:
                        target_iid = child_iid
                        break
                if target_iid is not None:
                    break
        if target_iid is None:
            return
        tree.selection_set(target_iid)
        tree.focus(target_iid)
        tree.see(target_iid)

    def _render_rows(self, rows: list[RowData], day_cols: list[str]) -> None:
        tree = self._tree
        assert tree is not None
        selected_key = self._capture_selection_key()
        for item in tree.get_children():
            tree.delete(item)

        sorted_rows = self._sorted_rows(rows)
        shown_projects = 0
        show_non_zero = (
            self._show_non_zero_var is not None and self._show_non_zero_var.get()
        )
        projects_only = (
            self._projects_only_var is not None and self._projects_only_var.get()
        )
        alternating = 0
        for row in sorted_rows:
            total = _to_float(row.get("total", 0.0))  # project total in selected range
            raw_children = row.get("children", [])
            children_src = (
                cast(list[Any], raw_children) if isinstance(raw_children, list) else []
            )
            children: list[dict[str, Any]] = [
                cast(dict[str, Any], c) for c in children_src if isinstance(c, dict)
            ]
            shown_children: list[dict[str, Any]] = []
            for child in children:
                child_total = _to_float(child.get("total", 0.0))
                if show_non_zero and child_total < 60:
                    continue
                shown_children.append(child)
            if show_non_zero:
                if projects_only:
                    if total < 60:
                        continue
                elif total < 60 and not shown_children:
                    continue

            values: list[str] = []
            for col in day_cols:
                values.append(_fmt(_to_float(row.get(col, 0.0))))
            values.append(_fmt(total))
            row_tag = "project_even" if alternating % 2 == 0 else "project_odd"
            project_iid = tree.insert(
                "",
                "end",
                text=str(row.get("name", "")),
                values=values,
                open=True,
                tags=(row_tag,),
            )
            alternating += 1
            shown_projects += 1

            if not projects_only:
                for child in shown_children:
                    child_values: list[str] = []
                    for col in day_cols:
                        child_values.append(_fmt(_to_float(child.get(col, 0.0))))
                    child_values.append(_fmt(_to_float(child.get("total", 0.0))))
                    tree.insert(
                        project_iid,
                        "end",
                        text=str(child.get("name", "")),
                        values=child_values,
                        tags=("sub",),
                    )
        self._shown_rows_count = shown_projects

        total_values: list[str] = []
        for col in day_cols:
            total_values.append(_fmt(self._totals_by_column.get(col, 0.0)))
        total_values.append(_fmt_total(self._totals_by_column.get("total", 0.0)))
        tree.insert(
            "",
            "end",
            text="DAILY TOTALS",
            values=total_values,
            tags=("totals",),
        )

        t = self._theme
        tree.tag_configure("project_even", background=t.entry_bg, foreground=t.fg)
        tree.tag_configure("project_odd", background=t.bg, foreground=t.fg)
        tree.tag_configure("sub", background=t.bg, foreground=t.fg_dim)
        tree.tag_configure("totals", foreground=t.fg, font=("Arial", 9, "bold"))
        self._restore_selection_key(selected_key)
        self._apply_column_widths()

    def _sorted_rows(self, rows: list[RowData]) -> list[RowData]:
        col = self._sort_column
        desc = self._sort_desc
        if col == "name":
            return sorted(
                rows, key=lambda r: str(r.get("name", "")).lower(), reverse=desc
            )
        return sorted(rows, key=lambda r: _to_float(r.get(col, 0.0)), reverse=desc)

    def _sort_by(self, column: str) -> None:
        if column == self._sort_column:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_column = column
            self._sort_desc = column != "name"
        self._refresh()

    def _set_summary(self, range_text: str, total: float, rows_total: int) -> None:
        if self._summary_var is None:
            return
        shown = rows_total
        if self._show_non_zero_var is not None and self._show_non_zero_var.get():
            shown = self._shown_rows_count
        filt = (
            self._filter_var.get() if self._filter_var is not None else "All Projects"
        )
        self._summary_var.set(
            f"{range_text} | Total {_fmt_total(total)} | Projects {shown}/{rows_total}"
            f" | Filter: {filt}"
        )

    def _iter_tree_rows(
        self, parent: str = "", depth: int = 0
    ) -> list[tuple[str, list[object]]]:
        """Return all tree rows as ``(text, values)`` tuples (recursive)."""
        tree = self._tree
        if tree is None:
            return []
        rows: list[tuple[str, list[object]]] = []
        for item in tree.get_children(parent):
            text = str(tree.item(item).get("text", ""))
            rows.append((("  " * depth) + text, list(tree.item(item)["values"])))
            rows.extend(self._iter_tree_rows(item, depth + 1))
        return rows

    def _copy_summary(self) -> None:
        tree = self._tree
        if tree is None:
            return
        lines: list[str] = []
        if self._summary_var is not None:
            lines.append(self._summary_var.get())
        cols = list(tree["columns"])
        header = [str(tree.heading("#0").get("text", "Project / Activity"))]
        header.extend(str(tree.heading(c).get("text", c)) for c in cols)
        lines.append("\t".join(header))
        for text, vals in self._iter_tree_rows():
            lines.append("\t".join([text, *(str(v) for v in vals)]))
        text = "\n".join(lines)
        self._win.clipboard_clear()
        self._win.clipboard_append(text)

    def _on_shift_wheel(self, event: "tk.Event[tk.Misc]") -> str:
        tree = self._tree
        if tree is None:
            return "break"
        step = -1 if event.delta > 0 else 1
        tree.xview_scroll(step, "units")
        return "break"

    def _export(self) -> None:
        if self._view_mode == "monthly":
            default_name = f"monthly_report_{self._year:04d}-{self._month:02d}"
        else:
            iso = self._week_start.isocalendar()
            default_name = f"weekly_report_{iso[0]}-W{iso[1]:02d}"

        filename = filedialog.asksaveasfilename(
            parent=self._win,
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
            title="Export Report",
            initialdir=self._last_export_dir,
            initialfile=f"{default_name}.csv",
        )
        if not filename:
            return
        self._last_export_dir = str(Path(filename).resolve().parent)
        try:
            if filename.lower().endswith(".txt"):
                if self._view_mode == "monthly":
                    self._export_txt_monthly(filename, self._year, self._month)
                else:
                    self._export_txt_weekly(filename)
            else:
                if self._view_mode == "monthly":
                    self._export_csv_monthly(filename, self._year, self._month)
                else:
                    self._export_csv_weekly(filename)
            messagebox.showinfo(
                "Export Complete",
                f"Report exported to:\n{filename}",
                parent=self._win,
            )
        except OSError as exc:
            messagebox.showerror(
                "Export Failed",
                f"Could not write file:\n{exc}",
                parent=self._win,
            )

    def _export_csv_monthly(self, filename: str, year: int, month: int) -> None:
        tree = self._tree
        assert tree is not None
        num_days = calendar.monthrange(year, month)[1]
        weekend_days = self._weekend_days(year, month)
        with open(filename, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [f"Monthly Time Tracking Report - {calendar.month_name[month]} {year}"]
            )
            writer.writerow(
                [f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
            )
            writer.writerow([])
            header = [str(tree.heading("#0").get("text", "Project / Activity"))]
            for d in range(1, num_days + 1):
                header.append(f"[{d}]" if d in weekend_days else str(d))
            header.append("Total")
            writer.writerow(header)
            for text, vals in self._iter_tree_rows():
                writer.writerow([text, *vals])

    def _export_csv_weekly(self, filename: str) -> None:
        tree = self._tree
        assert tree is not None
        week_end = self._week_start + timedelta(days=6)
        iso = self._week_start.isocalendar()
        with open(filename, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [
                    "Weekly Time Tracking Report - "
                    f"{self._week_start.strftime('%b %d')} - "
                    f"{week_end.strftime('%b %d, %Y')} (Week {iso[1]})"
                ]
            )
            writer.writerow(
                [f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
            )
            writer.writerow([])
            header = [str(tree.heading("#0").get("text", "Project / Activity"))]
            header.extend(str(tree.heading(c).get("text", c)) for c in tree["columns"])
            writer.writerow(header)
            for text, vals in self._iter_tree_rows():
                writer.writerow([text, *vals])

    def _export_txt_monthly(self, filename: str, year: int, month: int) -> None:
        tree = self._tree
        assert tree is not None
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write("MONTHLY TIME TRACKING REPORT\n")
            fh.write(f"{calendar.month_name[month]} {year}\n")
            fh.write("=" * 100 + "\n")
            for text, vals in self._iter_tree_rows():
                row = [text, *(str(v) for v in vals)]
                fh.write(" | ".join(row) + "\n")
            fh.write("=" * 100 + "\n")
            fh.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def _export_txt_weekly(self, filename: str) -> None:
        tree = self._tree
        assert tree is not None
        week_end = self._week_start + timedelta(days=6)
        iso = self._week_start.isocalendar()
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write("WEEKLY TIME TRACKING REPORT\n")
            fh.write(
                f"{self._week_start.strftime('%b %d')} - "
                f"{week_end.strftime('%b %d, %Y')} (Week {iso[1]})\n"
            )
            fh.write("=" * 100 + "\n")
            for text, vals in self._iter_tree_rows():
                row = [text, *(str(v) for v in vals)]
                fh.write(" | ".join(row) + "\n")
            fh.write("=" * 100 + "\n")
            fh.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    @staticmethod
    def _weekend_days(year: int, month: int) -> list[int]:
        num_days = calendar.monthrange(year, month)[1]
        return [
            d for d in range(1, num_days + 1) if date(year, month, d).weekday() >= 5
        ]

    def _week_label(self) -> str:
        end = self._week_start + timedelta(days=6)
        if self._week_start.month == end.month:
            return f"{self._week_start.strftime('%b %d')}-{end.day}, {end.year}"
        return f"{self._week_start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"

    @staticmethod
    def _weeks_in_iso_year(year: int) -> int:
        """Return the ISO week count for *year* (52 or 53)."""
        return date(year, 12, 28).isocalendar().week

    def _update_week_combo_values(self, year: int) -> None:
        combo = self._week_combo
        if combo is None:
            return
        week_count = self._weeks_in_iso_year(year)
        combo["values"] = [f"CW{w:02d}" for w in range(1, week_count + 1)]

    def _sync_week_selector(self) -> None:
        iso = self._week_start.isocalendar()
        self._update_week_combo_values(iso.year)
        if self._week_year_var is not None:
            self._week_year_var.set(str(iso.year))
        if self._week_num_var is not None:
            self._week_num_var.set(f"CW{iso.week:02d}")

    def _on_week_selector_changed(self) -> None:
        if self._week_year_var is None or self._week_num_var is None:
            return
        try:
            year = int(self._week_year_var.get())
            week = int(self._week_num_var.get().replace("CW", "").strip())
            week = max(1, min(week, self._weeks_in_iso_year(year)))
            self._week_start = date.fromisocalendar(year, week, 1)
        except (ValueError, TypeError):
            return
        self._refresh()

    def _on_date_changed(self) -> None:
        try:
            self._year = int(self._year_var.get())  # type: ignore[union-attr]
            self._month = list(calendar.month_name).index(
                self._month_var.get()  # type: ignore[union-attr]
            )
        except (ValueError, AttributeError):
            return
        self._refresh()

    def _prev_month(self) -> None:
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        if self._year_var is not None:
            self._year_var.set(str(self._year))
        if self._month_var is not None:
            self._month_var.set(calendar.month_name[self._month])
        self._refresh()

    def _next_month(self) -> None:
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        if self._year_var is not None:
            self._year_var.set(str(self._year))
        if self._month_var is not None:
            self._month_var.set(calendar.month_name[self._month])
        self._refresh()

    def _prev_week(self) -> None:
        self._week_start -= timedelta(weeks=1)
        self._refresh()

    def _next_week(self) -> None:
        self._week_start += timedelta(weeks=1)
        self._refresh()

    def _on_window_configure(self, event: "tk.Event[tk.Misc]") -> None:
        if event.widget is not self._win:
            return
        # Dragging the borderless dialog fires many Configure events even when
        # only x/y changes. Column reflow is needed only when size changes.
        new_size = (int(event.width), int(event.height))
        if new_size == self._last_window_size:
            return
        self._last_window_size = new_size
        if self._pending_resize_job is not None:
            try:
                self._win.after_cancel(self._pending_resize_job)
            except tk.TclError:
                pass
        # Defer to coalesce rapid resize bursts into one column layout pass.
        self._pending_resize_job = self._win.after(16, self._deferred_apply_columns)

    def _deferred_apply_columns(self) -> None:
        self._pending_resize_job = None
        if self._closed:
            return
        try:
            self._apply_column_widths()
        except tk.TclError:
            pass

    def _close(self) -> None:
        self._closed = True
        if self._auto_refresh_job is not None:
            try:
                self._win.after_cancel(self._auto_refresh_job)
            except tk.TclError:
                pass
            self._auto_refresh_job = None
        if self._refresh_poll_job is not None:
            try:
                self._win.after_cancel(self._refresh_poll_job)
            except tk.TclError:
                pass
            self._refresh_poll_job = None
        if self._pending_resize_job is not None:
            try:
                self._win.after_cancel(self._pending_resize_job)
            except tk.TclError:
                pass
            self._pending_resize_job = None
        try:
            self._refresh_executor.shutdown(wait=False, cancel_futures=True)
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("Report executor shutdown raised: %s", exc)
        try:
            self._win.destroy()
        except tk.TclError:
            pass


MonthlyReportDialog = ReportDialog
