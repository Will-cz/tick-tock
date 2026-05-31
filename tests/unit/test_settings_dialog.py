"""Unit tests for SettingsDialog."""

from pathlib import Path
import tkinter as tk

import pytest

from src.config import Config
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.themes import MATRIX

pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def root_tk():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable: {exc}")
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    return Config(config_path=tmp_path / "config.json")


@pytest.fixture
def dlg(root_tk, cfg: Config):
    d = SettingsDialog(root_tk, cfg, MATRIX)
    d.update_idletasks()
    yield d
    try:
        d._close()
    except Exception:
        pass


class TestSettingsDialog:
    def test_build_sets_default_theme_var(self, dlg: SettingsDialog):
        assert dlg._theme_var.get() in {"matrix", "dark", "light", "custom"}

    def test_dialog_is_non_modal(self, dlg: SettingsDialog, root_tk):
        root_tk.update_idletasks()
        assert root_tk.grab_current() is None

    def test_title_icon_matches_main_settings_icon(self, dlg: SettingsDialog):
        assert dlg._title_icon_label is not None
        # Segoe MDL2 Assets "Setting" gear glyph (E713) — matches the
        # main widget's title-bar settings button.
        assert dlg._title_icon_label.cget("text") == "\ue713"

    def test_custom_section_hidden_for_non_custom(self, dlg: SettingsDialog):
        dlg._theme_var.set("matrix")
        dlg._update_custom_visibility()
        assert not dlg._custom_frame.winfo_manager()
        dlg.update_idletasks()
        assert dlg.winfo_height() >= dlg.winfo_reqheight()

    def test_custom_section_shown_for_custom(self, dlg: SettingsDialog):
        dlg._theme_var.set("custom")
        dlg._update_custom_visibility()
        assert dlg._custom_frame.winfo_manager()
        dlg.update_idletasks()
        assert dlg.winfo_height() >= dlg.winfo_reqheight()

    def test_reset_restores_defaults(self, dlg: SettingsDialog):
        dlg._theme_var.set("custom")
        dlg._custom_bg_var.set("#111111")
        dlg._autosave_var.set("10 min")
        dlg._round_var.set("30 min")
        dlg._date_var.set("YYYY-MM-DD")
        dlg._time_fmt_var.set("12h")
        dlg._backup_var.set("20")
        dlg._on_reset()
        assert dlg._theme_var.get() == "matrix"
        assert dlg._custom_bg_var.get() == MATRIX.bg
        assert dlg._autosave_var.get() == "1 min"
        assert dlg._round_var.get() == "None"
        assert dlg._date_var.get() == "DD/MM/YYYY"
        assert dlg._time_fmt_var.get() == "24h"
        assert dlg._backup_var.get() == "5"

    def test_pick_color_updates_var_and_preview(self, dlg: SettingsDialog, monkeypatch):
        preview = dlg._bg_preview
        assert preview is not None
        monkeypatch.setattr(
            "src.ui.dialogs.settings_dialog.colorchooser.askcolor",
            lambda **kwargs: ((0, 255, 0), "#00ff00"),
        )
        dlg._pick_color(dlg._custom_bg_var, preview)
        assert dlg._custom_bg_var.get() == "#00FF00"
        assert preview.cget("bg") == "#00FF00"

    def test_pick_color_cancel_keeps_existing(self, dlg: SettingsDialog, monkeypatch):
        preview = dlg._fg_preview
        assert preview is not None
        original = dlg._custom_fg_var.get()
        monkeypatch.setattr(
            "src.ui.dialogs.settings_dialog.colorchooser.askcolor",
            lambda **kwargs: (None, None),
        )
        dlg._pick_color(dlg._custom_fg_var, preview)
        assert dlg._custom_fg_var.get() == original

    def test_apply_persists_theme_and_timer_settings(self, root_tk, cfg: Config):
        applied = []
        d = SettingsDialog(root_tk, cfg, MATRIX, on_apply=lambda t: applied.append(t))
        d._theme_var.set("custom")
        d._custom_bg_var.set("#010203")
        d._custom_fg_var.set("#AABBCC")
        d._custom_accent_var.set("#112233")
        d._autosave_var.set("5 min")
        d._round_var.set("15 min")
        d._date_var.set("MM/DD/YYYY")
        d._time_fmt_var.set("12h")
        d._backup_var.set("10")
        d._on_apply_pressed()
        cfg.reload()
        assert cfg.get_theme_setting("name") == "custom"
        assert cfg.get_timer_setting("autosave_interval_minutes") == 5
        assert cfg.get_timer_setting("time_rounding_minutes") == 15
        assert cfg.get_timer_setting("date_format") == "MM/DD/YYYY"
        assert cfg.get_timer_setting("time_format") == "12h"
        assert cfg.get_timer_setting("max_backup_files") == 10
        assert len(applied) == 1
        assert d.winfo_exists() == 1
        d._close()

    def test_apply_updates_dialog_theme_in_place(self, root_tk, cfg: Config):
        d = SettingsDialog(root_tk, cfg, MATRIX)
        d.update_idletasks()
        before_bg = d.cget("bg")

        d._theme_var.set("light")
        d._on_apply_pressed()
        d.update_idletasks()

        assert d.winfo_exists() == 1
        assert d._current_theme.name == "light"
        assert d.cget("bg") == d._current_theme.bg
        assert d.cget("bg") != before_bg
        d._close()
