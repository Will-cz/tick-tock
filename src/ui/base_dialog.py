"""Shared base class for Tick-Tock borderless modal dialogs."""

import tkinter as tk

from src.ui.drag_mixin import DragMixin
from src.ui.themes import Theme


class BaseDialog(DragMixin, tk.Toplevel):
    """Borderless modal dialog base.

    Subclasses gain:
    - ``self._win = self``    — alias so existing ``self._win.xxx`` calls work
    - ``self._parent``        — the parent widget passed to ``__init__``
    - Drag-to-move via :class:`DragMixin`
    """

    def __init__(
        self,
        parent: tk.Misc,
        *,
        theme: Theme,
        alpha: float = 0.95,
    ) -> None:
        super().__init__(parent)
        # Alias so subclass code like ``self._win.geometry(...)`` still works.
        self._win: "BaseDialog" = self
        self._parent = parent
        self._init_drag_state()
        self.configure(bg=theme.bg)
        self.overrideredirect(True)
        self.attributes("-topmost", True)  # pyright: ignore
        try:
            self.attributes("-alpha", alpha)  # pyright: ignore
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # DragMixin protocol
    # ------------------------------------------------------------------

    def _get_drag_window(self) -> "BaseDialog":
        return self
