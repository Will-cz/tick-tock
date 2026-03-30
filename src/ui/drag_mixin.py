"""Drag-to-move mixin for borderless Tkinter windows."""

from __future__ import annotations

import tkinter as tk
from typing import Optional


class DragMixin:
    """Mixin that adds drag-to-move behaviour to a borderless Tk window host.

    Subclasses must implement :meth:`_get_drag_window` to return the
    ``tk.Misc`` window that should be repositioned when the user drags.

    Call :meth:`_init_drag_state` from the host class ``__init__`` to
    initialise the per-instance tracking variables.
    """

    def _init_drag_state(self) -> None:
        """Initialise per-instance drag tracking variables."""
        self._drag_x: int = 0
        self._drag_y: int = 0
        self._drag_pending_job: Optional[str] = None
        self._drag_target_pos: Optional[tuple[int, int]] = None

    def _get_drag_window(self) -> Optional[tk.Misc]:
        """Return the window to reposition during a drag.

        Override in each host class to return the correct window object.
        """
        raise NotImplementedError

    def _drag_start(self, event: "tk.Event[tk.Misc]") -> None:
        self._drag_x = event.x_root
        self._drag_y = event.y_root

    def _drag_motion(self, event: "tk.Event[tk.Misc]") -> None:
        win = self._get_drag_window()
        if win is None:
            return
        x = win.winfo_x() + (event.x_root - self._drag_x)
        y = win.winfo_y() + (event.y_root - self._drag_y)
        self._drag_target_pos = (x, y)
        if self._drag_pending_job is None:
            self._drag_pending_job = win.after_idle(self._apply_pending_drag_geometry)
        self._drag_x = event.x_root
        self._drag_y = event.y_root

    def _apply_pending_drag_geometry(self) -> None:
        """Coalesce rapid drag events into one geometry update per UI idle cycle."""
        self._drag_pending_job = None
        win = self._get_drag_window()
        if win is None or self._drag_target_pos is None:
            return
        x, y = self._drag_target_pos
        try:
            win.geometry(f"+{x}+{y}")  # type: ignore[attr-defined]
        except tk.TclError:
            pass
