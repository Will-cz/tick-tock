"""Main GUI widget for Tick-Tock — v0.11.1 System Tray."""

import ctypes
import logging
import sys
import threading
from pathlib import Path
from queue import Empty, SimpleQueue
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from typing import Any, Callable, Optional, cast

from src.app.services.widget_today_service import (
    TodayTotalCache,
    compute_today_display_total,
    on_daily_flushed as _on_daily_flushed_update,
    refresh_today_total,
)
from src.app.services.data_transfer_service import import_data, export_data
from src.app.services.widget_session_service import (
    restore_saved_timer_state,
    switch_active_project_session,
    switch_within_project_target_session,
)
from src.app.services.widget_panel_service import (
    compute_panel_window_height,
    resolve_panel_tab_click,
    resolve_panel_tab_label_colors,
)
from src.app.services.widget_project_selector_service import (
    build_project_selector_state,
    resolve_selected_project_id,
)
from src.app.services.widget_tree_service import (
    TreeNodeEntry,
    build_project_tree_rows,
    build_sub_activity_tree_rows,
    resolve_main_tree_click_action,
    resolve_projects_tree_click_action,
    resolve_projects_tree_live_update,
    resolve_sub_activity_tree_live_update,
    resolve_tree_item_activation,
)
from src.app_service import AppService
from src.config import Config, Environment
from src.ui.minimized_widget import MinimizedWidget
from src.ui.dialogs.project_dialog import ProjectManagementDialog
from src.projects import ProjectManager
from src.ui.dialogs.report_dialog import MonthlyReportDialog
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.storage import Storage
from src.sub_activities import SubActivityManager
from src.ui.system_tray import SystemTrayIcon
from src.ui.drag_mixin import DragMixin
from src.ui.formatting import format_elapsed
from src.ui.themes import MATRIX, Theme, resolve_theme
from src.ui.widget_controller import WidgetController
from src.timer import Timer, TimerEvent, TimerState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class TickTockWidget(DragMixin):
    """Simple timer widget with Matrix-style design.

    Lifecycle::

        widget = TickTockWidget()
        widget.run()          # blocks until window is closed
    """

    _WINDOW_W = 450
    _WINDOW_H = 180  # height without project row (includes opacity slider)
    _WINDOW_H_PROJECTS = 230  # startup fallback for collapsed panel state
    _WINDOW_H_TREE = 450  # height with tree view (sub-activities panel)
    _PANEL_COLLAPSED_H = 24  # tabs-only strip height inside the panel frame

    # Persist running state every N ticks (~seconds) to limit data loss on force-close.
    _PERIODIC_SAVE_INTERVAL = 60

    def __init__(
        self,
        timer: Optional[Timer] = None,
        storage: Optional[Storage] = None,
        project_manager: Optional[ProjectManager] = None,
        startup_warning: Optional[str] = None,
        config: Optional[Config] = None,
        app_service: Optional[AppService] = None,
    ) -> None:
        self._timer = timer if timer is not None else Timer()
        # Build or adopt AppService.  Keep self._storage / self._project_mgr as
        # convenience aliases so dialogs and MinimizedWidget can still receive them.
        if app_service is not None:
            self._app_service: Optional[AppService] = app_service
            self._storage: Optional[Storage] = app_service.storage
            self._project_mgr: Optional[ProjectManager] = app_service.project_manager
        elif storage is not None and project_manager is not None:
            self._app_service = AppService(storage, project_manager)
            self._storage = storage
            self._project_mgr = project_manager
        else:
            self._app_service = None
            self._storage = storage
            self._project_mgr = project_manager
        self._startup_warning = startup_warning
        self._config = config

        # Load theme from config (or default to Matrix)
        if config is not None:
            theme_cfg = config.get("theme", {})
            self._theme: Theme = resolve_theme(theme_cfg)
        else:
            self._theme = MATRIX

        self._root: Optional[tk.Tk] = None

        # Widget references (populated in _create_widgets)
        self._elapsed_label: Optional[tk.Label] = None
        self._time_label: Optional[tk.Label] = None
        self._date_label: Optional[tk.Label] = None
        self._toggle_btn: Optional[tk.Button] = None
        self._stop_btn: Optional[tk.Button] = None
        self._report_btn: Optional[tk.Button] = None
        self._title_icon_label: Optional[tk.Label] = None
        self._project_combobox: Optional[ttk.Combobox] = None
        self._opacity_var: Optional[tk.DoubleVar] = None
        self._title_label: Optional[tk.Label] = None
        self._always_on_top_var: Optional[tk.BooleanVar] = None

        # Sub-activity tracking state
        self._sub_activity_mgr: Optional[SubActivityManager] = None
        self._active_sub_activity_id: Optional[int] = None

        # Tree view (project + sub-activity hierarchy)
        self._tree: Optional[ttk.Treeview] = None
        self._tree_node_map: dict[str, TreeNodeEntry] = {}
        self._sub_tree_iids: dict[int, str] = {}

        # Panel tab state ("sub_activities" or "projects")
        self._panel_tab: str = "sub_activities"
        self._panel_collapsed: bool = False
        self._panel_outer: Optional[tk.LabelFrame] = None
        self._outer_frame: Optional[tk.Frame] = None  # ref for height measurement
        self._tab_sub_lbl: Optional[tk.Label] = None
        self._tab_proj_lbl: Optional[tk.Label] = None
        self._sub_activities_frame: Optional[tk.Frame] = None
        self._projects_frame: Optional[tk.Frame] = None
        self._projects_tree: Optional[ttk.Treeview] = None
        self._projects_tree_iids: dict[int, str] = {}

        # Set of project IDs currently expanded in the tree (persisted to config)
        self._tree_expanded_ids: set[int] = set()

        # Drag state
        self._init_drag_state()

        # Theme-registered widgets: list of (widget, tk_config_key, theme_attr)
        # Populated in _create_widgets; used by apply_theme().
        self._theme_refs: list[tuple[tk.Widget, str, str]] = []

        # Tkinter after() job id for the clock loop
        self._clock_job: Optional[str] = None
        self._ui_pump_job: Optional[str] = None
        self._config_reload_registered: bool = False

        # Minimized widget (compact mode) — set when main window is hidden
        self._minimized_widget: Optional[MinimizedWidget] = None

        # System tray icon (started in build())
        self._tray: Optional[SystemTrayIcon] = None

        # Flag to suppress project-elapsed save during an internal project switch
        # (owned by WidgetController; widget accesses it via self._controller)

        self._today_label: Optional[tk.Label] = None
        self._today_cache: TodayTotalCache = TodayTotalCache()
        self._ui_queue: SimpleQueue[Callable[[], None]] = SimpleQueue()
        self._main_thread_id = threading.get_ident()
        self._drag_pending_job: Optional[str] = None

        # Sleep/wake detection: wall-clock time at last tick
        self._last_tick_wall_time: Optional[datetime] = None

        # Wire timer events → UI refresh (thread-safe via after(0, ...))
        for event in (
            TimerEvent.STARTED,
            TimerEvent.PAUSED,
            TimerEvent.RESUMED,
            TimerEvent.STOPPED,
            TimerEvent.RESET,
            TimerEvent.TICK,
        ):
            self._timer.on(event, self._on_timer_event)

        # Build the controller (always created; safe when app_service is None).
        self._controller = WidgetController(
            app_service=self._app_service,
            project_manager=self._project_mgr,
            config=config,
            active_sub_callback=lambda: (
                self._active_sub_activity_id,
                self._sub_activity_mgr,
            ),
            daily_flush_callback=self._on_daily_flushed,
        )

        # Wire timer events → controller persistence callbacks.
        if self._app_service is not None:
            self._timer.on(TimerEvent.STARTED, self._controller.on_started)
            self._timer.on(TimerEvent.PAUSED, self._controller.on_paused)
            self._timer.on(TimerEvent.RESUMED, self._controller.on_resumed)
            self._timer.on(TimerEvent.STOPPED, self._controller.on_stopped)
            self._timer.on(TimerEvent.RESET, self._controller.on_reset)
            self._timer.on(TimerEvent.TICK, self._controller.on_tick)

        # Initialise sub-activity manager for the starting active project.
        if self._app_service is not None and self._project_mgr is not None:
            active = self._project_mgr.active_project
            if active is not None:
                self._sub_activity_mgr = self._app_service.create_sub_manager(
                    active.project_id
                )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def timer(self) -> Timer:
        """Expose the shared timer instance used by the widget."""
        return self._timer

    def build(self) -> None:
        """Create the Tk window and all widgets. Call before :meth:`run`."""
        self._root = tk.Tk()
        self._root.withdraw()  # hide during setup to prevent startup flicker
        self._setup_window()
        self._create_widgets()
        self._setup_dragging()
        self._start_ui_dispatcher()
        self._start_clock()
        self._setup_config_hot_reload()
        self._restore_timer_state()
        self._apply_timer_display()
        # Start system tray icon (no-op if pystray/Pillow unavailable)
        self._tray = SystemTrayIcon(
            on_show_hide=self._tray_toggle_visibility,
            on_quit=self._tray_quit,
        )
        self._tray.start()
        self._root.deiconify()  # show window after layout is fully initialised
        if self._startup_warning:
            messagebox.showwarning(
                "Startup Warning",
                self._startup_warning,
                parent=self._root,
            )

    def run(self) -> None:
        """Build (if not already done) then start the Tk event loop."""
        if self._root is None:
            self.build()
        assert self._root is not None
        self._root.mainloop()

    def request_external_activate(self) -> None:
        """Bring the app to front after an external activation ping."""
        self._post_ui(self._activate_from_external_request)

    def close(self) -> None:
        """Stop the timer, remove the tray icon, and destroy the window."""
        self._timer.stop()
        # Stop the config hot-reload watcher so no background threads linger.
        if self._config is not None:
            self._config.stop_watching()
        # Stop system tray before destroying the window.
        if self._tray is not None:
            self._tray.stop()
            self._tray = None
        if self._minimized_widget is not None:
            self._minimized_widget.destroy()
            self._minimized_widget = None
        if self._root is not None:
            self._save_window_state()
            if self._clock_job is not None:
                self._root.after_cancel(self._clock_job)
                self._clock_job = None
            if self._ui_pump_job is not None:
                self._root.after_cancel(self._ui_pump_job)
                self._ui_pump_job = None
            if self._drag_pending_job is not None:
                self._root.after_cancel(self._drag_pending_job)
                self._drag_pending_job = (
                    None  # pylint: disable=attribute-defined-outside-init
                )
            self._root.destroy()
            self._root = None

    def _activate_from_external_request(self) -> None:
        """Main-thread activation handler for second-launch requests."""
        root = self._root
        if root is None:
            return
        if self._minimized_widget is not None:
            self._minimized_widget.destroy()
            self._minimized_widget = None
        self._show_from_tray()
        try:
            root.lift()  # pyright: ignore
        except tk.TclError:
            pass

    def _setup_config_hot_reload(self) -> None:
        """Enable config file watching and route reloads onto the UI thread."""
        if self._config is None:
            return
        if not self._config_reload_registered:
            self._config.on_reload(self._on_config_reloaded)
            self._config_reload_registered = True
        self._config.start_watching()

    def _on_config_reloaded(self, cfg: Config) -> None:
        """Config watcher callback (background thread safe)."""
        self._post_ui(lambda: self._apply_reloaded_config(cfg))

    def _apply_reloaded_config(self, cfg: Config) -> None:
        """Apply hot-reloaded config values on the main UI thread."""
        theme_cfg = cfg.get("theme", {})
        self.apply_theme(resolve_theme(theme_cfg))

        root = self._root
        if root is None:
            return
        always_on_top = bool(cfg.get_ui_pref("always_on_top", True))
        root.attributes("-topmost", always_on_top)  # pyright: ignore
        if self._always_on_top_var is not None:
            self._always_on_top_var.set(always_on_top)
        root.title(self._get_window_title_text())

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        root = self._root
        assert root is not None

        root.title(self._get_window_title_text())
        root.configure(bg=self._theme.bg)
        root.overrideredirect(True)  # borderless

        # Load UI preferences from config (fall back to defaults)
        always_on_top: bool = True
        opacity: float = 0.90
        if self._config is not None:
            always_on_top = bool(self._config.get_ui_pref("always_on_top", True))
            opacity = float(self._config.get_ui_pref("opacity", 0.90))

        root.attributes("-topmost", always_on_top)  # pyright: ignore
        self._always_on_top_var = tk.BooleanVar(value=always_on_top)
        try:
            root.attributes("-alpha", opacity)  # pyright: ignore
        except tk.TclError:
            pass

        root.protocol("WM_DELETE_WINDOW", self._on_window_close_request)

        if self._project_mgr is not None:
            collapsed = (
                bool(self._config.get_ui_pref("panel_collapsed", False))
                if self._config
                else False
            )
            h = self._WINDOW_H_PROJECTS if collapsed else self._WINDOW_H_TREE
        else:
            h = self._WINDOW_H

        root.update_idletasks()
        vx, vy, vw, vh = self._get_virtual_screen_bounds(root)

        # Restore saved window position (with on-screen validation)
        saved_x = self._config.get_ui_pref("window_x") if self._config else None
        saved_y = self._config.get_ui_pref("window_y") if self._config else None
        if saved_x is not None and saved_y is not None:
            x, y = self._validate_window_position(
                int(saved_x),
                int(saved_y),
                self._WINDOW_W,
                h,
                vx,
                vy,
                vw,
                vh,
            )
        else:
            # No saved position: center on the virtual desktop area.
            x = vx + (vw - self._WINDOW_W) // 2
            y = vy + (vh - h) // 2

        root.geometry(f"{self._WINDOW_W}x{h}+{x}+{y}")

    def _create_widgets(self) -> None:
        root = self._root
        assert root is not None
        t = self._theme
        self._theme_refs.clear()

        def _reg(widget: tk.Widget, **role_map: str) -> None:
            """Register *widget* config attrs for re-theming."""
            for attr, role in role_map.items():
                self._theme_refs.append((widget, attr, role))

        # Outer frame with a thin border
        outer = tk.Frame(
            root,
            bg=t.bg,
            highlightbackground=t.fg_dim,
            highlightthickness=1,
        )
        outer.pack(fill="both", expand=True, padx=3, pady=3)
        _reg(outer, bg="bg", highlightbackground="fg_dim")
        self._outer_frame = outer

        self._build_title_bar(outer, _reg)
        self._build_clock_row(outer, _reg)
        if self._project_mgr is not None:
            self._configure_ttk_styles()
            self._build_project_frame(outer, _reg)
            self._build_tree_panel(outer, _reg)
        self._build_button_row(outer, _reg)

        # Bind dragging to the outer frame background so most of the
        # window surface is draggable (like the POC's main_frame binding).
        outer.bind("<Button-1>", self._drag_start)
        outer.bind("<B1-Motion>", self._drag_motion)

    def _build_title_bar(self, outer: tk.Frame, _reg: Callable[..., None]) -> None:
        """Build the title bar row (icon, title, env badge, settings, close,
        minimize).
        """
        t = self._theme

        title_bar = tk.Frame(outer, bg=t.bg, height=28)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        _reg(title_bar, bg="bg")

        self._title_icon_label = tk.Label(
            title_bar,
            text="⏰",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 10, "bold"),
        )
        self._title_icon_label.pack(side="left", padx=(6, 1))
        _reg(
            self._title_icon_label, bg="bg"
        )  # fg intentionally excluded — project color owns it

        self._title_label = tk.Label(
            title_bar,
            text="Tick-Tock Project Timer",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 10, "bold"),
        )
        self._title_label.pack(side="left", padx=(0, 6))
        _reg(self._title_label, bg="bg", fg="fg_dim")

        # Environment indicator (shown for non-production environments)
        if self._config is not None and self._config.environment != Environment.PROD:
            env_labels = {
                Environment.DEV: " [DEV]",
                Environment.TEST: " [TEST]",
                Environment.PROTOTYPE: " [PROTOTYPE]",
            }
            env_text = env_labels.get(
                self._config.environment,
                f" [{self._config.environment.value.upper()}]",
            )
            env_lbl = tk.Label(
                title_bar,
                text=env_text,
                bg=t.bg,
                fg=t.stopped_color,
                font=("Arial", 8, "bold"),
            )
            env_lbl.pack(side="left")
            _reg(env_lbl, bg="bg", fg="stopped_color")

        close_btn = tk.Button(
            title_bar,
            text="✕",
            bg=t.close_bg,
            fg=t.close_fg,
            font=("Arial", 10, "bold"),
            bd=0,
            width=2,
            command=self.close,
        )
        close_btn.pack(side="right", padx=2, pady=2)
        _reg(close_btn, bg="close_bg", fg="close_fg", activebackground="close_bg")

        minimize_btn = tk.Button(
            title_bar,
            text="−",
            bg=t.btn_bg,
            fg=t.fg_dim,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            font=("Arial", 10, "bold"),
            bd=0,
            width=2,
            command=self._minimize,
        )
        minimize_btn.pack(side="right", padx=1, pady=2)
        _reg(
            minimize_btn,
            bg="btn_bg",
            fg="fg_dim",
            activebackground="btn_active",
            activeforeground="fg",
        )

        settings_btn = tk.Button(
            title_bar,
            text="⚙",
            bg=t.btn_bg,
            fg=t.fg_dim,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            font=("Arial", 10),
            bd=0,
            width=2,
            command=self._open_settings_dialog,
        )
        settings_btn.pack(side="right", padx=1, pady=2)
        _reg(
            settings_btn,
            bg="btn_bg",
            fg="fg_dim",
            activebackground="btn_active",
            activeforeground="fg",
        )

        title_bar.bind("<Button-1>", self._drag_start)
        title_bar.bind("<B1-Motion>", self._drag_motion)
        self._title_icon_label.bind("<Button-1>", self._drag_start)
        self._title_icon_label.bind("<B1-Motion>", self._drag_motion)
        self._title_label.bind("<Button-1>", self._drag_start)
        self._title_label.bind("<B1-Motion>", self._drag_motion)

    def _build_clock_row(self, outer: tk.Frame, _reg: Callable[..., None]) -> None:
        """Build the wall-clock / date row."""
        t = self._theme

        clock_row = tk.Frame(outer, bg=t.bg)
        clock_row.pack(fill="x", padx=8, pady=(4, 2))
        _reg(clock_row, bg="bg")

        self._time_label = tk.Label(
            clock_row,
            text="00:00:00",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Consolas", 12),
        )
        self._time_label.pack(side="left")
        _reg(self._time_label, bg="bg", fg="fg_dim")

        self._date_label = tk.Label(
            clock_row,
            text="01/01/2000",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Consolas", 12),
        )
        self._date_label.pack(side="right")
        _reg(self._date_label, bg="bg", fg="fg_dim")

        for w in (self._time_label, self._date_label):
            w.bind("<Button-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_motion)

    def _build_project_frame(self, outer: tk.Frame, _reg: Callable[..., None]) -> None:
        """Build the 'Current Project' section (combobox, buttons, today total).

        Pre-condition: ``self._project_mgr is not None``.
        """
        t = self._theme

        project_frame = tk.LabelFrame(
            outer,
            text="Current Project",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 8, "bold"),
            padx=4,
            pady=2,
        )
        project_frame.pack(fill="x", padx=6, pady=(4, 2))
        _reg(project_frame, bg="bg", fg="fg_dim")

        # ---- selector row: ● swatch + combobox + button stack ----
        selector_row = tk.Frame(project_frame, bg=t.bg)
        selector_row.pack(fill="x")
        _reg(selector_row, bg="bg")

        project_lbl = tk.Label(
            selector_row,
            text="Project:",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 9),
        )
        project_lbl.pack(side="left", padx=(2, 4))
        _reg(project_lbl, bg="bg", fg="fg_dim")

        self._project_combobox = ttk.Combobox(
            selector_row,
            font=("Arial", 9),
            state="readonly",
            width=16,
            style="Project.TCombobox",
            postcommand=lambda: self._style_combobox_popup(self._project_combobox),
        )
        self._project_combobox.pack(side="left", fill="x", expand=True, padx=(2, 4))
        self._project_combobox.bind(
            "<<ComboboxSelected>>", self._on_combobox_project_select
        )

        # Button stack on the right side of the selector row
        btn_stack = tk.Frame(selector_row, bg=t.bg)
        btn_stack.pack(side="right")
        _reg(btn_stack, bg="bg")

        manage_btn = tk.Button(
            btn_stack,
            text="\U0001f4ca Manage",
            bg=t.btn_bg,
            fg=t.fg_dim,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            font=("Arial", 8),
            width=8,
            bd=1,
            relief="raised",
            command=self._open_project_dialog,
        )
        manage_btn.pack(pady=1)
        _reg(
            manage_btn,
            bg="btn_bg",
            fg="fg_dim",
            activebackground="btn_active",
            activeforeground="fg",
        )

        self._report_btn = tk.Button(
            btn_stack,
            text="\U0001f4c8 Report",
            bg=t.btn_bg,
            fg=t.fg_dim,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            font=("Arial", 8),
            width=8,
            bd=1,
            relief="raised",
            command=self._open_report_dialog,
        )
        self._report_btn.pack(pady=1)
        _reg(
            self._report_btn,
            bg="btn_bg",
            fg="fg_dim",
            activebackground="btn_active",
            activeforeground="fg",
        )

        # ---- Total Today row inside the project frame ------------
        today_inner = tk.Frame(project_frame, bg=t.bg)
        today_inner.pack(fill="x", pady=(2, 0))
        _reg(today_inner, bg="bg")
        today_prefix = tk.Label(
            today_inner,
            text="Total Today:",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 9),
        )
        today_prefix.pack(side="left")
        _reg(today_prefix, bg="bg", fg="fg_dim")
        self._today_label = tk.Label(
            today_inner,
            text="00:00:00",
            bg=t.bg,
            fg=t.running_color,
            font=("Consolas", 11, "bold"),
        )
        self._today_label.pack(side="left", padx=(5, 0))
        _reg(self._today_label, bg="bg", fg="running_color")

    def _build_tree_panel(self, outer: tk.Frame, _reg: Callable[..., None]) -> None:
        """Build the tabbed sub-activities / projects treeview panel.

        Pre-condition: ``self._project_mgr is not None``.
        """
        t = self._theme

        panel_outer = tk.LabelFrame(
            outer,
            bg=t.bg,
            fg=t.fg_dim,
            padx=4,
            pady=2,
        )
        panel_outer.pack(fill="both", expand=True, padx=6, pady=(4, 2))
        _reg(panel_outer, bg="bg", fg="fg_dim")
        self._panel_outer = panel_outer

        # Tab labels embedded in the LabelFrame border via labelwidget=
        tab_label_frame = tk.Frame(panel_outer, bg=t.bg)
        _reg(tab_label_frame, bg="bg")

        self._tab_proj_lbl = tk.Label(
            tab_label_frame,
            text="Projects",
            bg=t.bg,
            fg=t.fg_dim,  # inactive tab — dim
            font=("Arial", 8, "bold"),
            cursor="hand2",
            padx=3,
        )
        self._tab_proj_lbl.pack(side="left")
        self._tab_proj_lbl.bind(
            "<Button-1>", lambda _e: self._on_panel_tab_click("projects")
        )
        _reg(self._tab_proj_lbl, bg="bg")  # fg handled by _switch_panel_tab

        self._tab_sub_lbl = tk.Label(
            tab_label_frame,
            text="Sub-Activities",
            bg=t.bg,
            fg=t.fg,  # active tab — full brightness
            font=("Arial", 8, "bold"),
            cursor="hand2",
            padx=3,
        )
        self._tab_sub_lbl.pack(side="left")
        self._tab_sub_lbl.bind(
            "<Button-1>", lambda _e: self._on_panel_tab_click("sub_activities")
        )
        _reg(self._tab_sub_lbl, bg="bg")  # fg handled by _switch_panel_tab

        panel_outer.configure(labelwidget=tab_label_frame)
        self._panel_outer = panel_outer

        # ---- Sub-activities panel (shown by default) ----
        self._sub_activities_frame = tk.Frame(panel_outer, bg=t.bg)
        self._sub_activities_frame.pack(fill="both", expand=True)
        _reg(self._sub_activities_frame, bg="bg")

        tree_container = tk.Frame(self._sub_activities_frame, bg=t.bg)
        tree_container.pack(fill="both", expand=True)
        _reg(tree_container, bg="bg")

        self._tree = ttk.Treeview(
            tree_container,
            columns=("name", "elapsed", "action"),
            style="Matrix.Treeview",
            height=6,
            selectmode="browse",
            show="",
        )
        self._tree.column("name", width=200, anchor="w", stretch=True, minwidth=150)
        self._tree.column("elapsed", width=80, anchor="e", stretch=False, minwidth=70)
        self._tree.column(
            "action", width=90, anchor="center", stretch=False, minwidth=80
        )

        tree_scroll = ttk.Scrollbar(
            tree_container,
            orient="vertical",
            command=self._tree.yview,  # pyright: ignore
            style="Matrix.Vertical.TScrollbar",
        )
        self._tree.configure(yscrollcommand=tree_scroll.set)
        self._tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self._tree.bind("<Double-1>", self._on_tree_double_click)
        self._tree.bind("<Button-1>", self._on_tree_click)

        # ---- Projects panel (hidden initially) ----
        self._projects_frame = tk.Frame(panel_outer, bg=t.bg)
        _reg(self._projects_frame, bg="bg")

        proj_tree_container = tk.Frame(self._projects_frame, bg=t.bg)
        proj_tree_container.pack(fill="both", expand=True)
        _reg(proj_tree_container, bg="bg")

        self._projects_tree = ttk.Treeview(
            proj_tree_container,
            columns=("name", "elapsed", "action"),
            style="Matrix.Treeview",
            height=6,
            selectmode="browse",
            show="",
        )
        self._projects_tree.column(
            "name", width=200, anchor="w", stretch=True, minwidth=150
        )
        self._projects_tree.column(
            "elapsed", width=80, anchor="e", stretch=False, minwidth=70
        )
        self._projects_tree.column(
            "action", width=90, anchor="center", stretch=False, minwidth=80
        )

        proj_scroll = ttk.Scrollbar(
            proj_tree_container,
            orient="vertical",
            command=self._projects_tree.yview,  # pyright: ignore
            style="Matrix.Vertical.TScrollbar",
        )
        self._projects_tree.configure(yscrollcommand=proj_scroll.set)
        self._projects_tree.pack(side="left", fill="both", expand=True)
        proj_scroll.pack(side="right", fill="y")
        self._projects_tree.bind("<Button-1>", self._on_projects_tree_click)

    def _build_button_row(self, outer: tk.Frame, _reg: Callable[..., None]) -> None:
        """Build the bottom control row (start/stop button and opacity slider)."""
        t = self._theme

        btn_row = tk.Frame(outer, bg=t.bg)
        btn_row.pack(fill="x", padx=5, pady=5, side="bottom")
        _reg(btn_row, bg="bg")

        self._toggle_btn = tk.Button(
            btn_row,
            text="▶️ Start",
            bg=t.btn_bg,
            fg=t.btn_fg,
            activebackground=t.btn_active,
            activeforeground=t.btn_fg,
            font=("Arial", 10, "bold"),
            width=12,
            bd=2,
            relief="raised",
            command=self._on_toggle,
        )
        self._toggle_btn.pack(side="left", padx=2)

        # ---- Opacity control (right side of btn_row) -----------------
        init_opacity = (
            float(self._config.get_ui_pref("opacity", 0.90))
            if self._config is not None
            else 0.90
        )
        self._opacity_var = tk.DoubleVar(value=init_opacity)
        opacity_scale = tk.Scale(
            btn_row,
            from_=0.3,
            to=1.0,
            resolution=0.1,
            orient="horizontal",
            variable=self._opacity_var,
            command=self._on_opacity_change,
            bg=t.bg,
            fg=t.fg_dim,
            highlightbackground=t.bg,
            troughcolor=t.btn_bg,
            activebackground=t.btn_active,
            length=90,
            width=10,
            showvalue=False,
        )
        opacity_scale.pack(side="right")
        _reg(
            opacity_scale,
            bg="bg",
            fg="fg_dim",
            highlightbackground="bg",
            troughcolor="btn_bg",
            activebackground="btn_active",
        )

    # ------------------------------------------------------------------
    # TTk style configuration
    # ------------------------------------------------------------------

    def _configure_ttk_styles(self) -> None:
        """Apply current theme colors to all ttk widget styles."""
        t = self._theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Project.TCombobox",
            fieldbackground=t.bg,
            background=t.bg,
            foreground=t.fg,
            arrowcolor=t.fg_dim,
            selectbackground=t.bg,
            selectforeground=t.fg,
        )
        style.map(
            "Project.TCombobox",
            fieldbackground=[("readonly", t.bg), ("active", t.bg)],
            foreground=[("readonly", t.fg), ("active", t.fg)],
            selectbackground=[("readonly", t.bg), ("active", t.bg)],
            selectforeground=[("readonly", t.fg), ("active", t.fg)],
            background=[("readonly", t.bg), ("active", t.bg)],
        )
        # Style the dropdown listbox popup (background, text, and selection colors)
        if self._root is not None:
            self._root.option_add(  # pyright: ignore
                "*TCombobox*Listbox.background", t.bg
            )
            self._root.option_add(  # pyright: ignore
                "*TCombobox*Listbox.foreground", t.fg
            )
            self._root.option_add(  # pyright: ignore
                "*TCombobox*Listbox.selectBackground", t.sel_bg
            )
            self._root.option_add(  # pyright: ignore
                "*TCombobox*Listbox.selectForeground", t.fg
            )
        style.configure(
            "Matrix.Treeview",
            background=t.entry_bg,
            fieldbackground=t.entry_bg,
            foreground=t.fg_dim,
            rowheight=20,
        )
        style.map(
            "Matrix.Treeview",
            background=[("selected", t.sel_bg)],
            foreground=[("selected", t.fg)],
        )
        style.configure(
            "Matrix.Treeview.Heading",
            background=t.btn_bg,
            foreground=t.fg_dim,
            font=("Arial", 8),
        )
        style.configure(
            "Matrix.Vertical.TScrollbar",
            background=t.btn_bg,
            troughcolor=t.entry_bg,
            arrowcolor=t.fg_dim,
            darkcolor=t.btn_bg,
            lightcolor=t.btn_bg,
            bordercolor=t.bg,
            relief="flat",
        )
        style.map(
            "Matrix.Vertical.TScrollbar",
            background=[("active", t.sel_bg), ("pressed", t.sel_bg)],
            arrowcolor=[("active", t.fg), ("pressed", t.fg)],
        )
        # Combobox popdowns use base ttk scrollbar styles on Windows.
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
    # Theme application
    # ------------------------------------------------------------------

    def apply_theme(self, new_theme: Theme) -> None:
        """Switch to *new_theme*, re-coloring all widgets immediately.

        Called either on startup (from :meth:`_check_config_theme`) or
        whenever the user applies a new selection in :class:`SettingsDialog`.
        """
        self._theme = new_theme
        root = self._root
        if root is None:
            return
        root.configure(bg=new_theme.bg)

        # Re-apply all registered widget color attributes
        for widget, attr, role in self._theme_refs:
            try:
                widget.configure(**{attr: getattr(new_theme, role)})
            except tk.TclError:
                pass

        # Update ttk styles (combobox + treeview)
        self._configure_ttk_styles()

        # Rebuild tree so tag colors take effect
        self._rebuild_tree()
        self._rebuild_projects_tree()

        # Re-apply tab label fg based on which tab is active
        if self._tab_sub_lbl is not None:
            self._tab_sub_lbl.config(
                fg=(
                    new_theme.fg
                    if self._panel_tab == "sub_activities"
                    else new_theme.fg_dim
                )
            )
        if self._tab_proj_lbl is not None:
            self._tab_proj_lbl.config(
                fg=new_theme.fg if self._panel_tab == "projects" else new_theme.fg_dim
            )

        # Update color swatch for active project
        self._update_project_combobox()

        # Refresh dynamic timer-state colors
        self._apply_timer_display()

    # ------------------------------------------------------------------
    # Window close / tray hide
    # ------------------------------------------------------------------

    def _on_window_close_request(self) -> None:
        """Handle close button, Alt+F4, and Escape.

        Hides to the system tray when the tray icon is running so the app
        keeps tracking time in the background.  Falls back to a full close
        when the tray is unavailable.
        """
        if self._tray is not None and self._tray.is_running():
            self._hide_to_tray()
        else:
            self.close()

    def _hide_to_tray(self) -> None:
        """Hide both the main window and the compact mini-widget to the tray."""
        if self._minimized_widget is not None:
            self._minimized_widget.destroy()
            self._minimized_widget = None
        if self._root is not None:
            self._save_window_state()
            self._root.withdraw()

    def _show_from_tray(self) -> None:
        """Restore the main window from the system tray."""
        if self._root is not None:
            self._root.deiconify()
            self._root.focus_force()

    def _tray_toggle_visibility(self) -> None:
        """Toggle visibility — called from the pystray background thread."""
        self._post_ui(self._toggle_tray_visibility)

    def _toggle_tray_visibility(self) -> None:
        """Main-thread handler: show if hidden, hide if visible."""
        if self._root is None:
            return
        if self._root.state() == "withdrawn":
            self._show_from_tray()
        else:
            self._hide_to_tray()

    def _tray_quit(self) -> None:
        """Quit the application — called from the pystray background thread."""
        self._post_ui(self.close)

    # ------------------------------------------------------------------
    # Minimize / restore (compact mode)
    # ------------------------------------------------------------------

    def _minimize(self) -> None:
        """Hide the main window and show the compact mini widget."""
        root = self._root
        if root is None:
            return
        x = root.winfo_x()
        y = root.winfo_y()
        root.withdraw()
        self._minimized_widget = MinimizedWidget(
            parent=root,
            timer=self._timer,
            project_mgr=self._project_mgr,
            storage=self._storage,
            theme=self._theme,
            on_toggle=self._on_toggle,
            on_project_switch=self._on_project_switch,
            on_sub_switch=self._on_tree_select_sub_activity,
            on_maximize=self._restore,
            active_sub_id_getter=lambda: self._active_sub_activity_id,
            start_x=x,
            start_y=y,
        )

    def _restore(self, x: int, y: int) -> None:
        """Called by the mini widget maximize button: show the main window."""
        self._minimized_widget = None
        root = self._root
        if root is None:
            return
        root.geometry(f"+{x}+{y}")
        root.deiconify()
        root.focus_force()
        # Refresh UI to reflect any changes made while minimized.
        self._apply_timer_display()
        self._update_project_selector()

    # ------------------------------------------------------------------
    # Timer settings helpers
    # ------------------------------------------------------------------

    def _get_date_fmt(self) -> str:
        """Return strftime format string for the configured date format."""
        if self._config is None:
            return "%d/%m/%Y"
        setting = self._config.get_timer_setting("date_format", "DD/MM/YYYY")
        return {
            "DD/MM/YYYY": "%d/%m/%Y",
            "MM/DD/YYYY": "%m/%d/%Y",
            "YYYY-MM-DD": "%Y-%m-%d",
        }.get(str(setting), "%d/%m/%Y")

    def _get_time_fmt(self) -> str:
        """Return strftime format string for the configured time format."""
        if self._config is None:
            return "%H:%M:%S"
        setting = self._config.get_timer_setting("time_format", "24h")
        return "%I:%M:%S %p" if str(setting) == "12h" else "%H:%M:%S"

    # ------------------------------------------------------------------
    # Window title / position helpers
    # ------------------------------------------------------------------

    def _get_window_title_text(self) -> str:
        """Return the title bar text, including env suffix for non-production."""
        base = "⏰ Tick-Tock"
        if self._config is not None and self._config.environment != Environment.PROD:
            labels = {
                Environment.DEV: "DEV",
                Environment.TEST: "TEST",
                Environment.PROTOTYPE: "PROTO",
            }
            suffix = labels.get(
                self._config.environment, self._config.environment.value.upper()
            )
            return f"{base}  [{suffix}]"
        return base

    @staticmethod
    def _get_virtual_screen_bounds(root: tk.Tk) -> tuple[int, int, int, int]:
        """Return (x, y, width, height) for the full virtual desktop."""
        if sys.platform == "win32":
            try:
                user32 = ctypes.windll.user32
                x = int(user32.GetSystemMetrics(76))  # SM_XVIRTUALSCREEN
                y = int(user32.GetSystemMetrics(77))  # SM_YVIRTUALSCREEN
                w = int(user32.GetSystemMetrics(78))  # SM_CXVIRTUALSCREEN
                h = int(user32.GetSystemMetrics(79))  # SM_CYVIRTUALSCREEN
                if w > 0 and h > 0:
                    return x, y, w, h
            except Exception:  # pylint: disable=broad-except
                pass
        try:
            x = int(root.winfo_vrootx())
            y = int(root.winfo_vrooty())
            w = int(root.winfo_vrootwidth())
            h = int(root.winfo_vrootheight())
            if w > 0 and h > 0:
                return x, y, w, h
        except tk.TclError:
            pass
        return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()

    @staticmethod
    def _validate_window_position(
        x: int,
        y: int,
        w: int,
        _h: int,
        screen_x: int,
        screen_y: int,
        screen_w: int,
        screen_h: int,
    ) -> tuple[int, int]:
        """Clamp *x*, *y* so at least 50 px of the title bar remains on-screen."""
        margin = 50
        x = max(screen_x + margin - w, min(x, screen_x + screen_w - margin))
        y = max(screen_y, min(y, screen_y + screen_h - margin))
        return x, y

    def _save_window_state(self) -> None:
        """Persist window position and UI preferences to config."""
        if self._config is None or self._root is None:
            return
        try:
            self._config.set_ui_pref("window_x", self._root.winfo_x())
            self._config.set_ui_pref("window_y", self._root.winfo_y())
            if self._always_on_top_var is not None:
                self._config.set_ui_pref("always_on_top", self._always_on_top_var.get())
            self._config.save()
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Could not persist window state: %s", exc)

    # ------------------------------------------------------------------
    # Export / Import
    # ------------------------------------------------------------------

    def _export_data(self) -> None:
        """Open a file dialog and export all data to a JSON file."""
        root = self._root
        if root is None:
            return
        if self._storage is None:
            messagebox.showinfo("Export", "No storage available.", parent=root)
            return
        path_str = filedialog.asksaveasfilename(
            parent=root,
            title="Export Tick-Tock Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="tick_tock_export.json",
        )
        if not path_str:
            return

        try:
            if self._app_service is None:
                return
            export_data(
                export_path=Path(path_str),
                app_service=self._app_service,
                timer=self._timer,
                controller=self._controller,
            )
            messagebox.showinfo(
                "Export Complete",
                f"Data exported to:\n{path_str}",
                parent=root,
            )
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror(
                "Export Failed",
                f"Could not export data:\n{exc}",
                parent=root,
            )

    def _import_data(self) -> None:
        """Open a file dialog, import data, then reload the UI."""
        root = self._root
        if root is None:
            return
        if self._storage is None:
            messagebox.showinfo("Import", "No storage available.", parent=root)
            return
        confirmed = messagebox.askyesno(
            "Import Data",
            "Importing will replace all current projects and time data.\n"
            "A backup will be made first.\n\nContinue?",
            parent=root,
        )
        if not confirmed:
            return
        path_str = filedialog.askopenfilename(
            parent=root,
            title="Import Tick-Tock Data",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path_str:
            return

        try:
            if self._app_service is None:
                return
            import_data(
                import_path=Path(path_str),
                app_service=self._app_service,
                project_manager=self._project_mgr,
                timer=self._timer,
                controller=self._controller,
                load_sub_activities_for_project=self._load_sub_activities_for_project,
                update_project_selector=self._update_project_selector,
                refresh_today_base_total=self._refresh_today_base_total,
                apply_timer_display=self._apply_timer_display,
            )
            messagebox.showinfo(
                "Import Complete",
                f"Data imported from:\n{path_str}",
                parent=root,
            )
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror(
                "Import Failed",
                f"Could not import data:\n{exc}",
                parent=root,
            )

    # ------------------------------------------------------------------
    # DragMixin protocol
    # ------------------------------------------------------------------

    def _get_drag_window(self) -> Optional[tk.Tk]:
        return self._root

    # ------------------------------------------------------------------
    # Dragging
    # ------------------------------------------------------------------

    def _setup_dragging(self) -> None:
        """Drag events are bound to outer frame and key labels in _create_widgets."""

    # ------------------------------------------------------------------
    # Real-time clock
    # ------------------------------------------------------------------

    def _update_tray_tooltip(self) -> None:
        """Refresh the system tray tooltip to reflect current project/time."""
        if self._tray is None or not self._tray.is_running():
            return
        state = self._timer.state
        if state == TimerState.RUNNING:
            project_name = "Unknown"
            if self._project_mgr is not None:
                active = self._project_mgr.active_project
                if active is not None:
                    project_name = active.name
            elapsed = format_elapsed(self._timer.elapsed, pad_hours=True)
            self._tray.update_tooltip(f"Tick-Tock | {project_name} | {elapsed}")
        elif state == TimerState.PAUSED:
            self._tray.update_tooltip("Tick-Tock | Paused")
        else:
            self._tray.update_tooltip("Tick-Tock | Idle")

    def _start_clock(self) -> None:
        self._tick_clock()

    # Wall-clock jump (seconds) that indicates a system sleep/wake event.
    _SLEEP_DETECT_THRESHOLD = 5.0

    def _tick_clock(self) -> None:
        root = self._root
        if root is None:
            return
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        # Sleep/wake detection: if the wall clock jumped more than the
        # threshold between two consecutive ticks the system likely slept.
        if self._last_tick_wall_time is not None:
            gap = (now - self._last_tick_wall_time).total_seconds()
            if (
                gap > self._SLEEP_DETECT_THRESHOLD
                and self._timer.state == TimerState.RUNNING
            ):
                logger.info(
                    "System sleep/wake detected (gap %.1fs) — pausing timer.", gap
                )
                # Preserve elapsed at the last known active value so a long
                # suspend gap is never counted as worked time.
                self._timer.pause(preserve_elapsed=True)
        self._last_tick_wall_time = now

        # Handle midnight date change while timer is running
        if self._timer.state == TimerState.RUNNING:
            self._controller.handle_midnight_rollover(self._timer.elapsed, today)

        if self._time_label:
            self._time_label.config(text=now.strftime(self._get_time_fmt()))
        if self._date_label:
            self._date_label.config(text=now.strftime(self._get_date_fmt()))
        if self._timer.state == TimerState.RUNNING:
            self._refresh_elapsed()
        self._update_today_label()
        self._update_tree_active_time()
        self._update_projects_tree_times()
        self._update_tray_tooltip()
        self._clock_job = root.after(1000, self._tick_clock)

    # ------------------------------------------------------------------
    # Timer control handlers
    # ------------------------------------------------------------------

    def _on_toggle(self) -> None:
        state = self._timer.state
        if state == TimerState.RUNNING:
            self._timer.stop()
        elif state == TimerState.PAUSED:
            self._timer.resume()
        elif state == TimerState.STOPPED:
            # Continue from existing elapsed — do NOT reset to zero.
            self._timer.continue_from_stopped()
        else:  # IDLE
            self._timer.start()

    # ------------------------------------------------------------------
    # Project management
    # ------------------------------------------------------------------

    def _on_project_switch(self, new_id: int) -> None:
        """Save current project's elapsed, switch active project, restore timer."""
        if self._project_mgr is None:
            return
        active = self._project_mgr.active_project
        if active is not None and active.project_id == new_id:
            # Allow callers (e.g. mini widget) to switch from a selected
            # sub-activity back to project-level tracking in the same project.
            if self._active_sub_activity_id is not None:
                self._on_tree_select_project(new_id)
            return

        switch_active_project_session(
            new_id=new_id,
            project_manager=self._project_mgr,
            app_service=self._app_service,
            timer=self._timer,
            controller=self._controller,
            load_sub_activities_for_project=self._load_sub_activities_for_project,
        )

        # Ensure the newly activated project is expanded in the tree.
        self._tree_expanded_ids.add(new_id)
        self._save_tree_expanded_state()
        self._refresh_today_base_total(force=True)
        self._apply_timer_display()
        self._update_project_selector()
        if self._minimized_widget is not None:
            self._minimized_widget.refresh_combos()

    def _open_report_dialog(self) -> None:
        if self._root is None or self._storage is None or self._project_mgr is None:
            return
        MonthlyReportDialog(
            self._root,
            storage=self._storage,
            project_mgr=self._project_mgr,
            theme=self._theme,
            live_segment_getter=self._get_live_daily_segment,
            active_sub_id_getter=lambda: self._active_sub_activity_id,
        )

    def _open_project_dialog(self) -> None:
        if self._root is None or self._project_mgr is None:
            return
        ProjectManagementDialog(
            self._root,
            self._project_mgr,
            on_projects_changed=self._on_projects_changed,
            storage=self._storage,
            theme=self._theme,
            active_sub_id_getter=lambda: self._active_sub_activity_id,
            live_segment_getter=self._get_live_daily_segment,
            on_before_project_change=self._before_project_change,
            on_before_sub_activity_delete=self._before_sub_activity_delete,
        )

    def _before_project_change(self, project_id: int) -> bool:
        """Prepare timer/session state before deleting or archiving a project."""
        if self._project_mgr is None:
            return True
        active = self._project_mgr.active_project
        if active is None or active.project_id != project_id:
            return True

        fallback = next(
            (
                p.project_id
                for p in self._project_mgr.projects
                if p.project_id != project_id and not p.archived
            ),
            None,
        )

        try:
            if fallback is not None:
                # Switch away from the soon-to-change active project so any
                # in-flight elapsed is persisted to the correct target first.
                self._on_project_switch(fallback)
                return True

            if self._timer.state in (TimerState.RUNNING, TimerState.PAUSED):
                self._timer.stop()
            elif self._timer.state == TimerState.STOPPED:
                self._controller.save_active_elapsed(self._timer.elapsed)

            self._controller.set_switching_project(True)
            self._timer.reset()
            self._controller.set_switching_project(False)
            self._active_sub_activity_id = None
            return True
        except Exception:  # pylint: disable=broad-except
            logger.exception("Failed to prepare active project transition")
            self._controller.set_switching_project(False)
            return False

    def _before_sub_activity_delete(
        self, project_id: int, sub_activity_id: int
    ) -> bool:
        """Prepare timer/session state before deleting a sub-activity target."""
        if self._project_mgr is None:
            return True
        active = self._project_mgr.active_project
        if active is None or active.project_id != project_id:
            return True
        if self._active_sub_activity_id != sub_activity_id:
            return True

        try:
            switch_within_project_target_session(
                timer=self._timer,
                controller=self._controller,
                app_service=self._app_service,
                apply_target=lambda: setattr(self, "_active_sub_activity_id", None),
                target_elapsed_seconds=active.elapsed_seconds,
            )
            self._refresh_after_target_transition()
            return True
        except Exception:  # pylint: disable=broad-except
            logger.exception("Failed to prepare active sub-activity deletion")
            return False

    def _get_live_daily_segment(self) -> tuple[Optional[int], float]:
        """Return live, not-yet-flushed segment as ``(project_id, delta_seconds)``."""
        if self._project_mgr is None:
            return None, 0.0
        if self._timer.state != TimerState.RUNNING:
            return None, 0.0
        active = self._project_mgr.active_project
        if active is None:
            return None, 0.0
        delta = max(
            0.0,
            self._timer.elapsed - self._controller.get_last_saved_daily_elapsed(),
        )
        return active.project_id, delta

    def _open_settings_dialog(self) -> None:
        if self._root is None or self._config is None:
            return
        SettingsDialog(
            self._root,
            self._config,
            current_theme=self._theme,
            on_apply=self.apply_theme,
            current_always_on_top=bool(
                self._always_on_top_var.get()
                if self._always_on_top_var is not None
                else self._config.get_ui_pref("always_on_top", True)
            ),
            on_set_always_on_top=self._set_always_on_top_from_settings,
            on_export=self._export_data,
            on_import=self._import_data,
        )

    def _set_always_on_top_from_settings(self, value: bool) -> None:
        """Apply always-on-top state from Settings dialog."""
        root = self._root
        if root is None:
            return
        root.attributes("-topmost", value)  # pyright: ignore
        if self._always_on_top_var is not None:
            self._always_on_top_var.set(value)

    def _on_projects_changed(self) -> None:
        """Called by the dialog after any CRUD operation."""
        # Reload sub-activities for the (potentially changed) active project.
        if self._project_mgr is not None and self._storage is not None:
            active = self._project_mgr.active_project
            if active is not None:
                self._load_sub_activities_for_project(active.project_id)
        self._update_project_selector()
        # If the active project changed (e.g. deleted), reload its timer.
        if self._project_mgr:
            active = self._project_mgr.active_project
            if active and self._timer.state in (TimerState.IDLE, TimerState.STOPPED):
                target_elapsed = max(0.0, float(active.elapsed_seconds))
                if self._timer.state == TimerState.IDLE:
                    if target_elapsed > 0:
                        self._timer.restore(target_elapsed)
                else:
                    if abs(self._timer.elapsed - target_elapsed) > 1e-6:
                        self._timer.restore(target_elapsed, "stopped")
            self._apply_timer_display()

    def _update_project_selector(self) -> None:
        """Refresh combobox + tree after any project data change."""
        self._update_project_combobox()
        self._rebuild_tree()
        self._rebuild_projects_tree()

    # ------------------------------------------------------------------
    # Storage callbacks (called synchronously from the timer context)
    # ------------------------------------------------------------------

    def _restore_timer_state(self) -> None:
        """Load saved timer state on startup."""
        restored = restore_saved_timer_state(
            app_service=self._app_service,
            storage=self._storage,
            timer=self._timer,
            controller=self._controller,
        )
        if restored and self._timer.elapsed > 0:
            self._refresh_elapsed()

        if self._project_mgr is not None:
            active = self._project_mgr.active_project
            # Load persisted tree expanded state from config
            if self._config is not None:
                raw = self._config.get_ui_pref("tree_expanded_projects", None)
                if isinstance(raw, list):
                    self._tree_expanded_ids = {
                        int(x)
                        for x in cast(list[Any], raw)
                        if isinstance(x, (int, float))
                    }
                if self._config.get_ui_pref("panel_collapsed", False):
                    self._set_panel_collapsed(True)
            # Default: expand the active project if nothing was saved
            if not self._tree_expanded_ids and active is not None:
                self._tree_expanded_ids = {active.project_id}
            if not restored and active is not None and active.elapsed_seconds > 0:
                self._timer.restore(active.elapsed_seconds)
                self._refresh_elapsed()
            self._update_project_combobox()
            self._rebuild_tree()
            return
        # Fallback when no project manager is available.
        return

    # ------------------------------------------------------------------
    # Sub-activity support
    # ------------------------------------------------------------------

    def _load_sub_activities_for_project(self, project_id: int) -> None:
        """Load sub-activities for *project_id* and clear the active sub-activity."""
        if self._app_service is not None:
            self._sub_activity_mgr = self._app_service.create_sub_manager(project_id)
        elif self._storage is not None:
            self._sub_activity_mgr = SubActivityManager(self._storage, project_id)
        self._active_sub_activity_id = None

    def _rebuild_tree(self) -> None:
        """Rebuild the flat sub-activity list for the active project."""
        tree = self._tree
        if tree is None or self._project_mgr is None:
            return

        for iid in tree.get_children():
            tree.delete(iid)
        self._tree_node_map.clear()
        self._sub_tree_iids.clear()

        active_project = self._project_mgr.active_project
        if active_project is None:
            return

        rows = build_sub_activity_tree_rows(
            sub_rows=(
                self._app_service.list_sub_activities(active_project.project_id)
                if self._app_service is not None
                else []
            ),
            project_id=active_project.project_id,
            active_sub_activity_id=self._active_sub_activity_id,
            timer_state=self._timer.state,
        )

        for row in rows:
            sa_iid = tree.insert(
                "",
                "end",
                values=(
                    row.name,
                    format_elapsed(row.elapsed_seconds, pad_hours=True),
                    row.action,
                ),
                tags=(row.tag,),
            )
            self._tree_node_map[sa_iid] = TreeNodeEntry(  # pyright: ignore
                kind="sub",
                node_id=row.sub_activity_id,
                project_id=row.project_id,
            )
            self._sub_tree_iids[row.sub_activity_id] = sa_iid

        tree.tag_configure("sub", foreground=self._theme.fg_dim)
        tree.tag_configure(
            "active_sub",
            foreground=self._theme.fg,
            background=self._theme.sel_bg,
        )

    def _on_panel_tab_click(self, tab: str) -> None:
        """Click on a tab: collapse if already active, otherwise switch to it."""
        collapse_value, switch_tab = resolve_panel_tab_click(
            clicked_tab=tab,
            current_tab=self._panel_tab,
            panel_collapsed=self._panel_collapsed,
        )
        if collapse_value is not None:
            self._set_panel_collapsed(collapse_value)
        if switch_tab is not None:
            self._switch_panel_tab(switch_tab)

    def _set_panel_collapsed(self, collapsed: bool) -> None:
        """Hide or show the tree panel content and resize the window accordingly."""
        root = self._root
        if root is None or self._panel_outer is None:
            return
        # Capture current position before changing layout so resize keeps
        # the exact on-screen anchor chosen by the user.
        root.update_idletasks()
        anchor_x = root.winfo_x()
        anchor_y = root.winfo_y()
        self._panel_collapsed = collapsed
        if collapsed:
            # Hide content frames — keep the LabelFrame so tab labels stay visible
            if self._sub_activities_frame is not None:
                self._sub_activities_frame.pack_forget()
            if self._projects_frame is not None:
                self._projects_frame.pack_forget()
            # Freeze panel to a slim tabs-only strip so hidden content cannot
            # continue influencing requested size on some Tk/WM combinations.
            self._panel_outer.pack_propagate(False)
            self._panel_outer.configure(height=self._PANEL_COLLAPSED_H)
            # Stop expanding so the thin label-strip doesn't eat vertical space
            self._panel_outer.pack_configure(
                fill="x", expand=False, padx=6, pady=(4, 2)
            )
        else:
            self._panel_outer.configure(height=0)
            self._panel_outer.pack_propagate(True)
            # Let the panel grow again, then restore whichever tab was active
            self._panel_outer.pack_configure(
                fill="both", expand=True, padx=6, pady=(4, 2)
            )
            self._switch_panel_tab(self._panel_tab)
        # Force geometry recalculation before measuring / resizing.
        root.update_idletasks()
        new_h = compute_panel_window_height(
            collapsed=collapsed,
            outer_frame_reqheight=(
                self._outer_frame.winfo_reqheight()
                if self._outer_frame is not None
                else None
            ),
            window_h_projects=self._WINDOW_H_PROJECTS,
            window_h_tree=self._WINDOW_H_TREE,
        )
        root.geometry(f"{self._WINDOW_W}x{new_h}+{anchor_x}+{anchor_y}")
        if self._config is not None:
            self._config.set_ui_pref("panel_collapsed", collapsed)

    def _switch_panel_tab(self, tab: str) -> None:
        """Switch the lower panel between 'sub_activities' and 'projects' views."""
        self._panel_tab = tab
        sub_fg, proj_fg = resolve_panel_tab_label_colors(
            tab=tab,
            fg=self._theme.fg,
            fg_dim=self._theme.fg_dim,
        )
        if tab == "sub_activities":
            if self._projects_frame is not None:
                self._projects_frame.pack_forget()
            if self._sub_activities_frame is not None:
                self._sub_activities_frame.pack(fill="both", expand=True)
        else:  # "projects"
            if self._sub_activities_frame is not None:
                self._sub_activities_frame.pack_forget()
            if self._projects_frame is not None:
                self._projects_frame.pack(fill="both", expand=True)
            self._rebuild_projects_tree()
        if self._tab_sub_lbl is not None:
            self._tab_sub_lbl.config(fg=sub_fg)
        if self._tab_proj_lbl is not None:
            self._tab_proj_lbl.config(fg=proj_fg)

    def _rebuild_projects_tree(self) -> None:
        """Rebuild the projects list tree with all non-archived projects."""
        tree = self._projects_tree
        if tree is None or self._project_mgr is None:
            return

        for iid in tree.get_children():
            tree.delete(iid)
        self._projects_tree_iids.clear()

        active = self._project_mgr.active_project
        rows = build_project_tree_rows(
            projects=self._project_mgr.projects,
            active_project_id=(active.project_id if active is not None else None),
            active_sub_activity_id=self._active_sub_activity_id,
            timer_state=self._timer.state,
            timer_elapsed=self._timer.elapsed,
        )

        for row in rows:
            iid = tree.insert(
                "",
                "end",
                values=(
                    row.label,
                    format_elapsed(row.elapsed_seconds, pad_hours=True),
                    row.action,
                ),
                tags=(row.tag,),
            )
            self._projects_tree_iids[row.project_id] = iid

        tree.tag_configure("proj", foreground=self._theme.fg_dim)
        tree.tag_configure(
            "active_proj",
            foreground=self._theme.fg,
            background=self._theme.sel_bg,
        )

    def _on_projects_tree_click(self, event: "tk.Event[tk.Misc]") -> str:
        """Handle click on the projects tree — action column switches/toggles."""
        tree = self._projects_tree
        if tree is None or self._project_mgr is None:
            return "break"

        active = self._project_mgr.active_project
        action, project_id = resolve_projects_tree_click_action(
            clicked_column=tree.identify_column(event.x),
            clicked_item_iid=tree.identify_row(event.y),
            project_tree_iids=self._projects_tree_iids,
            active_project_id=(active.project_id if active is not None else None),
            active_sub_activity_id=self._active_sub_activity_id,
        )

        if action == "toggle":
            self._on_toggle()
        elif action == "switch" and project_id is not None:
            self._on_project_switch(project_id)

        return "break"

    def _update_projects_tree_times(self) -> None:
        """Live-update the active project row in the projects tree."""
        if self._projects_tree is None or self._project_mgr is None:
            return

        active = self._project_mgr.active_project
        update = resolve_projects_tree_live_update(
            panel_tab=self._panel_tab,
            project_tree_iids=self._projects_tree_iids,
            active_project_id=(active.project_id if active is not None else None),
            timer_state=self._timer.state,
            timer_elapsed=self._timer.elapsed,
        )
        if update is None:
            return

        try:
            self._projects_tree.set(
                update.iid,
                "elapsed",
                format_elapsed(update.elapsed_seconds, pad_hours=True),
            )
            self._projects_tree.set(update.iid, "action", update.action)
        except tk.TclError:
            pass

    def _update_tree_active_time(self) -> None:
        """Update the active sub-activity row's elapsed and action symbol."""
        if self._tree is None:
            return

        update = resolve_sub_activity_tree_live_update(
            sub_tree_iids=self._sub_tree_iids,
            active_sub_activity_id=self._active_sub_activity_id,
            timer_state=self._timer.state,
            timer_elapsed=self._timer.elapsed,
        )
        if update is None:
            return

        try:
            self._tree.set(
                update.iid,
                "elapsed",
                format_elapsed(update.elapsed_seconds, pad_hours=True),
            )
            self._tree.set(update.iid, "action", update.action)
        except tk.TclError:
            pass

    def _update_project_combobox(self) -> None:
        """Refresh combobox values and selection, and the title icon color."""
        if self._project_mgr is None:
            return
        active_project = self._project_mgr.active_project
        selector_state = build_project_selector_state(
            projects=self._project_mgr.projects,
            active_project=active_project,
            fallback_title_color=self._theme.fg_dim,
        )
        if self._project_combobox is not None:
            self._project_combobox.configure(values=selector_state.labels)
            self._project_combobox.set(selector_state.active_label)
        if self._title_icon_label is not None:
            self._title_icon_label.config(fg=selector_state.title_color)

    def _on_combobox_project_select(self, _event: "tk.Event[tk.Misc]") -> None:
        """Handle the user selecting a project from the dropdown combobox."""
        combo = self._project_combobox
        if combo is None or self._project_mgr is None:
            return
        selected_project_id = resolve_selected_project_id(
            selected_label=combo.get(),
            projects=self._project_mgr.projects,
        )
        if selected_project_id is not None:
            self._on_project_switch(selected_project_id)

    def _on_opacity_change(self, value: str) -> None:
        """Adjust window transparency live and persist the preference."""
        root = self._root
        if root is None:
            return
        val = float(value)
        try:
            root.attributes("-alpha", val)  # pyright: ignore
        except tk.TclError:
            pass
        if self._config is not None:
            self._config.set_ui_pref("opacity", val)

    def _on_tree_double_click(self, event: "tk.Event[tk.Misc]") -> None:
        """Handle double-click on a tree item to switch the active tracking target."""
        tree = self._tree
        if tree is None:
            return
        item_iid = tree.identify_row(event.y)
        self._activate_tree_item(item_iid)

    def _on_tree_click(self, event: "tk.Event[tk.Misc]") -> str:
        """Handle single-click — activate tracking when the action column is clicked."""
        tree = self._tree
        if tree is None:
            return "break"
        active_project_id = (
            self._project_mgr.active_project.project_id
            if (
                self._project_mgr is not None
                and self._project_mgr.active_project is not None
            )
            else None
        )
        resolution = resolve_main_tree_click_action(
            clicked_column=tree.identify_column(event.x),
            clicked_item_iid=tree.identify_row(event.y),
            tree_node_map=self._tree_node_map,
            active_project_id=active_project_id,
            active_sub_activity_id=self._active_sub_activity_id,
            timer_state=self._timer.state,
            has_project_manager=(self._project_mgr is not None),
        )
        if resolution.action == "ignore":
            return "break"
        if resolution.action == "toggle":
            self._on_toggle()
            return "break"
        if resolution.action == "select_project" and resolution.project_id is not None:
            # Stop sub-activity and fall back to project timer (POC behaviour).
            self._on_tree_select_project(resolution.project_id)
            return "break"
        if resolution.action == "activate" and resolution.activate_iid is not None:
            self._activate_tree_item(resolution.activate_iid)
            if resolution.auto_toggle:
                self._on_toggle()
        return "break"

    def _activate_tree_item(self, item_iid: str) -> None:
        """Switch the active tracking target to the item identified by *item_iid*."""
        if self._project_mgr is None:
            return
        active = self._project_mgr.active_project
        plan = resolve_tree_item_activation(
            item_iid=item_iid,
            tree_node_map=self._tree_node_map,
            active_project_id=active.project_id if active is not None else None,
            active_sub_activity_id=self._active_sub_activity_id,
        )
        if plan.action == "select_project" and plan.project_id is not None:
            self._on_tree_select_project(plan.project_id)
            return
        if plan.action == "switch_then_select_sub":
            if plan.project_id is not None:
                self._on_project_switch(plan.project_id)
            if plan.sub_activity_id is not None:
                self._on_tree_select_sub_activity(plan.sub_activity_id)
            return
        if plan.action == "select_sub" and plan.sub_activity_id is not None:
            self._on_tree_select_sub_activity(plan.sub_activity_id)

    def _refresh_after_target_transition(self) -> None:
        """Refresh UI state after changing active project/sub target."""
        self._apply_timer_display()
        self._update_project_combobox()
        self._rebuild_tree()
        if self._minimized_widget is not None:
            self._minimized_widget.refresh_combos()

    def _on_tree_select_project(self, project_id: int) -> None:
        """Select a project node: switch to it and clear any active sub-activity."""
        if self._project_mgr is None:
            return
        active = self._project_mgr.active_project
        is_same_project = active is not None and active.project_id == project_id

        if not is_same_project:
            self._on_project_switch(project_id)
            return

        # Same project — switch from sub-activity level back to project level.
        if self._active_sub_activity_id is None:
            return  # already at project level
        project = self._project_mgr.active_project

        switch_within_project_target_session(
            timer=self._timer,
            controller=self._controller,
            app_service=self._app_service,
            apply_target=lambda: setattr(self, "_active_sub_activity_id", None),
            target_elapsed_seconds=(
                project.elapsed_seconds if project is not None else 0.0
            ),
        )
        self._refresh_after_target_transition()

    def _on_tree_select_sub_activity(self, sub_activity_id: int) -> None:
        """Select a sub-activity node: make it the active tracking target."""
        if self._sub_activity_mgr is None:
            return
        sa = self._sub_activity_mgr.get(sub_activity_id)

        switch_within_project_target_session(
            timer=self._timer,
            controller=self._controller,
            app_service=self._app_service,
            apply_target=lambda: setattr(
                self,
                "_active_sub_activity_id",
                sub_activity_id,
            ),
            target_elapsed_seconds=(sa.elapsed_seconds if sa is not None else 0.0),
        )
        self._refresh_after_target_transition()

    # ------------------------------------------------------------------
    # Tree expand/collapse state persistence
    # ------------------------------------------------------------------

    def _save_tree_expanded_state(self) -> None:
        """Persist _tree_expanded_ids to config (written to disk on close)."""
        if self._config is not None:
            self._config.set_ui_pref(
                "tree_expanded_projects", list(self._tree_expanded_ids)
            )

    def _update_today_label(self) -> None:
        """Refresh the 'Today: HH:MM:SS' label with live running total."""
        if self._today_label is None or self._app_service is None:
            return
        active_project_id: Optional[int] = None
        if (
            self._project_mgr is not None
            and self._project_mgr.active_project is not None
        ):
            active_project_id = self._project_mgr.active_project.project_id
        refresh_today_total(
            cache=self._today_cache,
            app_service=self._app_service,
            active_project_id=active_project_id,
        )
        total = compute_today_display_total(
            cache=self._today_cache,
            timer_running=self._timer.state == TimerState.RUNNING,
            timer_elapsed=self._timer.elapsed,
            last_saved_daily_elapsed=self._controller.get_last_saved_daily_elapsed(),
        )
        self._today_label.config(text=format_elapsed(total, pad_hours=True))

    def _refresh_today_base_total(self, *, force: bool = False) -> None:
        """Refresh cached persisted active-project total for today when needed."""
        if self._app_service is None:
            return
        active_project_id: Optional[int] = None
        if (
            self._project_mgr is not None
            and self._project_mgr.active_project is not None
        ):
            active_project_id = self._project_mgr.active_project.project_id
        refresh_today_total(
            cache=self._today_cache,
            app_service=self._app_service,
            active_project_id=active_project_id,
            force=force,
        )

    def _on_daily_flushed(self, date_str: str, project_id: int, delta: float) -> None:
        """Keep cached 'today total' aligned when a daily segment is persisted."""
        _on_daily_flushed_update(
            cache=self._today_cache,
            date_str=date_str,
            project_id=project_id,
            delta=delta,
        )

    # ------------------------------------------------------------------
    # UI state synchronisation
    # ------------------------------------------------------------------

    def _on_timer_event(self, _timer: Timer) -> None:
        """Fired from the timer context — schedule UI update on main thread."""
        self._post_ui(self._apply_timer_display)

    def _start_ui_dispatcher(self) -> None:
        root = self._root
        if root is None:
            return
        if self._ui_pump_job is None:
            self._ui_pump_job = root.after(16, self._drain_ui_queue)

    def _post_ui(self, fn: Callable[[], None]) -> None:
        """Thread-safe UI dispatch; executes immediately on main thread."""
        if threading.get_ident() == self._main_thread_id:
            fn()
            return
        self._ui_queue.put(fn)

    def _drain_ui_queue(self) -> None:
        root = self._root
        if root is None:
            self._ui_pump_job = None
            return
        processed = 0
        while processed < 100:
            try:
                fn = self._ui_queue.get_nowait()
            except Empty:
                break
            try:
                fn()
            except Exception:  # pylint: disable=broad-except
                logger.exception("UI-dispatch callback failed")
            processed += 1
        self._ui_pump_job = root.after(16, self._drain_ui_queue)

    def _refresh_elapsed(self) -> None:
        if self._elapsed_label:
            self._elapsed_label.config(
                text=format_elapsed(self._timer.elapsed, pad_hours=True)
            )

    def _apply_timer_display(self) -> None:
        """Update all UI elements to reflect current timer state (main thread)."""
        if self._root is None:
            return
        t = self._theme
        state = self._timer.state
        self._refresh_elapsed()

        # --- State indicator dot and elapsed label colour ---
        if self._elapsed_label:
            if state == TimerState.RUNNING:
                self._elapsed_label.config(fg=t.running_color)
            elif state == TimerState.PAUSED:
                self._elapsed_label.config(fg=t.paused_color)
            elif state == TimerState.STOPPED:
                elapsed_fg = t.stopped_color if self._timer.elapsed > 0 else t.fg_dim
                self._elapsed_label.config(fg=elapsed_fg)
            else:  # IDLE
                self._elapsed_label.config(fg=t.fg_dim)

        if self._toggle_btn:
            if state == TimerState.RUNNING:
                self._toggle_btn.config(
                    text="⏹ Stop", bg=t.pause_btn_bg, fg=t.paused_color
                )
            else:
                self._toggle_btn.config(text="▶️ Start", bg=t.btn_bg, fg=t.btn_fg)

        if self._stop_btn:
            if state == TimerState.IDLE:
                self._stop_btn.config(state="disabled")
            else:
                self._stop_btn.config(state="normal")
        # Keep tree action column in sync with timer state
        self._update_tree_active_time()
