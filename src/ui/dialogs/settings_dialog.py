"""Settings dialog for Tick-Tock Widget — v0.7.1."""

import tkinter as tk
from tkinter import colorchooser, messagebox
from typing import Any, Callable, Optional, cast

from src.config import Config
from src.ui.base_dialog import BaseDialog
from src.ui.themes import (
    BUILTIN_THEMES,
    MATRIX,
    THEME_DISPLAY_NAMES,
    Theme,
    resolve_theme,
)


class SettingsDialog(BaseDialog):
    """Borderless dialog for selecting and customizing the UI theme.

    Provides:
    - Radio buttons to switch between built-in themes (Matrix, Dark, Light)
      and a Custom option.
    - Color pickers for the three custom-theme base colors (background, text,
      accent) — only shown when Custom is selected.
    - Apply, Cancel, and Reset buttons.

    The *on_apply* callback is invoked with the resolved :class:`~src.themes.Theme`
    when the user clicks Apply.
    """

    _W = 300
    _H_COMPACT = 470  # no custom colors visible (minimum)
    _H_CUSTOM = 570  # with custom color pickers (minimum)

    # Timer settings option lists
    _AUTOSAVE_OPTIONS = ["1 min", "5 min", "10 min", "15 min"]
    _AUTOSAVE_TO_INT = {"1 min": 1, "5 min": 5, "10 min": 10, "15 min": 15}
    _AUTOSAVE_TO_LABEL = {1: "1 min", 5: "5 min", 10: "10 min", 15: "15 min"}

    _ROUND_OPTIONS = ["None", "5 min", "15 min", "30 min"]
    _ROUND_TO_INT = {"None": 0, "5 min": 5, "15 min": 15, "30 min": 30}
    _ROUND_TO_LABEL = {0: "None", 5: "5 min", 15: "15 min", 30: "30 min"}

    _DATE_OPTIONS = ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"]
    _TIME_OPTIONS = ["24h", "12h"]

    _BACKUP_OPTIONS = ["3", "5", "10", "20"]
    _BACKUP_TO_INT = {"3": 3, "5": 5, "10": 10, "20": 20}
    _BACKUP_TO_LABEL = {3: "3", 5: "5", 10: "10", 20: "20"}

    def __init__(
        self,
        parent: tk.Tk,
        config: Config,
        current_theme: Theme,
        on_apply: Optional[Callable[[Theme], None]] = None,
        current_always_on_top: bool = True,
        on_set_always_on_top: Optional[Callable[[bool], None]] = None,
        on_export: Optional[Callable[[], None]] = None,
        on_import: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, theme=current_theme, alpha=0.97)
        self._parent = parent
        self._config = config
        self._current_theme = current_theme
        self._on_apply = on_apply
        self._on_set_always_on_top = on_set_always_on_top
        self._on_export = on_export
        self._on_import = on_import

        # -- State variables (initialised from saved config) ----------
        saved_name = config.get_theme_setting("name", "matrix")
        self._theme_var = tk.StringVar(value=str(saved_name))
        _sc_raw = config.get_theme_setting("custom", None)
        saved_custom_d: dict[str, Any] = (
            cast(dict[str, Any], _sc_raw) if isinstance(_sc_raw, dict) else {}
        )
        self._custom_bg_var = tk.StringVar(
            value=str(saved_custom_d.get("bg", MATRIX.bg))
        )
        self._custom_fg_var = tk.StringVar(
            value=str(saved_custom_d.get("fg", MATRIX.fg))
        )
        self._custom_accent_var = tk.StringVar(
            value=str(saved_custom_d.get("accent", MATRIX.btn_bg))
        )

        # -- Timer settings state vars --------------------------------
        autosave_val = int(config.get_timer_setting("autosave_interval_minutes", 1))
        self._autosave_var = tk.StringVar(
            value=self._AUTOSAVE_TO_LABEL.get(autosave_val, "1 min")
        )
        round_val = int(config.get_timer_setting("time_rounding_minutes", 0))
        self._round_var = tk.StringVar(
            value=self._ROUND_TO_LABEL.get(round_val, "None")
        )
        self._date_var = tk.StringVar(
            value=str(config.get_timer_setting("date_format", "DD/MM/YYYY"))
        )
        self._time_fmt_var = tk.StringVar(
            value=str(config.get_timer_setting("time_format", "24h"))
        )
        backup_val = int(config.get_timer_setting("max_backup_files", 5))
        self._backup_var = tk.StringVar(
            value=self._BACKUP_TO_LABEL.get(backup_val, "5")
        )
        self._always_on_top_var = tk.BooleanVar(value=current_always_on_top)

        # Widget refs (populated in _build)
        self._custom_frame: Optional[tk.Frame] = None
        self._bg_preview: Optional[tk.Button] = None
        self._fg_preview: Optional[tk.Button] = None
        self._accent_preview: Optional[tk.Button] = None
        self._title_icon_label: Optional[tk.Label] = None
        self._timer_section_sep: Optional[tk.Frame] = None  # anchor for pack ordering

        self._build(preserve_position=False)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self, *, preserve_position: bool) -> None:
        t = self._current_theme
        win = self._win
        win.title("Settings")
        win.update_idletasks()
        if preserve_position:
            x = win.winfo_x()
            y = win.winfo_y()
        else:
            px = self._parent.winfo_x()
            py = self._parent.winfo_y()
            pw = self._parent.winfo_width()
            x = px + pw + 8
            y = py
        win.geometry(f"{self._W}x{self._H_COMPACT}+{x}+{y}")

        # ---- Border frame -------------------------------------------
        outer = tk.Frame(
            win, bg=t.bg, highlightbackground=t.fg_dim, highlightthickness=1
        )
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        # ---- Title bar ----------------------------------------------
        title_bar = tk.Frame(outer, bg=t.bg, height=26)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        self._title_icon_label = tk.Label(
            title_bar,
            # Segoe MDL2 Assets E713 = Setting gear icon. Shipped with
            # every Win10/11 install and renders as a proper cog.
            text="\ue713",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Segoe MDL2 Assets", 10),
        )
        self._title_icon_label.pack(side="left", padx=(6, 3))

        tk.Label(
            title_bar,
            text="Settings",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 10, "bold"),
        ).pack(side="left")

        tk.Button(
            title_bar,
            text="✕",
            bg=t.close_bg,
            fg=t.close_fg,
            font=("Arial", 10, "bold"),
            bd=0,
            width=2,
            command=self._on_cancel,
        ).pack(side="right", padx=2, pady=2)

        title_bar.bind("<Button-1>", self._drag_start)
        title_bar.bind("<B1-Motion>", self._drag_motion)
        self._title_icon_label.bind("<Button-1>", self._drag_start)
        self._title_icon_label.bind("<B1-Motion>", self._drag_motion)

        # ---- Section separator + heading ----------------------------
        tk.Frame(outer, bg=t.sep, height=1).pack(fill="x", padx=6, pady=(4, 0))

        tk.Label(
            outer,
            text="Theme",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=10, pady=(4, 2))

        # ---- Theme radio buttons ------------------------------------
        radio_frame = tk.Frame(outer, bg=t.bg)
        radio_frame.pack(fill="x", padx=16)

        theme_names = list(BUILTIN_THEMES.keys()) + ["custom"]
        for name in theme_names:
            display = THEME_DISPLAY_NAMES.get(name, name.capitalize())
            tk.Radiobutton(
                radio_frame,
                text=display,
                variable=self._theme_var,
                value=name,
                bg=t.bg,
                fg=t.fg,
                selectcolor=t.btn_bg,
                activebackground=t.bg,
                activeforeground=t.fg,
                font=("Arial", 9),
                command=self._on_theme_selected,
            ).pack(anchor="w", pady=1)

        # ---- Custom color pickers (hidden unless Custom is selected) -
        self._custom_frame = tk.Frame(outer, bg=t.bg)

        tk.Frame(self._custom_frame, bg=t.sep, height=1).pack(
            fill="x", padx=0, pady=(4, 0)
        )
        tk.Label(
            self._custom_frame,
            text="Custom Colors",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", pady=(4, 2))

        self._bg_preview = self._color_row(
            self._custom_frame, t, "Background", self._custom_bg_var
        )
        self._fg_preview = self._color_row(
            self._custom_frame, t, "Text", self._custom_fg_var
        )
        self._accent_preview = self._color_row(
            self._custom_frame, t, "Accent", self._custom_accent_var
        )

        # ---- Timer Settings section ---------------------------------
        self._timer_section_sep = tk.Frame(outer, bg=t.sep, height=1)
        self._timer_section_sep.pack(fill="x", padx=6, pady=(8, 0))

        tk.Label(
            outer,
            text="Timer Settings",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=10, pady=(4, 2))

        ts_frame = tk.Frame(outer, bg=t.bg)
        ts_frame.pack(fill="x", padx=10, pady=(0, 4))
        ts_frame.columnconfigure(1, weight=1)

        def _opt(
            parent: tk.Frame, row: int, label: str, var: tk.StringVar, opts: list[str]
        ) -> None:
            tk.Label(
                parent, text=label, bg=t.bg, fg=t.fg_dim, font=("Arial", 8), anchor="w"
            ).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 6))
            menu = tk.OptionMenu(parent, var, *opts)
            menu.config(
                bg=t.btn_bg,
                fg=t.fg,
                activebackground=t.btn_active,
                activeforeground=t.fg,
                highlightthickness=0,
                relief="flat",
                font=("Arial", 8),
                width=10,
                bd=1,
            )
            menu["menu"].config(
                bg=t.btn_bg,
                fg=t.fg,
                activebackground=t.btn_active,
                activeforeground=t.fg,
                font=("Arial", 8),
            )
            menu.grid(row=row, column=1, sticky="ew", pady=2)

        _opt(ts_frame, 0, "Auto-save:", self._autosave_var, self._AUTOSAVE_OPTIONS)
        _opt(ts_frame, 1, "Rounding:", self._round_var, self._ROUND_OPTIONS)
        _opt(ts_frame, 2, "Date format:", self._date_var, self._DATE_OPTIONS)
        _opt(ts_frame, 3, "Time format:", self._time_fmt_var, self._TIME_OPTIONS)
        _opt(ts_frame, 4, "Max backups:", self._backup_var, self._BACKUP_OPTIONS)

        # ---- App Settings section -----------------------------------
        tk.Frame(outer, bg=t.sep, height=1).pack(fill="x", padx=6, pady=(8, 0))

        tk.Label(
            outer,
            text="Application",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=10, pady=(4, 2))

        app_frame = tk.Frame(outer, bg=t.bg)
        app_frame.pack(fill="x", padx=10, pady=(0, 4))

        tk.Checkbutton(
            app_frame,
            text="Always on top",
            variable=self._always_on_top_var,
            bg=t.bg,
            fg=t.fg,
            activebackground=t.bg,
            activeforeground=t.fg,
            selectcolor=t.bg,
            font=("Arial", 9),
        ).pack(anchor="w")

        io_row = tk.Frame(app_frame, bg=t.bg)
        io_row.pack(fill="x", pady=(4, 0))
        tk.Button(
            io_row,
            text="Export Data",
            command=self._on_export_pressed,
            bg=t.btn_bg,
            fg=t.fg,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            relief="raised",
            bd=1,
            font=("Arial", 8, "bold"),
            width=12,
        ).pack(side="left", padx=(0, 4))
        tk.Button(
            io_row,
            text="Import Data",
            command=self._on_import_pressed,
            bg=t.btn_bg,
            fg=t.fg,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            relief="raised",
            bd=1,
            font=("Arial", 8, "bold"),
            width=12,
        ).pack(side="left")

        # ---- Separator + action buttons -----------------------------
        tk.Frame(outer, bg=t.sep, height=1).pack(fill="x", padx=6, pady=(8, 4))

        btn_row = tk.Frame(outer, bg=t.bg)
        btn_row.pack(pady=(0, 8))

        tk.Button(
            btn_row,
            text="Apply",
            bg=t.btn_bg,
            fg=t.btn_fg,
            activebackground=t.btn_active,
            activeforeground=t.btn_fg,
            font=("Arial", 9, "bold"),
            width=7,
            bd=1,
            relief="raised",
            command=self._on_apply_pressed,
        ).pack(side="left", padx=4)

        tk.Button(
            btn_row,
            text="Cancel",
            bg=t.btn_bg,
            fg=t.fg_dim,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            font=("Arial", 9),
            width=7,
            bd=1,
            relief="raised",
            command=self._on_cancel,
        ).pack(side="left", padx=4)

        tk.Button(
            btn_row,
            text="Reset",
            bg=t.btn_bg,
            fg=t.fg_dim,
            activebackground=t.btn_active,
            activeforeground=t.fg,
            font=("Arial", 9),
            width=7,
            bd=1,
            relief="raised",
            command=self._on_reset,
        ).pack(side="left", padx=4)

        self._update_custom_visibility()

        win.update_idletasks()
        win.focus_force()

    def _set_dialog_height(self, minimum_height: int) -> None:
        """Resize height to fit content while preserving the current position."""
        win = self._win
        win.update_idletasks()
        required_height = win.winfo_reqheight() + 6
        target_height = max(minimum_height, required_height)
        x = win.winfo_x()
        y = win.winfo_y()
        win.geometry(f"{self._W}x{target_height}+{x}+{y}")

    def _rebuild_for_theme(self, theme: Theme) -> None:
        """Rebuild all dialog widgets so the dialog theme updates immediately."""
        self._current_theme = theme
        self.configure(bg=theme.bg)
        self._custom_frame = None
        self._bg_preview = None
        self._fg_preview = None
        self._accent_preview = None
        self._title_icon_label = None
        self._timer_section_sep = None
        for child in self._win.winfo_children():
            child.destroy()
        self._build(preserve_position=True)

    # ------------------------------------------------------------------
    # Color row helper
    # ------------------------------------------------------------------

    def _color_row(
        self,
        parent: tk.Frame,
        t: Theme,
        label: str,
        var: tk.StringVar,
    ) -> tk.Button:
        """Create a label + hex display + color-swatch button for one color."""
        row = tk.Frame(parent, bg=t.bg)
        row.pack(fill="x", pady=2)

        tk.Label(
            row,
            text=f"{label}:",
            bg=t.bg,
            fg=t.fg_dim,
            font=("Arial", 8),
            width=10,
            anchor="w",
        ).pack(side="left")

        tk.Label(
            row,
            textvariable=var,
            bg=t.bg,
            fg=t.fg_dim,
            font=("Consolas", 8),
            width=9,
            anchor="w",
        ).pack(side="left", padx=(0, 4))

        swatch_color = var.get()
        preview = tk.Button(
            row,
            text="  ●  ",
            bg=swatch_color,
            fg=swatch_color,
            activebackground=swatch_color,
            bd=1,
            relief="raised",
            width=3,
        )
        preview.pack(side="left")

        def _on_click() -> None:
            self._pick_color(var, preview)

        preview.config(command=_on_click)
        return preview

    def _pick_color(self, var: tk.StringVar, preview: tk.Button) -> None:
        """Open a system color-chooser dialog and update *var* and *preview*."""
        current = var.get()
        win = self._win
        assert win is not None
        result = colorchooser.askcolor(color=current, parent=win, title="Choose Color")
        if result[1]:
            hex_color = result[1].upper()
            var.set(hex_color)
            preview.config(bg=hex_color, fg=hex_color, activebackground=hex_color)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_theme_selected(self) -> None:
        self._update_custom_visibility()

    def _update_custom_visibility(self) -> None:
        """Show custom color section only when the 'custom' radio is selected."""
        if self._custom_frame is None:
            return
        if self._theme_var.get() == "custom":
            # Insert before the timer section separator so ordering is preserved.
            if self._timer_section_sep is not None:
                self._custom_frame.pack(
                    fill="x", padx=10, pady=(0, 2), before=self._timer_section_sep
                )
            else:
                self._custom_frame.pack(fill="x", padx=10, pady=(0, 2))
            self._set_dialog_height(self._H_CUSTOM)
        else:
            self._custom_frame.pack_forget()
            self._set_dialog_height(self._H_COMPACT)

    def _on_apply_pressed(self) -> None:
        name = self._theme_var.get()
        self._config.set_theme_setting("name", name)
        if name == "custom":
            self._config.set_theme_setting(
                "custom",
                {
                    "bg": self._custom_bg_var.get(),
                    "fg": self._custom_fg_var.get(),
                    "accent": self._custom_accent_var.get(),
                },
            )
        # Save timer settings
        self._config.set_timer_setting(
            "autosave_interval_minutes",
            self._AUTOSAVE_TO_INT.get(self._autosave_var.get(), 1),
        )
        self._config.set_timer_setting(
            "time_rounding_minutes",
            self._ROUND_TO_INT.get(self._round_var.get(), 0),
        )
        self._config.set_timer_setting("date_format", self._date_var.get())
        self._config.set_timer_setting("time_format", self._time_fmt_var.get())
        self._config.set_timer_setting(
            "max_backup_files",
            self._BACKUP_TO_INT.get(self._backup_var.get(), 5),
        )
        self._config.set_ui_pref("always_on_top", self._always_on_top_var.get())
        try:
            self._config.save()
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror(
                "Settings Save Failed",
                f"Could not save settings:\n{exc}",
                parent=self._win,
            )
            return

        theme_cfg = self._config.get("theme", {})
        new_theme = resolve_theme(theme_cfg)
        if self._on_set_always_on_top is not None:
            self._on_set_always_on_top(self._always_on_top_var.get())
        if self._on_apply is not None:
            self._on_apply(new_theme)
        self._rebuild_for_theme(new_theme)
        self.lift()  # pyright: ignore
        self.focus_force()

    def _on_cancel(self) -> None:
        self._close()

    def _on_export_pressed(self) -> None:
        if self._on_export is not None:
            self._on_export()

    def _on_import_pressed(self) -> None:
        if self._on_import is not None:
            self._on_import()

    def _on_reset(self) -> None:
        """Reset selections to defaults (Matrix / Green, standard timer settings)."""
        self._theme_var.set("matrix")
        self._custom_bg_var.set(MATRIX.bg)
        self._custom_fg_var.set(MATRIX.fg)
        self._custom_accent_var.set(MATRIX.btn_bg)
        self._update_custom_visibility()
        # Reset timer settings to defaults
        self._autosave_var.set("1 min")
        self._round_var.set("None")
        self._date_var.set("DD/MM/YYYY")
        self._time_fmt_var.set("24h")
        self._backup_var.set("5")
        self._always_on_top_var.set(True)
        if self._bg_preview:
            self._bg_preview.config(
                bg=MATRIX.bg, fg=MATRIX.bg, activebackground=MATRIX.bg
            )
        if self._fg_preview:
            self._fg_preview.config(
                bg=MATRIX.fg, fg=MATRIX.fg, activebackground=MATRIX.fg
            )
        if self._accent_preview:
            self._accent_preview.config(
                bg=MATRIX.btn_bg, fg=MATRIX.btn_bg, activebackground=MATRIX.btn_bg
            )

    def _close(self) -> None:
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
