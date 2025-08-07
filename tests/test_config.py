"""
Test configuration and utilities for Tick-Tock Widget tests
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock
import tkinter as tk

# Test data constants
TEST_PROJECTS = [
    {
        "name": "Web Development Project",
        "dz_number": "WEB-001",
        "alias": "web",
        "sub_activities": [
            {"name": "Frontend Development", "alias": "frontend"},
            {"name": "Backend Development", "alias": "backend"},
            {"name": "Testing", "alias": "testing"},
        ]
    },
    {
        "name": "Mobile Application",
        "dz_number": "MOB-002", 
        "alias": "mobile",
        "sub_activities": [
            {"name": "UI Design", "alias": "ui"},
            {"name": "Development", "alias": "dev"},
            {"name": "QA Testing", "alias": "qa"},
        ]
    },
    {
        "name": "API Development",
        "dz_number": "API-003",
        "alias": "api",
        "sub_activities": [
            {"name": "Design", "alias": "design"},
            {"name": "Implementation", "alias": "impl"},
            {"name": "Documentation", "alias": "docs"},
        ]
    }
]

TEST_THEMES = [
    {
        'name': 'Matrix',
        'bg': '#001100',
        'fg': '#00FF00',
        'accent': '#00AA00',
        'button_bg': '#003300',
        'button_fg': '#00FF00',
        'button_active': '#004400'
    },
    {
        'name': 'Ocean',
        'bg': '#001122',
        'fg': '#00AAFF',
        'accent': '#0088AA',
        'button_bg': '#003344',
        'button_fg': '#00AAFF',
        'button_active': '#004455'
    },
    {
        'name': 'Fire',
        'bg': '#220011',
        'fg': '#FF4400',
        'accent': '#AA2200',
        'button_bg': '#440022',
        'button_fg': '#FF4400',
        'button_active': '#550033'
    }
]


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and utilities"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_path.exists():
            self.temp_path.unlink()
    
    def create_mock_parent_widget(self):
        """Create a mock parent widget for GUI tests"""
        mock_parent = MagicMock()
        mock_parent.root = tk.Tk()
        mock_parent.get_current_theme.return_value = TEST_THEMES[0]
        return mock_parent
    
    def create_test_data_file(self, projects_data=None):
        """Create a test data file with sample projects"""
        if projects_data is None:
            projects_data = TEST_PROJECTS
        
        data = {
            'projects': projects_data,
            'current_project_alias': None,
            'current_sub_activity_alias': None,
            'last_saved': '2025-01-01T00:00:00'
        }
        
        with open(self.temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return self.temp_path
    
    def assert_valid_time_format(self, time_string):
        """Assert that a time string is in valid HH:MM:SS format"""
        import re
        pattern = r'^\d{2}:\d{2}:\d{2}$'
        self.assertRegex(time_string, pattern, f"Invalid time format: {time_string}")
        
        # Verify actual time components
        parts = time_string.split(':')
        hours, minutes, seconds = map(int, parts)
        self.assertGreaterEqual(hours, 0)
        self.assertGreaterEqual(minutes, 0)
        self.assertLessEqual(minutes, 59)
        self.assertGreaterEqual(seconds, 0)
        self.assertLessEqual(seconds, 59)
    
    def assert_valid_theme(self, theme):
        """Assert that a theme has all required properties"""
        required_keys = ['name', 'bg', 'fg', 'accent', 'button_bg', 'button_fg', 'button_active']
        
        for key in required_keys:
            self.assertIn(key, theme, f"Theme missing required key: {key}")
            self.assertIsInstance(theme[key], str, f"Theme {key} should be string")
        
        # Verify color format for color keys
        color_keys = ['bg', 'fg', 'accent', 'button_bg', 'button_fg', 'button_active']
        for key in color_keys:
            color = theme[key]
            self.assertTrue(color.startswith('#'), f"Color {key} should start with #")
            self.assertEqual(len(color), 7, f"Color {key} should be 7 characters long")
            # Verify hex format
            hex_part = color[1:]
            self.assertTrue(all(c in '0123456789ABCDEFabcdef' for c in hex_part),
                          f"Color {key} should be valid hex: {color}")


class MockDataManager:
    """Mock data manager for testing GUI components"""
    
    def __init__(self):
        self.projects = []
        self.current_project_alias = None
        self.current_sub_activity_alias = None
    
    def get_project_aliases(self):
        return [p.alias for p in self.projects]
    
    def get_current_project(self):
        if self.current_project_alias:
            for p in self.projects:
                if p.alias == self.current_project_alias:
                    return p
        return None
    
    def get_current_sub_activity(self):
        project = self.get_current_project()
        if project and self.current_sub_activity_alias:
            for sub in project.sub_activities:
                if sub.alias == self.current_sub_activity_alias:
                    return sub
        return None
    
    def set_current_project(self, alias):
        for p in self.projects:
            if p.alias == alias:
                self.current_project_alias = alias
                self.current_sub_activity_alias = None
                return True
        return False
    
    def set_current_sub_activity(self, alias):
        project = self.get_current_project()
        if project:
            if alias is None:
                self.current_sub_activity_alias = None
                return True
            for sub in project.sub_activities:
                if sub.alias == alias:
                    self.current_sub_activity_alias = alias
                    return True
        return False
    
    def start_current_timer(self):
        project = self.get_current_project()
        return project is not None
    
    def stop_all_timers(self):
        pass
    
    def save_projects(self, force=False):
        return True
    
    def load_projects(self):
        return True


class TestUtilities:
    """Utility functions for tests"""
    
    @staticmethod
    def create_mock_project(name="Test Project", dz_number="TEST-001", alias="test"):
        """Create a mock project for testing"""
        mock_project = MagicMock()
        mock_project.name = name
        mock_project.dz_number = dz_number
        mock_project.alias = alias
        mock_project.sub_activities = []
        mock_project.time_records = {}
        mock_project.is_running_today.return_value = False
        mock_project.get_total_time_today.return_value = "00:00:00"
        mock_project.get_today_record.return_value = MagicMock()
        return mock_project
    
    @staticmethod
    def create_mock_sub_activity(name="Test Sub", alias="test_sub"):
        """Create a mock sub-activity for testing"""
        mock_sub = MagicMock()
        mock_sub.name = name
        mock_sub.alias = alias
        mock_sub.time_records = {}
        mock_sub.is_running_today.return_value = False
        mock_sub.get_total_time_today.return_value = "00:00:00"
        mock_sub.get_today_record.return_value = MagicMock()
        return mock_sub
    
    @staticmethod
    def suppress_gui_calls():
        """Context manager to suppress GUI-related calls during testing"""
        import contextlib
        
        @contextlib.contextmanager
        def suppressor():
            # Patch common GUI methods that might cause issues in tests
            with unittest.mock.patch.object(tk.Tk, 'mainloop'), \
                 unittest.mock.patch.object(tk.Toplevel, 'mainloop'), \
                 unittest.mock.patch('tkinter.messagebox.showinfo'), \
                 unittest.mock.patch('tkinter.messagebox.showerror'), \
                 unittest.mock.patch('tkinter.messagebox.askquestion'):
                yield
        
        return suppressor()


# Test categories for organized test running
TEST_CATEGORIES = {
    'unit': [
        'test_project_data',
        'test_project_data_extended', 
        'test_theme_colors'
    ],
    'gui': [
        'test_tick_tock_widget',
        'test_minimized_widget',
        'test_project_management',
        'test_monthly_report'
    ],
    'integration': [
        'test_integration'
    ],
    'all': [
        'test_project_data',
        'test_project_data_extended',
        'test_theme_colors',
        'test_tick_tock_widget',
        'test_minimized_widget', 
        'test_project_management',
        'test_monthly_report',
        'test_integration'
    ]
}
