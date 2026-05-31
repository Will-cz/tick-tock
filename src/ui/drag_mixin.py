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
        # Offset from the window's top-left corner to the mouse-down point,
        # captured in screen coords. Using an absolute offset (instead of
        # accumulating per-motion deltas) keeps drag rock-solid when the
        # window crosses monitors with different DPI scaling.
        self._drag_offset_x: int = 0
        self._drag_offset_y: int = 0
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
        win = self._get_drag_window()
        if win is not None:
            self._drag_offset_x = event.x_root - win.winfo_x()
            self._drag_offset_y = event.y_root - win.winfo_y()

    def _drag_motion(self, event: "tk.Event[tk.Misc]") -> None:
        win = self._get_drag_window()
        if win is None:
            return
        # Absolute placement keeps the mouse-down point pinned to the window
        # under the cursor, even across monitors with mixed DPI scaling.
        x = event.x_root - self._drag_offset_x
        y = event.y_root - self._drag_offset_y
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
