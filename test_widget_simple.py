#!/usr/bin/env python3
"""Simple test to verify TickTockWidget can be mocked properly."""

import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tick_tock_widget.tick_tock_widget import TickTockWidget

class TestWidgetSimple(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.write('{}')
        self.temp_file.close()
        
        self.test_theme = {
            'bg': '#333333',
            'fg': '#ffffff',
            'button_bg': '#555555',
            'button_fg': '#ffffff'
        }

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    @patch('tick_tock_widget.tick_tock_widget.get_config')
    @patch('tick_tock_widget.tick_tock_widget.ProjectDataManager')
    @patch('tkinter.DoubleVar')
    @patch('tkinter.StringVar')
    @patch('tkinter.ttk.Style')
    @patch('tkinter.ttk.Combobox')
    @patch('tkinter.ttk.Button')
    @patch('tkinter.ttk.Label')
    @patch('tkinter.ttk.Frame')
    @patch('tkinter.Tk')
    def test_widget_creation(self, mock_tk, mock_frame, mock_label, mock_button,
                           mock_combobox, mock_style, mock_stringvar, mock_doublevar,
                           mock_data_manager_class, mock_get_config):
        """Test that widget can be created with proper mocking"""
        # Configure mocks
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        mock_root.after.return_value = "mock_timer_id"
        
        mock_stringvar.return_value = MagicMock()
        mock_doublevar.return_value = MagicMock()
        mock_style.return_value = MagicMock()
        
        # Mock config
        mock_config = MagicMock()
        mock_config.data_file = self.temp_file.name
        mock_config.themes = [self.test_theme]
        mock_config.current_theme_index = 0
        mock_get_config.return_value = mock_config
        
        # Mock data manager
        mock_data_manager = MagicMock()
        mock_data_manager.projects = []
        mock_data_manager.get_project_aliases.return_value = []
        mock_data_manager_class.return_value = mock_data_manager
        
        # Create widget
        widget = TickTockWidget()
        
        # Basic assertions
        self.assertIsNotNone(widget)
        self.assertFalse(widget.is_timing)
        print("Widget created successfully!")

if __name__ == '__main__':
    unittest.main()
