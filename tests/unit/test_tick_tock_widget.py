"""
Unit tests for TickTockWidget main GUI class
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk

from tick_tock_widget.tick_tock_widget import TickTockWidget
from tick_tock_widget.theme_colors import ThemeColors


class TestTickTockWidget:
    """Test TickTockWidget main class"""
    
    def test_widget_initialization(self, mock_gui_components, mock_get_config):
        """Test TickTockWidget initialization"""
        # Mock the get_config to return proper values
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        widget = TickTockWidget()
        
        assert widget.root is not None
        assert widget.is_timing is False
        assert widget.project_mgmt_window is None
        assert widget.monthly_report_window is None
        assert widget.minimized_widget is None
        assert widget.current_theme == 0
        assert len(widget.themes) == 5  # Should have 5 themes
    
    def test_widget_themes(self, mock_gui_components, mock_get_config):
        """Test widget theme structure"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        widget = TickTockWidget()
        
        # Check that all themes have required keys
        required_keys = ['name', 'bg', 'fg', 'accent', 'button_bg', 'button_fg', 'button_active']
        
        for theme in widget.themes:
            for key in required_keys:
                assert key in theme
        
        # Check specific themes
        theme_names = [theme['name'] for theme in widget.themes]
        assert 'Matrix' in theme_names
        assert 'Ocean' in theme_names
        assert 'Fire' in theme_names
        assert 'Cyberpunk' in theme_names
        assert 'Minimal' in theme_names
    
    def test_get_current_theme(self, mock_gui_components, mock_get_config):
        """Test getting current theme"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        widget = TickTockWidget()
        
        # Default theme should be the first one (Matrix)
        current_theme = widget.get_current_theme()
        assert current_theme['name'] == 'Matrix'
        assert current_theme['bg'] == '#001100'
        assert current_theme['fg'] == '#00FF00'
    
    def test_cycle_theme(self, mock_gui_components, mock_get_config):
        """Test cycling through themes"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        widget = TickTockWidget()
        
        initial_theme = widget.current_theme
        widget.cycle_theme()
        
        assert widget.current_theme == (initial_theme + 1) % len(widget.themes)
    
    def test_cycle_theme_wraps_around(self, mock_gui_components, mock_get_config):
        """Test theme cycling wraps around to beginning"""
        widget = TickTockWidget()
        
        # Set to last theme
        widget.current_theme = len(widget.themes) - 1
        widget.cycle_theme()
        
        # Should wrap to first theme
        assert widget.current_theme == 0
    
    @patch('tick_tock_widget.tick_tock_widget.ProjectManagementWindow')
    def test_open_project_management(self, mock_project_mgmt_class, mock_gui_components, mock_get_config):
        """Test opening project management window"""
        mock_project_mgmt = Mock()
        mock_project_mgmt_class.return_value = mock_project_mgmt
        
        widget = TickTockWidget()
        widget.open_project_management()
        
        assert widget.project_mgmt_window is mock_project_mgmt
        mock_project_mgmt_class.assert_called_once()
    
    @patch('tick_tock_widget.tick_tock_widget.MonthlyReportWindow')
    def test_open_monthly_report(self, mock_monthly_report_class, mock_gui_components, mock_get_config):
        """Test opening monthly report window"""
        mock_monthly_report = Mock()
        mock_monthly_report_class.return_value = mock_monthly_report
        
        widget = TickTockWidget()
        widget.open_monthly_report()
        
        assert widget.monthly_report_window is mock_monthly_report
        mock_monthly_report_class.assert_called_once()
    
    @patch('tick_tock_widget.tick_tock_widget.MinimizedTickTockWidget')
    def test_minimize_widget(self, mock_minimized_class, mock_gui_components, mock_get_config):
        """Test minimizing widget"""
        mock_minimized = Mock()
        mock_minimized_class.return_value = mock_minimized
        
        widget = TickTockWidget()
        widget.minimize()
        
        assert widget.minimized_widget is mock_minimized
        mock_minimized_class.assert_called_once()
        widget.root.withdraw.assert_called_once()
    
    def test_maximize_from_minimized(self, mock_gui_components, mock_get_config):
        """Test maximizing from minimized state"""
        widget = TickTockWidget()
        
        # Create mock minimized widget
        mock_minimized = Mock()
        widget.minimized_widget = mock_minimized
        
        widget.maximize(100, 200)
        
        # Should destroy minimized widget and show main window
        mock_minimized.root.destroy.assert_called_once()
        assert widget.minimized_widget is None
        widget.root.deiconify.assert_called_once()
        widget.root.geometry.assert_called()  # Just check it was called
    
    def test_setup_window_called(self, mock_gui_components, mock_get_config):
        """Test that setup_window is called during initialization"""
        with patch.object(TickTockWidget, 'setup_window') as mock_setup:
            widget = TickTockWidget()
            mock_setup.assert_called_once()
    
    def test_create_widgets_called(self, mock_gui_components, mock_get_config):
        """Test that create_widgets is called during initialization"""
        with patch.object(TickTockWidget, 'create_widgets') as mock_create:
            widget = TickTockWidget()
            mock_create.assert_called_once()
    
    def test_setup_dragging_called(self, mock_gui_components, mock_get_config):
        """Test that setup_dragging is called during initialization"""
        with patch.object(TickTockWidget, 'setup_dragging') as mock_setup:
            widget = TickTockWidget()
            mock_setup.assert_called_once()
    
    def test_load_data_called(self, mock_gui_components, mock_get_config):
        """Test that load_data is called during initialization"""
        with patch.object(TickTockWidget, 'load_data') as mock_load:
            widget = TickTockWidget()
            mock_load.assert_called_once()
    
    def test_test_mode_flag(self, mock_dependencies):
        """Test test mode flag suppresses UI dialogs"""
        widget = TickTockWidget()
        
        # Test mode should be False by default
        assert widget._test_mode is False
        
        # Can be set to True for testing
        widget._test_mode = True
        assert widget._test_mode is True
    
    def test_timing_state_management(self, mock_gui_components, mock_get_config):
        """Test timing state management"""
        widget = TickTockWidget()
        
        # Should start with timing false
        assert widget.is_timing is False
        assert widget._timing_explicitly_set is False
        
        # Should be able to set timing state
        widget.is_timing = True
        assert widget.is_timing is True
    
    def test_window_position_tracking(self, mock_gui_components, mock_get_config):
        """Test window position tracking"""
        widget = TickTockWidget()
        
        # Should start with no last position
        assert widget._last_window_pos is None
        
        # Should be able to set position
        widget._last_window_pos = {"x": 100, "y": 200}
        assert widget._last_window_pos == {"x": 100, "y": 200}
    
    def test_cycle_count_tracking(self, mock_dependencies):
        """Test cycle count tracking for testing"""
        widget = TickTockWidget()
        
        # Should start at 0
        assert widget._cycle_count == 0
        
        # Should increment when cycling themes
        widget.cycle_theme()
        assert widget._cycle_count == 1
        
        widget.cycle_theme()
        assert widget._cycle_count == 2
    
    def test_update_theme_propagation(self, mock_gui_components, mock_get_config):
        """Test that theme updates propagate to child windows"""
        widget = TickTockWidget()
        
        # Create mock child windows
        mock_project_mgmt = Mock()
        mock_monthly_report = Mock()
        mock_minimized = Mock()
        
        widget.project_mgmt_window = mock_project_mgmt
        widget.monthly_report_window = mock_monthly_report
        widget.minimized_widget = mock_minimized
        
        # Cycle theme
        new_theme = widget.themes[1]  # Ocean theme
        widget.current_theme = 1
        
        with patch.object(widget, 'apply_theme') as mock_apply:
            widget.update_child_window_themes()
            
            # Should update all child windows
            mock_project_mgmt.update_theme.assert_called_once_with(new_theme)
            mock_monthly_report.update_theme.assert_called_once_with(new_theme)
            # Minimized widget would be recreated rather than updated
    
    def test_close_child_windows(self, mock_dependencies):
        """Test closing child windows"""
        widget = TickTockWidget()
        
        # Create mock child windows
        mock_project_mgmt = Mock()
        mock_monthly_report = Mock()
        mock_minimized = Mock()
        
        widget.project_mgmt_window = mock_project_mgmt
        widget.monthly_report_window = mock_monthly_report  
        widget.minimized_widget = mock_minimized
        
        widget.close_child_windows()
        
        # Should close all child windows
        mock_project_mgmt.close.assert_called_once()
        mock_monthly_report.close.assert_called_once()
        mock_minimized.root.destroy.assert_called_once()
        
        # Should clear references
        assert widget.project_mgmt_window is None
        assert widget.monthly_report_window is None
        assert widget.minimized_widget is None

    def test_close_app_data_safety(self, mock_gui_components, mock_get_config):
        """Test that close_app saves data and cleans up properly"""
        widget = TickTockWidget()
        
        # Create mock minimized widget
        mock_minimized = Mock()
        widget.minimized_widget = mock_minimized
        
        # Test close_app
        widget.close_app()
        
        # Verify data is saved
        widget.data_manager.stop_all_timers.assert_called_once()
        widget.data_manager.save_projects.assert_called_once_with(force=True)
        
        # Verify minimized widget cleanup
        mock_minimized.root.destroy.assert_called_once()
        
        # Verify main window destruction
        widget.root.destroy.assert_called_once()

    def test_on_closing_calls_close_app(self, mock_gui_components, mock_get_config):
        """Test that window close event calls close_app"""
        widget = TickTockWidget()
        
        with patch.object(widget, 'close_app') as mock_close:
            widget.on_closing()
            mock_close.assert_called_once()

    def test_save_data_wrapper(self, mock_dependencies):
        """Test save_data wrapper method"""
        widget = TickTockWidget()
        
        widget.save_data()
        
        # Should call data manager with force=True
        widget.data_manager.save_projects.assert_called_once_with(force=True)

    def test_toggle_timing_alias(self, mock_gui_components, mock_get_config):
        """Test toggle_timing alias for compatibility"""
        widget = TickTockWidget()
        
        with patch.object(widget, 'toggle_timer') as mock_toggle:
            widget.toggle_timing()
            mock_toggle.assert_called_once()
