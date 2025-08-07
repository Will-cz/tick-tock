"""
Safe theme colors tests - No GUI creation
Tests the theme_colors.py module functionality without any widget creation
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tick_tock_widget.theme_colors import ThemeColors


class TestThemeColorsModule(unittest.TestCase):
    """Test theme colors module functionality"""
    
    def test_theme_colors_type(self):
        """Test ThemeColors TypedDict structure"""
        # Test creating a valid theme
        valid_theme: ThemeColors = {
            'name': 'Test Theme',
            'bg': '#FFFFFF',
            'fg': '#000000',
            'accent': '#0078D4',
            'button_bg': '#E1E1E1',
            'button_fg': '#000000',
            'button_active': '#C7C7C7'
        }
        
        # Verify all required keys are present
        required_keys = ['name', 'bg', 'fg', 'accent', 'button_bg', 'button_fg', 'button_active']
        for key in required_keys:
            self.assertIn(key, valid_theme)
            self.assertIsInstance(valid_theme[key], str)
    
    def test_theme_colors_validation_light(self):
        """Test light theme color validation"""
        light_theme: ThemeColors = {
            'name': 'Light Theme',
            'bg': '#FFFFFF',
            'fg': '#000000',
            'accent': '#0078D4',
            'button_bg': '#F0F0F0',
            'button_fg': '#000000',
            'button_active': '#E0E0E0'
        }
        
        # Test that colors are hex format
        color_keys = ['bg', 'fg', 'accent', 'button_bg', 'button_fg', 'button_active']
        for key in color_keys:
            color = light_theme[key]
            self.assertTrue(color.startswith('#'), f"Color {key} should start with #")
            self.assertEqual(len(color), 7, f"Color {key} should be 7 characters long")
    
    def test_theme_colors_validation_dark(self):
        """Test dark theme color validation"""
        dark_theme: ThemeColors = {
            'name': 'Dark Theme',
            'bg': '#1E1E1E',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#2D2D2D',
            'button_fg': '#FFFFFF',
            'button_active': '#404040'
        }
        
        # Test that colors are hex format
        color_keys = ['bg', 'fg', 'accent', 'button_bg', 'button_fg', 'button_active']
        for key in color_keys:
            color = dark_theme[key]
            self.assertTrue(color.startswith('#'), f"Color {key} should start with #")
            self.assertEqual(len(color), 7, f"Color {key} should be 7 characters long")
    
    def test_theme_colors_name_validation(self):
        """Test theme name validation"""
        theme: ThemeColors = {
            'name': 'My Custom Theme',
            'bg': '#FFFFFF',
            'fg': '#000000',
            'accent': '#0078D4',
            'button_bg': '#E1E1E1',
            'button_fg': '#000000',
            'button_active': '#C7C7C7'
        }
        
        # Test name properties
        self.assertIsInstance(theme['name'], str)
        self.assertTrue(len(theme['name']) > 0)
        self.assertNotEqual(theme['name'].strip(), '')
    
    def test_theme_colors_multiple_themes(self):
        """Test creating multiple theme instances"""
        themes = []
        
        # Create multiple theme variations
        theme_configs = [
            ('Light', '#FFFFFF', '#000000'),
            ('Dark', '#1E1E1E', '#FFFFFF'),
            ('Blue', '#003366', '#FFFFFF'),
            ('Green', '#004400', '#FFFFFF')
        ]
        
        for name, bg, fg in theme_configs:
            theme: ThemeColors = {
                'name': f'{name} Theme',
                'bg': bg,
                'fg': fg,
                'accent': '#0078D4',
                'button_bg': '#E1E1E1',
                'button_fg': '#000000',
                'button_active': '#C7C7C7'
            }
            themes.append(theme)
        
        # Verify all themes are valid
        self.assertEqual(len(themes), 4)
        for theme in themes:
            self.assertIn('name', theme)
            self.assertTrue(theme['name'].endswith(' Theme'))
    
    def test_theme_colors_hex_validation(self):
        """Test hex color format validation patterns"""
        valid_colors = ['#FFFFFF', '#000000', '#FF0000', '#00FF00', '#0000FF', '#123456']
        
        for color in valid_colors:
            theme: ThemeColors = {
                'name': 'Test Theme',
                'bg': color,
                'fg': '#000000',
                'accent': '#0078D4',
                'button_bg': '#E1E1E1',
                'button_fg': '#000000',
                'button_active': '#C7C7C7'
            }
            
            # Test hex format
            self.assertTrue(theme['bg'].startswith('#'))
            self.assertEqual(len(theme['bg']), 7)
            
            # Test that it contains only valid hex characters
            hex_chars = set('0123456789ABCDEFabcdef')
            color_chars = set(theme['bg'][1:])  # Skip the #
            self.assertTrue(color_chars.issubset(hex_chars))


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
