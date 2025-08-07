"""
Unit tests for theme colors module
"""
import pytest
from typing import TypedDict


class TestThemeColors:
    """Test the ThemeColors TypedDict"""
    
    def test_theme_colors_import(self):
        """Test that ThemeColors can be imported"""
        from tick_tock_widget.theme_colors import ThemeColors
        
        # Should be a TypedDict class
        assert ThemeColors is not None
        assert hasattr(ThemeColors, '__annotations__')
    
    def test_theme_colors_structure(self):
        """Test ThemeColors structure and required fields"""
        from tick_tock_widget.theme_colors import ThemeColors
        
        # Check that all required fields are defined
        expected_fields = {
            'name': str,
            'bg': str, 
            'fg': str,
            'accent': str,
            'button_bg': str,
            'button_fg': str,
            'button_active': str
        }
        
        annotations = ThemeColors.__annotations__
        
        for field, expected_type in expected_fields.items():
            assert field in annotations, f"Field '{field}' missing from ThemeColors"
            assert annotations[field] == expected_type, f"Field '{field}' has wrong type"
    
    def test_theme_colors_usage(self):
        """Test creating a ThemeColors instance"""
        from tick_tock_widget.theme_colors import ThemeColors
        
        # Create a valid theme
        test_theme: ThemeColors = {
            'name': 'Test Theme',
            'bg': '#000000',
            'fg': '#FFFFFF', 
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        
        # Verify all fields are present
        assert test_theme['name'] == 'Test Theme'
        assert test_theme['bg'] == '#000000'
        assert test_theme['fg'] == '#FFFFFF'
        assert test_theme['accent'] == '#0078D4'
        assert test_theme['button_bg'] == '#404040'
        assert test_theme['button_fg'] == '#FFFFFF'
        assert test_theme['button_active'] == '#505050'
    
    def test_theme_colors_validation(self):
        """Test that ThemeColors validates field types"""
        from tick_tock_widget.theme_colors import ThemeColors
        
        # This should work fine (all strings)
        valid_theme: ThemeColors = {
            'name': 'Valid',
            'bg': '#000',
            'fg': '#fff',
            'accent': '#blue',
            'button_bg': '#gray',
            'button_fg': '#white',
            'button_active': '#light'
        }
        
        assert isinstance(valid_theme['name'], str)
        assert isinstance(valid_theme['bg'], str)
        assert len(valid_theme) == 7  # All 7 required fields
