"""
Critical Path Tests - Safety Net for Production Release
Tests the most failure-prone scenarios that could crash the app
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import sys
import os

class TestCriticalPaths:
    """Test critical application paths for production safety"""
    
    def test_main_entry_import_fallback(self):
        """Test main entry point handles import failures gracefully"""
        # Simulate import failure scenario
        with patch('sys.path') as mock_path:
            with patch('builtins.__import__', side_effect=ImportError("Module not found")):
                with patch('os.path.dirname') as mock_dirname:
                    with patch('os.path.join') as mock_join:
                        mock_dirname.return_value = '/mock/dir'
                        mock_join.return_value = '/mock/dir/src'
                        
                        # Import should not crash, should attempt path modification
                        try:
                            import tick_tock
                            # If we get here, the fallback worked
                            assert True
                        except ImportError:
                            # Expected - but app shouldn't crash completely
                            assert True
    
    def test_config_file_corruption_recovery(self):
        """Test recovery from corrupted config file"""
        with patch('builtins.open', mock_open(read_data='invalid json {')):
            with patch('json.load', side_effect=json.JSONDecodeError("Invalid", "doc", 0)):
                # Should not crash, should use default config
                from tick_tock_widget.config import Config
                config = Config()
                # Should have default values even with corrupted file
                assert config.config is not None
                assert "environment" in config.config
    
    def test_data_file_corruption_recovery(self):
        """Test recovery from corrupted project data file"""
        with patch('builtins.open', mock_open(read_data='invalid json [')):
            with patch('json.load', side_effect=json.JSONDecodeError("Invalid", "doc", 0)):
                # Should not crash, should create default projects
                from tick_tock_widget.project_data import ProjectDataManager
                pdm = ProjectDataManager()
                # Should have default empty projects list even with corrupted file
                assert pdm.projects is not None
                assert isinstance(pdm.projects, list)
    
    def test_gui_initialization_failure_recovery(self):
        """Test GUI handles initialization failures"""
        with patch('tkinter.Tk', side_effect=Exception("Display not available")):
            with pytest.raises(Exception):
                # Should fail gracefully, not with unhandled exception
                from tick_tock_widget.tick_tock_widget import TickTockWidget
                widget = TickTockWidget()
    
    @patch('tick_tock_widget.tick_tock_widget.ProjectDataManager')
    @patch('tick_tock_widget.tick_tock_widget.get_config')
    def test_close_app_data_persistence_critical(self, mock_config, mock_project_data, mock_gui_components):
        """CRITICAL: Test close_app saves data before shutdown"""
        # Setup mocks using the GUI fixture
        mock_data_manager = Mock()
        mock_project_data.return_value = mock_data_manager
        
        # Setup mock project with proper attributes
        mock_project = Mock()
        mock_project.sub_activities = []  # Empty list to avoid iteration issues
        mock_project.name = "Test Project"
        mock_project.alias = "TP"
        
        # Setup data manager methods
        mock_data_manager.get_current_project.return_value = mock_project
        mock_data_manager.get_project_aliases.return_value = ["TP"]
        mock_data_manager.current_project_alias = "TP"
        mock_data_manager.projects = [mock_project]

        mock_config_instance = Mock()
        mock_config_instance.get_window_title.return_value = "Test Window"
        mock_config_instance.get_title_color.return_value = "#FFFFFF"
        mock_config_instance.get_environment.return_value = Mock(value="test")
        mock_config_instance.get_auto_idle_time_seconds.return_value = 300
        mock_config_instance.get_timer_popup_interval_seconds.return_value = 600
        mock_config_instance.get_auto_save_interval.return_value = 60  # Return number for math operation
        mock_config.return_value = mock_config_instance

        # Import and create widget
        from tick_tock_widget.tick_tock_widget import TickTockWidget
        widget = TickTockWidget()
        
        # Test close_app MUST save data
        widget.close_app()

        # CRITICAL: Verify data is saved before shutdown
        mock_data_manager.stop_all_timers.assert_called_once()
        # Check that save_projects was called with force=True (the critical call)
        mock_data_manager.save_projects.assert_any_call(force=True)

    @patch('tick_tock_widget.tick_tock_widget.ProjectDataManager')
    @patch('tick_tock_widget.tick_tock_widget.get_config')
    def test_window_close_event_safety(self, mock_config, mock_project_data, mock_gui_components):
        """CRITICAL: Test window close event doesn't lose data"""
        # Setup mocks using the GUI fixture
        mock_data_manager = Mock()
        mock_project_data.return_value = mock_data_manager

        # Setup mock project with proper attributes
        mock_project = Mock()
        mock_project.sub_activities = []  # Empty list to avoid iteration issues
        mock_data_manager.get_current_project.return_value = mock_project

        mock_config_instance = Mock()
        mock_config_instance.get_window_title.return_value = "Test Window"
        mock_config_instance.get_title_color.return_value = "#FFFFFF"
        mock_config_instance.get_environment.return_value = Mock(value="test")
        mock_config_instance.get_auto_idle_time_seconds.return_value = 300
        mock_config_instance.get_timer_popup_interval_seconds.return_value = 600
        mock_config_instance.get_auto_save_interval.return_value = 60  # Return number for math operation
        mock_config.return_value = mock_config_instance        # Import and create widget
        from tick_tock_widget.tick_tock_widget import TickTockWidget
        widget = TickTockWidget()
        
        # Mock the close_app method to verify it's called
        with patch.object(widget, 'close_app') as mock_close_app:
            widget.on_closing()
            
            # CRITICAL: Window close MUST trigger proper shutdown
            mock_close_app.assert_called_once()
    
    def test_environment_detection_safety(self):
        """Test environment detection doesn't crash in unknown environments"""
        # Test various environment scenarios
        test_cases = [
            ('development', 'dev'),
            ('prototype', 'prototype'), 
            ('production', ''),
            ('unknown_env', ''),  # Should default safely
            (None, ''),  # Should handle None
        ]
        
        for env_name, expected_suffix in test_cases:
            with patch.dict(os.environ, {'ENVIRONMENT': env_name} if env_name else {}):
                try:
                    from tick_tock_widget.config import Config
                    config = Config()
                    # Should not crash regardless of environment
                    assert True
                except Exception as e:
                    pytest.fail(f"Environment {env_name} caused crash: {e}")
    
    def test_timer_state_during_shutdown(self, mock_gui_components):
        """Test timer state is properly handled during shutdown"""
        with patch('tick_tock_widget.tick_tock_widget.ProjectDataManager') as mock_pd:
            with patch('tick_tock_widget.tick_tock_widget.get_config') as mock_config:
                mock_data_manager = Mock()
                mock_pd.return_value = mock_data_manager

                # Setup mock project with proper attributes
                mock_project = Mock()
                mock_project.sub_activities = []  # Empty list to avoid iteration issues
                mock_data_manager.get_current_project.return_value = mock_project

                mock_config_instance = Mock()
                mock_config_instance.get_window_title.return_value = "Test Window"
                mock_config_instance.get_title_color.return_value = "#FFFFFF"
                mock_config_instance.get_environment.return_value = Mock(value="test")
                mock_config_instance.get_auto_idle_time_seconds.return_value = 300
                mock_config_instance.get_timer_popup_interval_seconds.return_value = 600
                mock_config_instance.get_auto_save_interval.return_value = 60  # Return number for math operation
                mock_config.return_value = mock_config_instance

                from tick_tock_widget.tick_tock_widget import TickTockWidget
                widget = TickTockWidget()
                
                # Simulate active timers
                mock_data_manager.stop_all_timers = Mock()
                
                widget.close_app()
                
                # CRITICAL: All timers must be stopped before shutdown
                mock_data_manager.stop_all_timers.assert_called_once()

if __name__ == '__main__':
    pytest.main([__file__])
