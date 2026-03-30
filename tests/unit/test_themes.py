"""Unit tests for themes module (v0.7.0)."""

import pytest

from src.ui.themes import (
    BUILTIN_THEMES,
    DARK,
    LIGHT,
    MATRIX,
    THEME_DISPLAY_NAMES,
    Theme,
    _blend,
    _darken,
    make_custom,
    resolve_theme,
)


# ---------------------------------------------------------------------------
# Theme dataclass
# ---------------------------------------------------------------------------


class TestThemeDataclass:
    def test_matrix_name(self):
        assert MATRIX.name == "matrix"

    def test_dark_name(self):
        assert DARK.name == "dark"

    def test_light_name(self):
        assert LIGHT.name == "light"

    def test_theme_is_frozen(self):
        with pytest.raises((AttributeError, TypeError)):
            MATRIX.bg = "#ffffff"  # type: ignore[misc]

    def test_all_fields_are_strings(self):
        for field in MATRIX.__dataclass_fields__:
            assert isinstance(getattr(MATRIX, field), str)

    def test_builtin_themes_dict_has_all_themes(self):
        assert set(BUILTIN_THEMES.keys()) == {"matrix", "dark", "light"}

    def test_display_names_include_custom(self):
        assert "custom" in THEME_DISPLAY_NAMES

    def test_all_builtin_themes_have_display_names(self):
        for name in BUILTIN_THEMES:
            assert name in THEME_DISPLAY_NAMES


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


class TestColorHelpers:
    def test_darken_to_black(self):
        assert _darken("#ffffff", 0.0) == "#000000"

    def test_darken_no_change(self):
        assert _darken("#ff8800", 1.0) == "#ff8800"

    def test_darken_half(self):
        result = _darken("#ff0000", 0.5)
        # red channel: 255 * 0.5 = 127 = 0x7f
        assert result == "#7f0000"

    def test_blend_extremes_returns_c1(self):
        assert _blend("#ff0000", "#0000ff", 0.0) == "#ff0000"

    def test_blend_extremes_returns_c2(self):
        assert _blend("#ff0000", "#0000ff", 1.0) == "#0000ff"

    def test_blend_midpoint(self):
        result = _blend("#000000", "#ffffff", 0.5)
        # each channel: (255 * 0.5) = 127 = 0x7f
        assert result == "#7f7f7f"

    def test_blend_clamps_values(self):
        # should not raise and should stay in [0, 255]
        result = _blend("#ffffff", "#ffffff", 0.5)
        assert result == "#ffffff"


# ---------------------------------------------------------------------------
# make_custom
# ---------------------------------------------------------------------------


class TestMakeCustom:
    def test_name_is_custom(self):
        t = make_custom("#001100", "#00FF00", "#003300")
        assert t.name == "custom"

    def test_bg_is_passed_through(self):
        t = make_custom("#112233", "#aabbcc", "#334455")
        assert t.bg == "#112233"

    def test_fg_is_passed_through(self):
        t = make_custom("#112233", "#aabbcc", "#334455")
        assert t.fg == "#aabbcc"

    def test_derived_colors_are_valid_hex(self):
        t = make_custom("#102030", "#80a0c0", "#203040")
        for field in t.__dataclass_fields__:
            if field == "name":
                continue
            value = getattr(t, field)
            assert value.startswith("#"), f"Field {field} = {value!r} not a hex color"
            assert len(value) == 7, f"Field {field} = {value!r} wrong length"

    def test_fg_dim_is_darker_than_fg(self):
        """fg_dim should be a blend toward bg, so less saturated."""
        t = make_custom("#000000", "#00ff00", "#003300")
        # fg is #00ff00 (green=255), fg_dim should have lower green value
        fg_g = int(t.fg[3:5], 16)
        fgd_g = int(t.fg_dim[3:5], 16)
        assert fgd_g < fg_g

    def test_close_button_always_red(self):
        """Close button stays red regardless of theme colors."""
        t = make_custom("#ffffff", "#000000", "#ffffff")
        assert t.close_bg == "#660000"
        assert t.close_fg == "#FF6666"


# ---------------------------------------------------------------------------
# resolve_theme
# ---------------------------------------------------------------------------


class TestResolveTheme:
    def test_matrix_name_returns_matrix(self):
        assert resolve_theme({"name": "matrix"}) is MATRIX

    def test_dark_name_returns_dark(self):
        assert resolve_theme({"name": "dark"}) is DARK

    def test_light_name_returns_light(self):
        assert resolve_theme({"name": "light"}) is LIGHT

    def test_case_insensitive(self):
        assert resolve_theme({"name": "MATRIX"}) is MATRIX
        assert resolve_theme({"name": "Dark"}) is DARK

    def test_unknown_name_returns_matrix(self):
        assert resolve_theme({"name": "neon"}) is MATRIX

    def test_empty_dict_returns_matrix(self):
        assert resolve_theme({}) is MATRIX

    def test_non_dict_returns_matrix(self):
        assert resolve_theme(None) is MATRIX  # type: ignore[arg-type]
        assert resolve_theme("matrix") is MATRIX  # type: ignore[arg-type]

    def test_custom_name_builds_theme(self):
        cfg = {
            "name": "custom",
            "custom": {"bg": "#102030", "fg": "#c0d0e0", "accent": "#203040"},
        }
        t = resolve_theme(cfg)
        assert t.name == "custom"
        assert t.bg == "#102030"
        assert t.fg == "#c0d0e0"

    def test_custom_missing_custom_dict_returns_matrix(self):
        # No "custom" key present
        t = resolve_theme({"name": "custom"})
        # Falls back gracefully using MATRIX defaults
        assert isinstance(t, Theme)

    def test_custom_partial_dict_uses_matrix_fallback(self):
        cfg = {"name": "custom", "custom": {"bg": "#aabbcc"}}
        t = resolve_theme(cfg)
        assert t.bg == "#aabbcc"
        # fg falls back to MATRIX.fg
        assert t.fg == MATRIX.fg

    def test_custom_invalid_hex_values_fall_back(self):
        cfg = {
            "name": "custom",
            "custom": {
                "bg": "not-a-hex",
                "fg": "#12",
                "accent": "#zzzzzz",
            },
        }
        t = resolve_theme(cfg)
        assert t.bg == MATRIX.bg
        assert t.fg == MATRIX.fg
        assert t.btn_bg.startswith("#")
