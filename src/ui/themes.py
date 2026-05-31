"""Theme definitions for Tick-Tock Widget — v0.7.0."""

from dataclasses import dataclass
from typing import Any, cast

from src.ui.formatting import darken_hex, is_valid_hex_color


@dataclass(frozen=True)
class Theme:
    """Complete color palette for one UI theme.

    All color values are hex strings (e.g. ``"#001100"``).
    """

    name: str

    # Background / window
    bg: str
    fg: str  # primary (bright) text
    fg_dim: str  # secondary (dim) text / labels
    sep: str  # separator line color

    # Buttons
    btn_bg: str
    btn_fg: str
    btn_active: str

    # Close button (deliberately kept visually distinct)
    close_bg: str
    close_fg: str

    # Stop button
    stop_fg: str
    stop_active: str

    # Input fields (dialogs)
    entry_bg: str
    sel_bg: str  # selection / highlight background

    # Dynamic timer-state colors
    running_color: str  # elapsed label + state dot while running
    paused_color: str  # elapsed label + state dot while paused
    stopped_color: str  # elapsed label + state dot while stopped
    continue_fg: str  # "▶ Continue" button foreground text
    pause_btn_bg: str  # "⏸ Pause" button background color


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


def _darken(hex_color: str, factor: float) -> str:
    """Return *hex_color* darkened by *factor* (0 = black, 1 = original)."""
    return darken_hex(hex_color, factor)


def _blend(c1: str, c2: str, t: float) -> str:
    """Linearly blend two colors: *t* = 0 → *c1*, *t* = 1 → *c2*."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = max(0, min(255, int(r1 + (r2 - r1) * t)))
    g = max(0, min(255, int(g1 + (g2 - g1) * t)))
    b = max(0, min(255, int(b1 + (b2 - b1) * t)))
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# Built-in themes
# ---------------------------------------------------------------------------

MATRIX = Theme(
    name="matrix",
    bg="#001100",
    fg="#00FF00",
    fg_dim="#00AA00",
    sep="#00AA00",
    btn_bg="#003300",
    btn_fg="#00FF00",
    btn_active="#004400",
    close_bg="#660000",
    close_fg="#FF6666",
    stop_fg="#FF6666",
    stop_active="#440000",
    entry_bg="#001a00",
    sel_bg="#004400",
    running_color="#00FF00",
    paused_color="#FFFF00",
    stopped_color="#FF8800",
    continue_fg="#88FF88",
    pause_btn_bg="#333300",
)

DARK = Theme(
    name="dark",
    bg="#1e1e1e",
    fg="#d4d4d4",
    fg_dim="#888888",
    sep="#444444",
    btn_bg="#2d2d2d",
    btn_fg="#d4d4d4",
    btn_active="#3d3d3d",
    close_bg="#6e2020",
    close_fg="#ff7070",
    stop_fg="#ff7070",
    stop_active="#3d1e1e",
    entry_bg="#252525",
    sel_bg="#3d3d3d",
    running_color="#4ec9b0",
    paused_color="#dcdcaa",
    stopped_color="#ce9178",
    continue_fg="#b5cea8",
    pause_btn_bg="#3d3d30",
)

LIGHT = Theme(
    name="light",
    bg="#f5f5f5",
    fg="#1a1a1a",
    fg_dim="#555555",
    sep="#cccccc",
    btn_bg="#e0e0e0",
    btn_fg="#1a1a1a",
    btn_active="#d0d0d0",
    close_bg="#ffcccc",
    close_fg="#aa0000",
    stop_fg="#cc0000",
    stop_active="#ffaaaa",
    entry_bg="#ffffff",
    sel_bg="#cce5ff",
    running_color="#007700",
    paused_color="#886600",
    stopped_color="#cc6600",
    continue_fg="#004400",
    pause_btn_bg="#ececd0",
)

BUILTIN_THEMES: dict[str, Theme] = {
    "matrix": MATRIX,
    "dark": DARK,
    "light": LIGHT,
}

THEME_DISPLAY_NAMES: dict[str, str] = {
    "matrix": "Matrix / Green",
    "dark": "Dark",
    "light": "Light",
    "custom": "Custom",
}


# ---------------------------------------------------------------------------
# Custom theme builder
# ---------------------------------------------------------------------------


def make_custom(bg: str, fg: str, accent: str) -> Theme:
    """Build a custom :class:`Theme` from three base hex colors.

    The remaining palette values are derived automatically by blending and
    darkening the supplied colors so the result is visually self-consistent.

    Args:
        bg:     Main window / background color.
        fg:     Primary text / foreground color.
        accent: Accent color used for buttons and highlights.
    """
    if not is_valid_hex_color(bg):
        bg = MATRIX.bg
    if not is_valid_hex_color(fg):
        fg = MATRIX.fg
    if not is_valid_hex_color(accent):
        accent = MATRIX.btn_bg

    fg_dim = _blend(fg, bg, 0.45)
    sep = _blend(fg, bg, 0.40)
    btn_bg = _blend(bg, accent, 0.35)
    btn_active = _blend(bg, accent, 0.55)
    entry_bg = _darken(bg, 0.75)
    sel_bg = _blend(bg, accent, 0.65)
    continue_fg = _blend(fg, "#ffffff", 0.2)
    pause_btn_bg = _blend(btn_bg, "#333300", 0.4)
    return Theme(
        name="custom",
        bg=bg,
        fg=fg,
        fg_dim=fg_dim,
        sep=sep,
        btn_bg=btn_bg,
        btn_fg=fg,
        btn_active=btn_active,
        close_bg="#660000",
        close_fg="#FF6666",
        stop_fg="#FF6666",
        stop_active="#440000",
        entry_bg=entry_bg,
        sel_bg=sel_bg,
        running_color=fg,
        paused_color="#FFFF00",
        stopped_color="#FF8800",
        continue_fg=continue_fg,
        pause_btn_bg=pause_btn_bg,
    )


# ---------------------------------------------------------------------------
# Theme resolver
# ---------------------------------------------------------------------------


def resolve_theme(theme_config: Any) -> Theme:
    """Build a :class:`Theme` from the ``"theme"`` section of the config dict.

    Falls back to :data:`MATRIX` for unknown or invalid input.

    Args:
        theme_config: The value of ``config["theme"]``.
    """
    if not isinstance(theme_config, dict):
        return MATRIX
    tc = cast(dict[str, Any], theme_config)
    name = str(tc.get("name", "matrix")).lower()
    if name in BUILTIN_THEMES:
        return BUILTIN_THEMES[name]
    if name == "custom":
        custom = tc.get("custom", {})
        if isinstance(custom, dict):
            cc = cast(dict[str, Any], custom)
            bg = str(cc.get("bg", MATRIX.bg))
            fg = str(cc.get("fg", MATRIX.fg))
            accent = str(cc.get("accent", MATRIX.btn_bg))
            return make_custom(bg, fg, accent)
    return MATRIX
