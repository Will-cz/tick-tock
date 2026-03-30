"""Shared input validation helpers."""

import re


HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")
_DEFAULT_NAME_MAX_LENGTH = 120


def normalize_name(
    raw: object,
    *,
    field_label: str,
    max_length: int = _DEFAULT_NAME_MAX_LENGTH,
) -> str:
    """Return a trimmed, validated human-readable name.

    Raises ``ValueError`` when the value is blank, too long, or contains
    control characters.
    """
    name = str(raw).strip()
    if not name:
        raise ValueError(f"{field_label} cannot be empty")
    if len(name) > max_length:
        raise ValueError(f"{field_label} cannot exceed {max_length} characters")
    if _CONTROL_CHAR_RE.search(name) is not None:
        raise ValueError(f"{field_label} cannot contain control characters")
    return name
