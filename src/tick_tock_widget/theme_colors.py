"""Theme colors and types for Tick-Tock Widget"""

from typing import TypedDict

class ThemeColors(TypedDict):
    """Theme colors definition"""
    name: str
    bg: str
    fg: str
    accent: str
    button_bg: str
    button_fg: str
    button_active: str
