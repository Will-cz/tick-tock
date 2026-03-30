"""Compact 'mini' view of Tick-Tock — v0.7.1."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Callable, Optional

from src.projects import ProjectManager
from src.storage import Storage
from src.ui.drag_mixin import DragMixin
from src.ui.formatting import format_elapsed
from src.ui.themes import Theme
from src.timer import Timer, TimerState


class MinimizedWidget(DragMixin):
    """Compact two-row widget displayed when the main window is minimized.

    Layout::

        [HH:MM:SS] │ [▶/⏸] │ [00:00:00]             [□]
        [Project ▼                  ] [Activity ▼        ]

    The widget operates by reading directly from the shared ``Timer`` and
    ``ProjectManager`` on every clock tick, so it always shows current state
    without needing explicit notifications from the main widget—except for
    combobox refresh after project/sub-activity switches, which the main
    widget triggers via :meth:`refresh_combos`.
    """

    _W = 300
    _H = 54
    # Keep project-level selection visually empty in the mini activity dropdown.
    _PROJECT_LEVEL_LABEL = ""

    def __init__(
        self,
        parent: tk.Tk,
        timer: Timer,
        project_mgr: Optional[ProjectManager],
        storage: Optional[Storage],
        theme: Theme,
        on_toggle: Callable[[], None],
        on_project_switch: Callable[[int], None],
        on_sub_switch: Callable[[int], None],
        on_maximize: Callable[[int, int], None],
        active_sub_id_getter: Optional[Callable[[], Optional[int]]] = None,
        start_x: int = 0,
        start_y: int = 0,
    ) -> None:
        self._parent = parent
        self._timer = timer
        self._project_mgr = project_mgr
        self._storage = storage
        self._theme = theme
        self._on_toggle = on_toggle
        self._on_project_switch = on_project_switch
        self._on_sub_switch = on_sub_switch
        self._on_maximize = on_maximize
        self._get_active_sub_id = active_sub_id_getter or (lambda: None)

        self._clock_job: Optional[str] = None
        self._drag_pending_job: Optional[str] = None
        self._init_drag_state()

        # Widget refs
        self._win: Optional[tk.Toplevel] = None
        self._time_lbl: Optional[tk.Label] = None
        self._elapsed_lbl: Optional[tk.Label] = None
        self._toggle_btn: Optional[tk.Button] = None
        self._project_combo: Optional[ttk.Combobox] = None
        self._activity_combo: Optional[ttk.Combobox] = None

        self._build(start_x, start_y)
        self._start_clock()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self, x: int, y: int) -> None:
        t = self._theme
        win = tk.Toplevel(self._parent)
        self._win = win
        win.overrideredirect(True)
        win.attributes("-topmost", True)  # pyright: ignore
        win.configure(bg=t.bg)
        win.geometry(f"{self._W}x{self._H}+{x}+{y}")
        win.protocol("WM_DELETE_WINDOW", self._maximize)

        # Border frame
        outer = tk.Frame(
            win, bg=t.bg, highlightbackground=t.fg_dim, highlightthickness=1
        )
        outer.pack(fill="both", expand=True, padx=2, pady=1)

        # --- Top row: clock | sep | toggle | sep | elapsed | maximize --
        top = tk.Frame(outer, bg=t.bg)
        top.pack(fill="x", padx=2, pady=(2, 1))

        left_container = tk.Frame(top, bg=t.bg)
        left_container.pack(side="left", fill="y", padx=2)

        self._time_lbl = tk.Label(
            left_container,
            text="00:00:00",
            bg=t.bg,
            fg=t.fg,
            font=("Consolas", 10, "bold"),
        )
        self._time_lbl.pack(side="left")

        tk.Label(
            left_container,
            text="︱",
            bg=t.bg,
            fg=t.fg,
            font=("Consolas", 10),
        ).pack(side="left", padx=2)

        self._toggle_btn = tk.Button(
            left_container,
            text="▶",
            bg=t.btn_bg,
            fg=t.btn_fg,
            activebackground=t.btn_active,
            activeforeground=t.btn_fg,
            font=("Arial", 8, "bold"),
            bd=0,
            width=2,
            command=self._on_toggle_clicked,
        )
        self._toggle_btn.pack(side="left")

        tk.Label(
            left_container,
            text="︱",
            bg=t.bg,
            fg=t.fg,
            font=("Consolas", 10),
        ).pack(side="left", padx=2)

        self._elapsed_lbl = tk.Label(
            left_container,
            text="00:00:00",
            bg=t.bg,
            fg=t.running_color,
            font=("Consolas", 10, "bold"),
        )
        self._elapsed_lbl.pack(side="left")

        maximize_btn = tk.Button(
            top,
            text="□",
            bg=t.btn_bg,
            fg=t.fg_dim,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            font=("Arial", 8, "bold"),
            bd=0,
            width=2,
            command=self._maximize,
        )
        maximize_btn.pack(side="right")

        # --- Bottom row: project combo | activity combo ---------------
        self._configure_ttk_style()
        bot = tk.Frame(outer, bg=t.bg)
        bot.pack(fill="x", padx=2, pady=(0, 1))

        self._project_combo = ttk.Combobox(
            bot,
            font=("Arial", 8),
            state="readonly",
            width=14,
            style="Mini.TCombobox",
            postcommand=lambda: self._style_combobox_popup(self._project_combo),
        )
        self._project_combo.pack(side="left", fill="x", expand=True, padx=(0, 2))
        self._project_combo.bind("<<ComboboxSelected>>", self._on_project_select)

        self._activity_combo = ttk.Combobox(
            bot,
            font=("Arial", 8),
            state="readonly",
            width=14,
            style="Mini.TCombobox",
            postcommand=lambda: self._style_combobox_popup(self._activity_combo),
        )
        self._activity_combo.pack(side="left", fill="x", expand=True)
        self._activity_combo.bind("<<ComboboxSelected>>", self._on_activity_select)

        # Bind drag on non-interactive widgets
        for w in (outer, top, self._time_lbl, self._elapsed_lbl, bot):
            w.bind("<Button-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_motion)

        self.refresh_combos()
        # Trim any unused vertical space based on actual rendered content.
        win.update_idletasks()
        win.geometry(f"{self._W}x{win.winfo_reqheight()}+{x}+{y}")

    def _configure_ttk_style(self) -> None:
        t = self._theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Mini.TCombobox",
            fieldbackground=t.bg,
            background=t.bg,
            foreground=t.fg,
            arrowcolor=t.fg_dim,
            selectbackground=t.bg,
            selectforeground=t.fg,
        )
        style.map(
            "Mini.TCombobox",
            fieldbackground=[("readonly", t.bg), ("active", t.bg)],
            foreground=[("readonly", t.fg), ("active", t.fg)],
            selectbackground=[("readonly", t.bg), ("active", t.bg)],
            selectforeground=[("readonly", t.fg), ("active", t.fg)],
            background=[("readonly", t.bg), ("active", t.bg)],
        )
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
        for widget in (self._parent, self._win):
            if widget is not None:
                widget.option_add(  # pyright: ignore
                    "*TCombobox*Listbox.background", t.bg
                )
                widget.option_add(  # pyright: ignore
                    "*TCombobox*Listbox.foreground", t.fg
                )
                widget.option_add(  # pyright: ignore
                    "*TCombobox*Listbox.selectBackground", t.sel_bg
                )
                widget.option_add(  # pyright: ignore
                    "*TCombobox*Listbox.selectForeground", t.fg
                )

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
            pass

    # ------------------------------------------------------------------
    # Clock / display
    # ------------------------------------------------------------------

    def _start_clock(self) -> None:
        self._tick()

    def _tick(self) -> None:
        win = self._win
        if win is None:
            return
        now = datetime.now()
        if self._time_lbl:
            self._time_lbl.config(text=now.strftime("%H:%M:%S"))
        self.refresh_display()
        self._clock_job = win.after(1000, self._tick)

    def refresh_display(self) -> None:
        """Refresh elapsed label and toggle button from current timer state."""
        t = self._theme
        state = self._timer.state
        elapsed = self._timer.elapsed
        poc_stop_red = "#FF4444"

        if self._elapsed_lbl:
            if state == TimerState.RUNNING:
                self._elapsed_lbl.config(
                    text=format_elapsed(elapsed, pad_hours=True), fg=poc_stop_red
                )
            elif state == TimerState.PAUSED:
                self._elapsed_lbl.config(
                    text=format_elapsed(elapsed, pad_hours=True), fg=t.paused_color
                )
            elif state == TimerState.STOPPED and elapsed > 0:
                self._elapsed_lbl.config(
                    text=format_elapsed(elapsed, pad_hours=True), fg=t.running_color
                )
            else:
                self._elapsed_lbl.config(text="00:00:00", fg=t.fg_dim)

        if self._toggle_btn:
            if state == TimerState.RUNNING:
                self._toggle_btn.config(
                    text="■",
                    fg=poc_stop_red,
                    bg=t.btn_bg,
                    activeforeground=poc_stop_red,
                    activebackground=t.btn_active,
                )
            elif state == TimerState.PAUSED:
                self._toggle_btn.config(
                    text="▶",
                    fg=t.paused_color,
                    bg=t.btn_bg,
                    activeforeground=t.btn_fg,
                    activebackground=t.btn_active,
                )
            elif state == TimerState.STOPPED and elapsed > 0:
                self._toggle_btn.config(
                    text="▶",
                    fg=t.btn_fg,
                    bg=t.btn_bg,
                    activeforeground=t.btn_fg,
                    activebackground=t.btn_active,
                )
            else:
                self._toggle_btn.config(
                    text="▶",
                    fg=t.btn_fg,
                    bg=t.btn_bg,
                    activeforeground=t.btn_fg,
                    activebackground=t.btn_active,
                )

    def refresh_combos(self) -> None:
        """Refresh project and activity comboboxes from current project state."""
        if self._project_mgr is None:
            return
        active = self._project_mgr.active_project
        projects = [p for p in self._project_mgr.projects if not p.archived]
        labels = [p.alias if p.alias else p.name for p in projects]

        if self._project_combo is not None:
            self._project_combo.configure(values=labels)
            if active:
                self._project_combo.set(active.alias if active.alias else active.name)

        if self._storage is not None and active is not None:
            subs = [
                r
                for r in self._storage.list_sub_activities(active.project_id)
                if not r["archived"]
            ]
            sa_labels = [r["name"] for r in subs]
            if self._activity_combo is not None:
                self._activity_combo.configure(
                    values=[self._PROJECT_LEVEL_LABEL, *sa_labels]
                )
                active_sub_id = self._get_active_sub_id()
                if active_sub_id is None:
                    self._activity_combo.set(self._PROJECT_LEVEL_LABEL)
                else:
                    selected_name = next(
                        (
                            row["name"]
                            for row in subs
                            if row["id"] == active_sub_id and not row["archived"]
                        ),
                        self._PROJECT_LEVEL_LABEL,
                    )
                    self._activity_combo.set(selected_name)

    # ------------------------------------------------------------------
    # DragMixin protocol
    # ------------------------------------------------------------------

    def _get_drag_window(self) -> Optional[tk.Toplevel]:
        return self._win

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_toggle_clicked(self) -> None:
        self._on_toggle()
        win = self._win
        if win is not None:
            win.after(0, self.refresh_display)

    def _on_project_select(self, _event: "tk.Event") -> None:
        combo = self._project_combo
        if combo is None or self._project_mgr is None:
            return
        selected = combo.get()
        for p in self._project_mgr.projects:
            if not p.archived:
                label = p.alias if p.alias else p.name
                if label == selected:
                    self._on_project_switch(p.project_id)
                    break

    def _on_activity_select(self, _event: "tk.Event") -> None:
        if self._project_mgr is None or self._storage is None:
            return
        active = self._project_mgr.active_project
        if active is None:
            return
        combo = self._activity_combo
        if combo is None:
            return
        selected = combo.get()
        if selected == self._PROJECT_LEVEL_LABEL:
            self._on_project_switch(active.project_id)
            return
        subs = self._storage.list_sub_activities(active.project_id)
        for row in subs:
            if row["name"] == selected and not row["archived"]:
                self._on_sub_switch(row["id"])
                break

    def _maximize(self) -> None:
        win = self._win
        if win is None:
            return
        x = win.winfo_x()
        y = win.winfo_y()
        if self._clock_job is not None:
            win.after_cancel(self._clock_job)
            self._clock_job = None
        if self._drag_pending_job is not None:
            win.after_cancel(self._drag_pending_job)
            self._drag_pending_job = (
                None  # pylint: disable=attribute-defined-outside-init
            )
        win.destroy()
        self._win = None
        self._on_maximize(x, y)

    def destroy(self) -> None:
        """Destroy the mini window (called externally, e.g. on app close)."""
        win = self._win
        if win is None:
            return
        if self._clock_job is not None:
            win.after_cancel(self._clock_job)
            self._clock_job = None
        if self._drag_pending_job is not None:
            win.after_cancel(self._drag_pending_job)
            self._drag_pending_job = (
                None  # pylint: disable=attribute-defined-outside-init
            )
        try:
            win.destroy()
        except tk.TclError:
            pass
        self._win = None
