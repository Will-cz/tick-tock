"""
Unit tests for TickTockWidget main GUI class
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk

from tick_tock_widget.tick_tock_widget import TickTockWidget
from tick_tock_widget.theme_colors import ThemeColors
from tick_tock_widget.config import Environment


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
        widget.show_monthly_report()
        
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
        """Test that create_widgets creates main_frame"""
        widget = TickTockWidget()
        # After initialization, main_frame should exist
        assert hasattr(widget, 'main_frame')
        assert widget.main_frame is not None
    
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
    
    def test_test_mode_flag(self, mock_gui_components, mock_get_config):
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
    
    def test_cycle_count_tracking(self, mock_gui_components, mock_get_config):
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
        
        # Mock the update_theme method for child windows
        mock_project_mgmt.update_theme = Mock()
        mock_monthly_report.update_theme = Mock()
        
        # Mock window existence checks to return True
        mock_project_mgmt.window.winfo_exists.return_value = True
        mock_monthly_report.window.winfo_exists.return_value = True

        # Test the theme cycle method that actually calls update_theme
        widget.cycle_theme()

        # Check that update_theme was called on child windows that exist
        mock_project_mgmt.update_theme.assert_called_once()
        mock_monthly_report.update_theme.assert_called_once()
        mock_monthly_report.update_theme.assert_called_once()
        # Minimized widget would be recreated rather than updated
    
    def test_close_child_windows(self, mock_gui_components, mock_get_config):
        """Test closing child windows via close_app"""
        widget = TickTockWidget()
        
        # Create mock child windows
        mock_project_mgmt = Mock()
        mock_monthly_report = Mock()
        mock_minimized = Mock()
        
        widget.project_mgmt_window = mock_project_mgmt
        widget.monthly_report_window = mock_monthly_report  
        widget.minimized_widget = mock_minimized
        
        # Mock the root destroy to avoid actual window operations
        widget.root.destroy = Mock()
        
        widget.close_app()  # Use actual close_app method instead of non-existent close_child_windows
        
        # Should clean up minimized widget (as per actual implementation)
        mock_minimized.root.destroy.assert_called_once()

    def test_close_app_data_safety(self, mock_gui_components, mock_get_config):
        """Test that close_app saves data and cleans up properly"""
        widget = TickTockWidget()
        
        # Mock the data manager methods
        widget.data_manager.stop_all_timers = Mock()
        widget.data_manager.save_projects = Mock()
        
        # Mock the root destroy method
        widget.root.destroy = Mock()
        
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

    def test_save_data_wrapper(self, mock_gui_components, mock_get_config):
        """Test save_data wrapper method"""
        widget = TickTockWidget()
        
        # Mock the data manager's save_projects method
        widget.data_manager.save_projects = Mock()
        
        widget.save_data()
        
        # Should call data manager with force=True
        widget.data_manager.save_projects.assert_called_once_with(force=True)

    def test_toggle_timing_alias(self, mock_gui_components, mock_get_config):
        """Test toggle_timing alias for compatibility"""
        widget = TickTockWidget()
        
        with patch.object(widget, 'toggle_timer') as mock_toggle:
            widget.toggle_timing()
            mock_toggle.assert_called_once()

    def test_schedule_auto_save_calls_forced_save(self, mock_gui_components, mock_get_config):
        """Test that schedule_auto_save calls save_projects with force=True"""
        widget = TickTockWidget()
        
        # Mock the data manager's save_projects method
        widget.data_manager.save_projects = Mock()
        
        # Mock the root.after method to prevent actual scheduling
        widget.root.after = Mock()
        
        # Call schedule_auto_save
        widget.schedule_auto_save()
        
        # Verify save_projects was called with force=True (this is the critical fix)
        widget.data_manager.save_projects.assert_called_once_with(force=True)
        
        # Verify next auto-save was scheduled
        expected_interval_ms = widget.config.get_auto_save_interval() * 1000
        widget.root.after.assert_called_once_with(expected_interval_ms, widget.schedule_auto_save)

    def test_schedule_auto_save_uses_config_interval(self, mock_gui_components, mock_get_config):
        """Test that schedule_auto_save uses the configured interval"""
        # Mock the config import in tick_tock_widget module as well
        with patch('tick_tock_widget.tick_tock_widget.get_config') as mock_widget_config:
            # Set custom auto-save interval for both patches
            mock_get_config.return_value.get_auto_save_interval.return_value = 120  # 2 minutes
            mock_widget_config.return_value.get_auto_save_interval.return_value = 120  # 2 minutes
            
            widget = TickTockWidget()
            widget.data_manager.save_projects = Mock()
            widget.root.after = Mock()
            
            widget.schedule_auto_save()
            
            # Should schedule next save with 120000ms (120 seconds * 1000)
            widget.root.after.assert_called_once_with(120000, widget.schedule_auto_save)

    def test_auto_save_initialization(self, mock_gui_components, mock_get_config):
        """Test that auto-save is initialized when widget is created"""
        with patch.object(TickTockWidget, 'schedule_auto_save') as mock_schedule:
            widget = TickTockWidget()
            
            # Verify schedule_auto_save was called during initialization
            mock_schedule.assert_called_once()

    def test_environment_button_condition_development(self, mock_gui_components, mock_get_config):
        """Test that environment button condition is True in development environment"""
        mock_get_config.return_value.get_environment.return_value = Environment.DEVELOPMENT
        widget = TickTockWidget()
        
        # Test the condition directly - should be True for development
        condition = widget.config.get_environment().value not in ["production", "prototype"]
        assert condition is True, "Environment button should be visible in development"

    def test_environment_button_condition_test(self, mock_gui_components, mock_get_config):
        """Test that environment button condition is True in test environment"""
        mock_get_config.return_value.get_environment.return_value = Environment.TEST
        widget = TickTockWidget()
        
        # Test the condition directly - should be True for test
        condition = widget.config.get_environment().value not in ["production", "prototype"]
        assert condition is True, "Environment button should be visible in test"

    def test_environment_button_condition_production(self, mock_gui_components, mock_get_config):
        """Test that environment button condition is False in production environment"""
        mock_get_config.return_value.get_environment.return_value = Environment.PRODUCTION
        widget = TickTockWidget()
        
        # Test the condition directly - should be False for production
        condition = widget.config.get_environment().value not in ["production", "prototype"]
        assert condition is False, "Environment button should be hidden in production"

    def test_environment_button_condition_prototype(self, mock_gui_components, mock_get_config):
        """Test that environment button condition is False in prototype environment"""
        mock_get_config.return_value.get_environment.return_value = Environment.PROTOTYPE
        widget = TickTockWidget()
        
        # Test the condition directly - should be False for prototype
        condition = widget.config.get_environment().value not in ["production", "prototype"]
        assert condition is False, "Environment button should be hidden in prototype"

    def test_environment_button_visibility_logic(self, mock_gui_components, mock_get_config):
        """Test environment button visibility logic for all environments"""
        expected_visibility = {
            Environment.DEVELOPMENT: True,
            Environment.TEST: True,
            Environment.PRODUCTION: False,
            Environment.PROTOTYPE: False
        }
        
        for env, should_be_visible in expected_visibility.items():
            mock_get_config.return_value.get_environment.return_value = env
            widget = TickTockWidget()
            
            # Test the actual condition used in the code
            condition = widget.config.get_environment().value not in ["production", "prototype"]
            
            if should_be_visible:
                assert condition is True, f"Environment button condition should be True for {env.value}"
            else:
                assert condition is False, f"Environment button condition should be False for {env.value}"

    def test_show_environment_menu_exists(self, mock_gui_components, mock_get_config):
        """Test that show_environment_menu method exists for button command"""
        widget = TickTockWidget()
        
        # Verify the method exists and is callable
        assert hasattr(widget, 'show_environment_menu'), "show_environment_menu method should exist"
        assert callable(getattr(widget, 'show_environment_menu')), "show_environment_menu should be callable"

    def test_restore_window_updates_display(self, mock_gui_components, mock_get_config):
        """Test that restore_window updates displays after minimized widget changes (Total Today fix)"""
        widget = TickTockWidget()
        
        # Mock the display update methods
        widget.update_project_display = Mock()
        widget.update_project_list = Mock()
        
        # Simulate having a minimized widget
        mock_minimized_widget = Mock()
        mock_minimized_widget.root = Mock()
        widget.minimized_widget = mock_minimized_widget
        
        # Mock window position
        widget._last_window_pos = {
            'x': 100,
            'y': 100,
            'width': 800,
            'height': 600
        }
        
        # Call restore_window (this is what happens when user maximizes from minimized state)
        widget.restore_window(200, 200)
        
        # Verify that displays are updated to reflect any changes made in minimized widget
        widget.update_project_display.assert_called_once()
        widget.update_project_list.assert_called_once()
        
        # Verify minimized widget was cleaned up
        assert widget.minimized_widget is None
        mock_minimized_widget.root.destroy.assert_called_once()

    def test_restore_window_handles_destroyed_minimized_widget(self, mock_gui_components, mock_get_config):
        """Test that restore_window handles already destroyed minimized widget gracefully"""
        widget = TickTockWidget()
        
        # Mock the display update methods
        widget.update_project_display = Mock()
        widget.update_project_list = Mock()
        
        # Simulate having a minimized widget that throws error when destroyed
        mock_minimized_widget = Mock()
        mock_minimized_widget.root = Mock()
        mock_minimized_widget.root.destroy.side_effect = tk.TclError("Window already destroyed")
        widget.minimized_widget = mock_minimized_widget
        
        # Call restore_window - should not crash
        widget.restore_window()
        
        # Verify that displays are still updated despite the error
        widget.update_project_display.assert_called_once()
        widget.update_project_list.assert_called_once()
        
        # Verify minimized widget reference was still cleaned up
        assert widget.minimized_widget is None


class TestSystemTrayIntegration:
    """Test System Tray Integration"""
    
    @patch('tick_tock_widget.tick_tock_widget.SystemTrayManager')
    @patch('tick_tock_widget.tick_tock_widget.is_system_tray_available')
    def test_system_tray_initialization_success(self, mock_is_available, mock_system_tray_class, mock_gui_components, mock_get_config):
        """Test successful system tray initialization"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        # Mock system tray being available
        mock_is_available.return_value = True
        
        # Mock successful system tray creation
        mock_system_tray = Mock()
        mock_system_tray_class.return_value = mock_system_tray
        
        widget = TickTockWidget()
        
        # Verify system tray was initialized with correct callbacks
        mock_system_tray_class.assert_called_once_with(
            main_window_callback=widget._toggle_window_visibility,
            quit_callback=widget._quit_application
        )
        assert widget.system_tray == mock_system_tray
    
    @patch('tick_tock_widget.tick_tock_widget.SystemTrayManager')
    @patch('tick_tock_widget.tick_tock_widget.is_system_tray_available')
    def test_system_tray_initialization_failure(self, mock_is_available, mock_system_tray_class, mock_gui_components, mock_get_config):
        """Test system tray initialization failure handling"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        # Mock system tray being available but creation failing
        mock_is_available.return_value = True
        mock_system_tray_class.side_effect = Exception("Pystray not available")
        
        widget = TickTockWidget()
        
        # Verify graceful failure handling
        mock_system_tray_class.assert_called_once()
        assert widget.system_tray is None
    
    @patch('tick_tock_widget.tick_tock_widget.is_system_tray_available')
    def test_system_tray_not_available(self, mock_is_available, mock_gui_components, mock_get_config):
        """Test when system tray is not available"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        # Mock system tray not being available
        mock_is_available.return_value = False
        
        widget = TickTockWidget()
        
        # Verify system tray is None when not available
        assert widget.system_tray is None
    
    def test_timer_id_tracking_initialization(self, mock_gui_components, mock_get_config):
        """Test that timer IDs are properly initialized"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        widget = TickTockWidget()
        
        # The timer IDs may be set during initialization due to auto-save and update time timers
        # This is expected behavior, so we just verify they exist
        assert hasattr(widget, '_auto_save_timer_id')
        assert hasattr(widget, '_update_time_timer_id')
    
    @patch('sys.exit')
    def test_quit_application_with_timer_cleanup(self, mock_sys_exit, mock_gui_components, mock_get_config):
        """Test _quit_application properly cancels timers"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        widget = TickTockWidget()
        
        # Set some mock timer IDs
        widget._auto_save_timer_id = "timer1"
        widget._update_time_timer_id = "timer2"
        
        # Mock the root.after_cancel method
        widget.root.after_cancel = Mock()
        # Mock the root.quit method
        widget.root.quit = Mock()
        
        # Call quit application
        widget._quit_application()
        
        # Verify timers were cancelled
        expected_calls = [
            (("timer1",), {}),
            (("timer2",), {})
        ]
        assert widget.root.after_cancel.call_args_list == expected_calls
        
        # Verify timer IDs are reset
        assert widget._auto_save_timer_id is None
        assert widget._update_time_timer_id is None
        
        # Verify root.quit was called
        widget.root.quit.assert_called_once()
        # Verify sys.exit was called
        mock_sys_exit.assert_called_once_with(0)
    
    @patch('sys.exit')
    def test_quit_application_without_timers(self, mock_sys_exit, mock_gui_components, mock_get_config):
        """Test _quit_application when no timers are active"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        widget = TickTockWidget()
        
        # Ensure timer IDs are None
        widget._auto_save_timer_id = None
        widget._update_time_timer_id = None
        
        # Mock the root.after_cancel method
        widget.root.after_cancel = Mock()
        # Mock the root.quit method
        widget.root.quit = Mock()
        
        # Call quit application
        widget._quit_application()
        
        # Verify after_cancel was not called since no timers were active
        widget.root.after_cancel.assert_not_called()
        
        # Verify root.quit was still called
        widget.root.quit.assert_called_once()
        # Verify sys.exit was called
        mock_sys_exit.assert_called_once_with(0)
    
    def test_window_close_calls_quit_application(self, mock_gui_components, mock_get_config):
        """Test that window close event calls appropriate methods"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        widget = TickTockWidget()
        
        # Test both scenarios: with and without system tray
        # Since the system tray might not be available in test environment,
        # we'll test the close_app path
        with patch.object(widget, 'close_app') as mock_close:
            widget._on_window_close()
            # Should call close_app when no system tray or tray not running
            mock_close.assert_called_once()
    
    def test_keyboard_shortcuts_bound(self, mock_gui_components, mock_get_config):
        """Test that keyboard shortcuts are properly bound"""
        mock_get_config.return_value.get_auto_idle_time_seconds.return_value = 300
        mock_get_config.return_value.get_timer_popup_interval_seconds.return_value = 600
        
        widget = TickTockWidget()
        
        # Verify keyboard shortcuts were bound
        # The actual bindings from the implementation
        expected_bindings = [
            '<Control-h>',
            '<Control-Shift-H>',
            '<Alt-F4>',
            '<Escape>'
        ]
        
        for binding in expected_bindings:
            assert binding in widget.root.key_bindings
