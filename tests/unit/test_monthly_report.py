#!/usr/bin/env python3
"""
Unit tests for monthly_report.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
import tkinter as tk

@pytest.mark.gui
class TestMonthlyReportWindow:
    """Test MonthlyReportWindow class"""

    @pytest.fixture
    def mock_setup(self):
        """Set up common mocks for testing"""
        with patch('tick_tock_widget.monthly_report.tk.Toplevel') as mock_toplevel, \
             patch('tick_tock_widget.monthly_report.get_config') as mock_get_config, \
             patch('tick_tock_widget.monthly_report.MonthlyReportWindow.setup_window'), \
             patch('tick_tock_widget.monthly_report.MonthlyReportWindow.create_widgets'), \
             patch('tick_tock_widget.monthly_report.MonthlyReportWindow.update_report'):
                 
            # Mock parent widget
            mock_parent = Mock()
            mock_parent.root = Mock()
            mock_parent.root.winfo_x.return_value = 100
            mock_parent.root.winfo_y.return_value = 100
            mock_parent.root.winfo_screenwidth.return_value = 1920
            mock_parent.root.winfo_screenheight.return_value = 1080
            
            # Mock data manager
            mock_data_manager = Mock()
            
            # Mock config
            mock_config = Mock()
            mock_config.get_tree_state.return_value = {}
            mock_config.set_tree_state = Mock()
            mock_get_config.return_value = mock_config
            
            # Mock window
            mock_window = Mock()
            mock_window.update_idletasks = Mock()
            mock_window.geometry = Mock()
            mock_window.configure = Mock()
            mock_window.winfo_screenwidth.return_value = 1920
            mock_window.winfo_screenheight.return_value = 1080
            mock_toplevel.return_value = mock_window
            
            yield {
                'parent': mock_parent,
                'data_manager': mock_data_manager,
                'config': mock_config,
                'get_config': mock_get_config,
                'toplevel': mock_toplevel,
                'window': mock_window
            }

    def test_monthly_report_window_creation(self, mock_setup):
        """Test creating a monthly report window"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        mock_theme = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        
        # Create window
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager'],
            theme=mock_theme
        )
        
        # Verify initialization
        assert window.parent_widget == mocks['parent']
        assert window.data_manager == mocks['data_manager']
        assert window.theme == mock_theme
        assert window.current_year == datetime.now().year
        assert window.current_month == datetime.now().month
        assert not window.window_closed
        mocks['toplevel'].assert_called_once_with(mocks['parent'].root)

    def test_monthly_report_default_theme(self, mock_setup):
        """Test monthly report with default theme"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        
        # Create window without theme
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager'],
            theme=None
        )
        
        # Verify default matrix theme
        assert window.theme['name'] == 'Matrix'
        assert window.theme['bg'] == '#001100'
        assert window.theme['fg'] == '#00FF00'

    def test_format_time(self, mock_setup):
        """Test time formatting"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Test time formatting
        assert window.format_time(3661) == "01:01"  # 1 hour, 1 minute, 1 second
        assert window.format_time(3600) == "01:00"  # 1 hour exactly
        assert window.format_time(1800) == "00:30"  # 30 minutes
        assert window.format_time(0) == "00:00"      # 0 seconds

    def test_get_weekend_days(self, mock_setup):
        """Test getting weekend days"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Test January 2024 (starts on Monday)
        weekend_days = window.get_weekend_days(2024, 1)
        expected_weekends = [6, 7, 13, 14, 20, 21, 27, 28]  # Saturdays and Sundays
        assert weekend_days == expected_weekends

    def test_save_tree_state(self, mock_setup):
        """Test saving tree state"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Mock tree widget
        window.tree = Mock()
        mock_item = "item1"
        window.tree.get_children.return_value = [mock_item]
        window.tree.item.return_value = {'open': True}
        
        # Save tree state
        window.save_tree_state()
        
        # Verify tree state was saved
        mocks['config'].set_tree_state.assert_called_once()

    def test_navigation_methods(self, mock_setup):
        """Test month navigation"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Mock update_report method
        window.update_report = Mock()
        
        # Test next month
        initial_month = window.current_month
        initial_year = window.current_year
        
        window.next_month()
        
        if initial_month == 12:
            assert window.current_month == 1
            assert window.current_year == initial_year + 1
        else:
            assert window.current_month == initial_month + 1
            assert window.current_year == initial_year
            
        window.update_report.assert_called_once()

    def test_previous_month(self, mock_setup):
        """Test previous month navigation"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Set to February to test going back to January
        window.current_month = 2
        window.current_year = 2024
        window.update_report = Mock()
        
        window.previous_month()
        
        assert window.current_month == 1
        assert window.current_year == 2024
        window.update_report.assert_called_once()

    def test_update_theme(self, mock_setup):
        """Test theme updating"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Mock window components
        window.tree = Mock()
        
        new_theme = {
            'name': 'Dark',
            'bg': '#2B2B2B',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        
        # Update theme
        window.update_theme(new_theme)
        
        # Verify theme was updated
        assert window.theme == new_theme

    @patch('tick_tock_widget.monthly_report.MonthlyReportWindow._export_txt')
    @patch('tkinter.filedialog.asksaveasfilename')
    def test_export_to_txt(self, mock_filedialog, mock_export_txt, mock_setup):
        """Test text export functionality"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Mock file dialog to return a filename
        mock_filedialog.return_value = "test_report.txt"
        
        # Set up year_var and month_var that are normally created in create_widgets
        window.year_var = Mock()
        window.year_var.get.return_value = "2024"
        window.month_var = Mock()
        window.month_var.get.return_value = "January"
        
        # Test export
        window.export_to_txt()
        
        # Verify file dialog was called and export method was invoked
        mock_filedialog.assert_called_once()
        mock_export_txt.assert_called_once_with(
            "test_report.txt", 
            2024,  # year from year_var.get()
            1      # month index for January
        )

    @patch('tick_tock_widget.monthly_report.MonthlyReportWindow._export_txt')
    @patch('tkinter.filedialog.asksaveasfilename')
    def test_export_to_txt_cancelled(self, mock_filedialog, mock_export_txt, mock_setup):
        """Test text export when user cancels file dialog"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Mock file dialog to return None (cancelled)
        mock_filedialog.return_value = None
        
        # Test export
        window.export_to_txt()
        
        # Verify file dialog was called but export method was NOT invoked
        mock_filedialog.assert_called_once()
        mock_export_txt.assert_not_called()

    @patch('builtins.open', new_callable=mock_open)
    def test_export_txt_file_creation(self, mock_file, mock_setup):
        """Test actual TXT file export"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Mock tree structure
        window.tree = Mock()
        window.tree.get_children.return_value = []
        
        # Test export
        window._export_txt("test.txt", 2024, 1)
        
        # Verify file was opened for writing
        mock_file.assert_called_once_with("test.txt", 'w', encoding='utf-8')

    def test_key_press_handling(self, mock_setup):
        """Test keyboard event handling"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Mock methods
        window.previous_month = Mock()
        window.next_month = Mock()
        
        # Test left arrow key
        event = Mock()
        event.keysym = 'Left'
        window.on_key_press(event)
        window.previous_month.assert_called_once()
        
        # Test right arrow key
        event.keysym = 'Right'
        window.on_key_press(event)
        window.next_month.assert_called_once()

    def test_double_click_handling(self, mock_setup):
        """Test double-click event handling"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Mock tree
        window.tree = Mock()
        window.tree.focus.return_value = "item1"
        window.tree.item.return_value = {'open': False}
        
        # Test double-click
        event = Mock()
        window.on_double_click(event)
        
        # Verify tree item was toggled
        window.tree.item.assert_called()

    def test_window_closure_tracking(self, mock_setup):
        """Test window closure state tracking"""
        from tick_tock_widget.monthly_report import MonthlyReportWindow
        
        mocks = mock_setup
        window = MonthlyReportWindow(
            parent_widget=mocks['parent'],
            data_manager=mocks['data_manager']
        )
        
        # Initially not closed
        assert not window.window_closed
        
        # Window should track closure state
        assert hasattr(window, 'window_closed')
