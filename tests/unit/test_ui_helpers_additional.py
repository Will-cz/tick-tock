"""Additional UI helper tests for coverage-critical small branches."""

import tkinter as tk

from src.ui.base_dialog import BaseDialog
from src.ui.formatting import darken_hex as _darken_hex


def test_darken_hex_raises_for_invalid_color() -> None:
    import pytest

    with pytest.raises(ValueError):
        _darken_hex("bad", 0.5)
    with pytest.raises(ValueError):
        _darken_hex("#12", 0.5)


def test_base_dialog_drag_geometry_handles_tclerror(monkeypatch) -> None:
    dlg = BaseDialog.__new__(BaseDialog)
    dlg._drag_pending_job = "job-id"
    dlg._drag_target_pos = (100, 120)

    def _raise_tcl(*_args, **_kwargs):
        raise tk.TclError("x")

    monkeypatch.setattr(dlg, "geometry", _raise_tcl)
    dlg._apply_pending_drag_geometry()  # should not raise
    assert dlg._drag_pending_job is None
