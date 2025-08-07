"""
Tests for theme colors functionality
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tick_tock_widget.theme_colors import ThemeColors


class TestThemeColors(unittest.TestCase):
    """Test ThemeColors TypedDict functionality"""
    
    def test_theme_colors_structure(self):
        """Test that ThemeColors follows expected structure"""
        # Create a valid theme
        theme: ThemeColors = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF', 
            'accent': '#FF0000',
            'button_bg': '#111111',
            'button_fg': '#EEEEEE',
            'button_active': '#222222'
        }
        
        # Test all required keys are present
        self.assertIn('name', theme)
        self.assertIn('bg', theme)
        self.assertIn('fg', theme)
        self.assertIn('accent', theme)
        self.assertIn('button_bg', theme)
        self.assertIn('button_fg', theme)
        self.assertIn('button_active', theme)
        
        # Test values are strings
        for key, value in theme.items():
            self.assertIsInstance(value, str)
    
    def test_color_hex_format(self):
        """Test that color values follow hex format"""
        theme: ThemeColors = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#FF0000', 
            'button_bg': '#111111',
            'button_fg': '#EEEEEE',
            'button_active': '#222222'
        }
        
        color_keys = ['bg', 'fg', 'accent', 'button_bg', 'button_fg', 'button_active']
        for key in color_keys:
            color = theme[key]
            self.assertTrue(color.startswith('#'), f"Color {key} should start with #")
            self.assertEqual(len(color), 7, f"Color {key} should be 7 characters long")
            # Test hex format (excluding #)
            hex_part = color[1:]
            self.assertTrue(all(c in '0123456789ABCDEFabcdef' for c in hex_part), 
                          f"Color {key} should be valid hex")


if __name__ == '__main__':
    unittest.main()
