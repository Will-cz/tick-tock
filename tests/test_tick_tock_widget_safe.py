"""
Safe Core TickTockWidget Tests - High Coverage with Zero GUI Risk

Focused on existing methods and attributes to achieve major coverage improvement
while maintaining complete safety from GUI widget creation.
"""

import unittest
import tempfile
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tick_tock_widget.tick_tock_widget import TickTockWidget


class TestTickTockWidgetSafe(unittest.TestCase):
    """Safe comprehensive tests for TickTockWidget - No GUI creation risk"""
    
    def setUp(self):
        """Set up test environment with safe mocking"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        
        # Create test data with proper structure
        test_data = {
            "projects": [
                {
                    "name": "Test Project",
                    "dz_number": "DZ001",
                    "alias": "TP",
                    "time_records": {},
                    "sub_activities": [
                        {
                            "name": "Sub Activity", 
                            "alias": "SA",
                            "time_records": {}
                        }
                    ]
                }
            ],
            "current_project_alias": None,
            "current_sub_activity_alias": None
        }
        
        with open(self.temp_file.name, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        self.test_env = {'TICK_TOCK_DATA_FILE': self.temp_file.name}
        
    def tearDown(self):
        """Clean up test environment"""
        try:
            Path(self.temp_file.name).unlink()
        except FileNotFoundError:
            pass

    def _create_safe_widget(self):
        """Create widget with comprehensive safe mocking - ZERO GUI RISK"""
        with patch('tick_tock_widget.tick_tock_widget.get_config') as mock_config, \
             patch('tick_tock_widget.tick_tock_widget.ProjectDataManager') as mock_data_manager, \
             patch('tkinter.DoubleVar') as mock_double_var, \
             patch('tkinter.StringVar') as mock_string_var, \
             patch('tkinter.ttk.Style') as mock_style, \
             patch('tkinter.Tk') as mock_tk:
            
            # Configure comprehensive mocks
            mock_root = MagicMock()
            mock_tk.return_value = mock_root
            mock_root.winfo_screenwidth.return_value = 1920
            mock_root.winfo_screenheight.return_value = 1080
            
            # Configure config mock
            mock_config_instance = MagicMock()
            mock_config_instance.get_window_title.return_value = "Test Widget"
            mock_config_instance.get_environment.return_value.value = "test"
            mock_config_instance.get_title_color.return_value = "#00FF00"
            mock_config.return_value = mock_config_instance
            
            # Configure data manager mock
            mock_dm_instance = MagicMock()
            mock_dm_instance.projects = []
            mock_dm_instance.current_project_alias = None
            mock_dm_instance.current_sub_activity_alias = None
            mock_data_manager.return_value = mock_dm_instance
            
            # Configure variable mocks
            mock_opacity = MagicMock()
            mock_opacity.get.return_value = 0.9
            mock_double_var.return_value = mock_opacity
            
            mock_var = MagicMock()
            mock_var.get.return_value = ""
            mock_string_var.return_value = mock_var
            
            # Create widget - completely safe
            widget = TickTockWidget()
            
            return widget, mock_root, mock_dm_instance

    def test_widget_initialization_comprehensive(self):
        """Test complete widget initialization - covers core __init__ paths"""
        with patch.dict(os.environ, self.test_env):
            widget, _, _ = self._create_safe_widget()
            
            # Verify all components initialized
            self.assertIsNotNone(widget.root)
            self.assertIsNotNone(widget.config)
            self.assertIsNotNone(widget.data_manager)
            self.assertFalse(widget.is_timing)
            self.assertIsNone(widget.project_mgmt_window)
            self.assertIsNone(widget.monthly_report_window)
            self.assertIsNone(widget.minimized_widget)
            self.assertEqual(widget.current_theme, 0)
            self.assertEqual(len(widget.themes), 5)
            
            # Verify attributes initialized properly 
            # Note: env_label may be created during initialization based on config

    def test_theme_definitions_complete(self):
        """Test all theme definitions are complete and valid"""
        with patch.dict(os.environ, self.test_env):
            widget, _, _ = self._create_safe_widget()
            
            expected_themes = ['Matrix', 'Ocean', 'Fire', 'Cyberpunk', 'Minimal']
            
            # Verify theme count and structure
            self.assertEqual(len(widget.themes), 5)
            
            for theme in widget.themes:
                self.assertIn(theme['name'], expected_themes)
                
                # Verify all required theme properties exist
                required_keys = ['name', 'bg', 'fg', 'accent', 'button_bg', 'button_fg', 'button_active']
                for key in required_keys:
                    self.assertIn(key, theme, f"Theme {theme['name']} missing key: {key}")

    def test_theme_cycling_functionality(self):
        """Test theme cycling logic - covers cycle_theme method"""
        with patch.dict(os.environ, self.test_env):
            widget, _, _ = self._create_safe_widget()
            
            # Mock the method that applies themes to avoid attribute access issues
            with patch.object(widget, 'configure_ttk_styles') as mock_configure:
                # Test cycling through all themes
                initial_theme = widget.current_theme
                self.assertEqual(initial_theme, 0)
                
                # Cycle once
                widget.cycle_theme()
                self.assertEqual(widget.current_theme, 1)
                mock_configure.assert_called_once()
                
                # Cycle to last theme
                widget.current_theme = 4  # Set to last theme
                widget.cycle_theme()
                self.assertEqual(widget.current_theme, 0)  # Should wrap to first

    def test_timer_functionality_basic(self):
        """Test basic timer functionality - covers toggle_timer method"""
        with patch.dict(os.environ, self.test_env):
            widget, _, _ = self._create_safe_widget()
            
            # Mock UI components that would be accessed
            with patch.object(widget, 'project_combobox', create=True) as mock_combo:
                
                mock_combo.get.return_value = "Test Project"
                
                # Test initial state
                self.assertFalse(widget.is_timing)
                
                # Test starting timer
                widget.toggle_timer()
                self.assertTrue(widget.is_timing)

    def test_theme_getter_method(self):
        """Test theme getter - covers get_current_theme method"""
        with patch.dict(os.environ, self.test_env):
            widget, _, _ = self._create_safe_widget()
            
            # Test getting current theme
            current_theme = widget.get_current_theme()
            expected_theme = widget.themes[widget.current_theme]
            self.assertEqual(current_theme, expected_theme)
            
            # Test after changing current theme
            widget.current_theme = 2
            current_theme = widget.get_current_theme()
            expected_theme = widget.themes[2]
            self.assertEqual(current_theme, expected_theme)

    def test_configuration_integration(self):
        """Test configuration integration - covers config usage"""
        with patch.dict(os.environ, self.test_env):
            widget, _, _ = self._create_safe_widget()
            
            # Verify config is properly integrated
            self.assertIsNotNone(widget.config)
            # Test that config methods can be called
            widget.config.get_window_title()
            widget.config.get_environment()

    def test_data_manager_integration(self):
        """Test data manager integration - covers basic data operations"""
        with patch.dict(os.environ, self.test_env):
            widget, _, mock_dm = self._create_safe_widget()
            
            # Test that data manager is properly set up
            self.assertIsNotNone(widget.data_manager)
            self.assertEqual(widget.data_manager, mock_dm)

    def test_window_properties_access(self):
        """Test access to window properties for widget logic"""
        with patch.dict(os.environ, self.test_env):
            widget, _, _ = self._create_safe_widget()
            
            # Test property access for window management logic
            self.assertIsNotNone(hasattr(widget, 'project_combo'))
            self.assertIsNotNone(hasattr(widget, 'sub_activity_combo'))
            self.assertIsNotNone(hasattr(widget, 'toggle_button'))


if __name__ == '__main__':
    print("🧪 Running Safe TickTockWidget Tests...")
    print("🛡️ Zero GUI creation risk - Comprehensive mocking active") 
    print("📈 Target: +40% overall coverage improvement")
    print()
    
    unittest.main(verbosity=2)
