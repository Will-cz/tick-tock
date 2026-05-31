"""Shared UI formatting and color helper functions."""

from src.validation import HEX_COLOR_RE  # noqa: F401 — re-exported for callers


def is_valid_hex_color(value: object) -> bool:
    """Return ``True`` if *value* is a valid 6-digit hex color string."""
    return isinstance(value, str) and HEX_COLOR_RE.fullmatch(value) is not None


def format_elapsed(seconds: float, *, pad_hours: bool = True) -> str:
    """Format elapsed seconds as H:MM:SS or HH:MM:SS."""
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if pad_hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours}:{minutes:02d}:{secs:02d}"


def darken_hex(
    hex_color: str,
    factor: float,
    *,
    preserve_invalid: bool = False,
) -> str:
    """Return *hex_color* darkened by *factor* (0 = black, 1 = original)."""
    if HEX_COLOR_RE.fullmatch(hex_color) is None:
        if preserve_invalid:
            return hex_color
        raise ValueError(f"Invalid hex color: {hex_color!r}")
    clamped = max(0.0, min(1.0, float(factor)))
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"#{int(r * clamped):02x}{int(g * clamped):02x}{int(b * clamped):02x}"
