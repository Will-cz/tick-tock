"""
Integration tests for Tick-Tock Widget components working together
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from pathlib import Path
from datetime import datetime, date

from tick_tock_widget.project_data import ProjectDataManager, Project, SubActivity, TimeRecord
from tick_tock_widget.config import Config, Environment


class TestProjectDataIntegration:
    """Integration tests for project data management"""
    
    def test_complete_project_lifecycle(self, temp_config_dir):
        """Test complete project lifecycle - create, use, save, load"""
        data_file = temp_config_dir / "integration_test.json"
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            # Setup mock config
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 1  # 1 second for testing
            mock_config.is_backup_enabled.return_value = False
            mock_config.get_environment.return_value = Environment.TEST
            mock_get_config.return_value = mock_config
            
            # Create manager and add project
            manager = ProjectDataManager(data_file=str(data_file))
            project = manager.add_project("Integration Test", "DZ999", "ITEST")
            
            assert project is not None
            assert len(manager.projects) == 1
            
            # Add sub-activity
            sub_activity = project.add_sub_activity("Coding", "CODE")
            assert len(project.sub_activities) == 1
            
            # Set as current project and start timer
            manager.set_current_project("ITEST")
            manager.set_current_sub_activity("CODE")
            
            assert manager.current_project_alias == "ITEST"
            assert manager.current_sub_activity_alias == "CODE"
            
            # Start timer
            with patch('tick_tock_widget.project_data.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 8, 13, 10, 0, 0)
                
                result = manager.start_current_timer()
                assert result is True
                
                # Check that timers are running
                today_record = project.get_today_record()
                sub_today_record = sub_activity.get_today_record()
                
                assert today_record.is_running is True
                assert sub_today_record.is_running is True
            
            # Stop timers and save
            manager.stop_all_timers()
            manager.save_projects(force=True)
            
            assert data_file.exists()
        
        # Create new manager and load data
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config2:
            mock_config2 = Mock()
            mock_config2.get_auto_save_interval.return_value = 300
            mock_get_config2.return_value = mock_config2
            
            manager2 = ProjectDataManager(data_file=str(data_file))
            manager2.load_projects()
            
            # Verify data was loaded correctly
            assert len(manager2.projects) == 1
            assert manager2.projects[0].name == "Integration Test"
            assert manager2.projects[0].alias == "ITEST"
            assert len(manager2.projects[0].sub_activities) == 1
            assert manager2.projects[0].sub_activities[0].name == "Coding"
    
    def test_time_tracking_accuracy(self, temp_config_dir):
        """Test time tracking accuracy across start/stop cycles"""
        data_file = temp_config_dir / "time_test.json"
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 1
            mock_config.is_backup_enabled.return_value = False
            mock_config.get_environment.return_value = Environment.TEST
            mock_get_config.return_value = mock_config
            
            manager = ProjectDataManager(data_file=str(data_file))
            project = manager.add_project("Time Test", "DZ888", "TTEST")
            
            manager.set_current_project("TTEST")
            
            with patch('tick_tock_widget.project_data.datetime') as mock_datetime, \
                 patch('tick_tock_widget.project_data.date') as mock_date:
                
                # Set date
                test_date = date(2025, 8, 13)
                mock_date.today.return_value = test_date
                
                # First timing session: 10 minutes
                start_time1 = datetime(2025, 8, 13, 10, 0, 0)
                end_time1 = datetime(2025, 8, 13, 10, 10, 0)
                
                mock_datetime.now.return_value = start_time1
                mock_datetime.fromisoformat.return_value = start_time1
                
                manager.start_current_timer()
                
                mock_datetime.now.return_value = end_time1
                manager.stop_all_timers()
                
                # Second timing session: 15 minutes
                start_time2 = datetime(2025, 8, 13, 11, 0, 0)
                end_time2 = datetime(2025, 8, 13, 11, 15, 0)
                
                mock_datetime.now.return_value = start_time2
                mock_datetime.fromisoformat.return_value = start_time2
                
                manager.start_current_timer()
                
                mock_datetime.now.return_value = end_time2
                manager.stop_all_timers()
                
                # Verify total time
                today_record = project.get_today_record()
                total_seconds = today_record.total_seconds
                
                # Should be 25 minutes = 1500 seconds
                assert total_seconds == 1500
                
                # Verify formatted time
                formatted_time = today_record.get_formatted_time()
                assert formatted_time == "00:25:00"
    
    def test_multiple_projects_timing(self, temp_config_dir):
        """Test timing multiple projects independently"""
        data_file = temp_config_dir / "multi_test.json"
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 1
            mock_config.is_backup_enabled.return_value = False
            mock_config.get_environment.return_value = Environment.TEST
            mock_get_config.return_value = mock_config
            
            manager = ProjectDataManager(data_file=str(data_file))
            
            # Create two projects
            project1 = manager.add_project("Project 1", "DZ111", "P1")
            project2 = manager.add_project("Project 2", "DZ222", "P2")
            
            with patch('tick_tock_widget.project_data.datetime') as mock_datetime, \
                 patch('tick_tock_widget.project_data.date') as mock_date:
                
                test_date = date(2025, 8, 13)
                mock_date.today.return_value = test_date
                
                # Work on project 1 for 30 minutes
                start_time = datetime(2025, 8, 13, 9, 0, 0)
                end_time = datetime(2025, 8, 13, 9, 30, 0)
                
                mock_datetime.now.return_value = start_time
                mock_datetime.fromisoformat.return_value = start_time
                
                manager.set_current_project("P1")
                manager.start_current_timer()
                
                mock_datetime.now.return_value = end_time
                manager.stop_all_timers()
                
                # Work on project 2 for 45 minutes
                start_time2 = datetime(2025, 8, 13, 10, 0, 0)
                end_time2 = datetime(2025, 8, 13, 10, 45, 0)
                
                mock_datetime.now.return_value = start_time2
                mock_datetime.fromisoformat.return_value = start_time2
                
                manager.set_current_project("P2")
                manager.start_current_timer()
                
                mock_datetime.now.return_value = end_time2
                manager.stop_all_timers()
                
                # Verify each project has correct time
                p1_time = project1.get_today_record().total_seconds
                p2_time = project2.get_today_record().total_seconds
                
                assert p1_time == 1800  # 30 minutes
                assert p2_time == 2700  # 45 minutes
                
                # Verify only one timer can run at a time
                manager.set_current_project("P1")
                start_time3 = datetime(2025, 8, 13, 11, 0, 0)
                mock_datetime.now.return_value = start_time3
                mock_datetime.fromisoformat.return_value = start_time3
                
                manager.start_current_timer()
                
                # Check that P1 is running and P2 is not
                assert project1.get_today_record().is_running is True
                assert project2.get_today_record().is_running is False
    
    def test_sub_activity_timing_integration(self, temp_config_dir):
        """Test sub-activity timing integration with main project"""
        data_file = temp_config_dir / "sub_test.json"
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 1
            mock_config.is_backup_enabled.return_value = False
            mock_config.get_environment.return_value = Environment.TEST
            mock_get_config.return_value = mock_config
            
            manager = ProjectDataManager(data_file=str(data_file))
            project = manager.add_project("Sub Test", "DZ333", "STEST")
            
            # Add sub-activities
            coding_sub = project.add_sub_activity("Coding", "CODE")
            testing_sub = project.add_sub_activity("Testing", "TEST")
            
            manager.set_current_project("STEST")
            
            with patch('tick_tock_widget.project_data.datetime') as mock_datetime, \
                 patch('tick_tock_widget.project_data.date') as mock_date:
                
                test_date = date(2025, 8, 13)
                mock_date.today.return_value = test_date
                
                # Work on coding for 1 hour
                start_time = datetime(2025, 8, 13, 9, 0, 0)
                end_time = datetime(2025, 8, 13, 10, 0, 0)
                
                mock_datetime.now.return_value = start_time
                mock_datetime.fromisoformat.return_value = start_time
                
                manager.set_current_sub_activity("CODE")
                manager.start_current_timer()
                
                mock_datetime.now.return_value = end_time
                manager.stop_all_timers()
                
                # Work on testing for 30 minutes
                start_time2 = datetime(2025, 8, 13, 11, 0, 0)
                end_time2 = datetime(2025, 8, 13, 11, 30, 0)
                
                mock_datetime.now.return_value = start_time2
                mock_datetime.fromisoformat.return_value = start_time2
                
                manager.set_current_sub_activity("TEST")
                manager.start_current_timer()
                
                mock_datetime.now.return_value = end_time2
                manager.stop_all_timers()
                
                # Verify sub-activity times
                coding_time = coding_sub.get_today_record().total_seconds
                testing_time = testing_sub.get_today_record().total_seconds
                
                assert coding_time == 3600  # 1 hour
                assert testing_time == 1800  # 30 minutes
                
                # Verify project total time includes both
                project_time = project.get_today_record().total_seconds
                assert project_time == 5400  # 1.5 hours total
    
    def test_environment_switching_integration(self, temp_config_dir):
        """Test switching between environments preserves data"""
        dev_file = temp_config_dir / "dev_data.json"
        prod_file = temp_config_dir / "prod_data.json"
        
        # Create development data
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 1
            mock_config.is_backup_enabled.return_value = False
            mock_config.get_environment.return_value = Environment.DEVELOPMENT
            mock_config.set_environment = Mock()
            mock_config.save_config = Mock()
            mock_config.get_data_file.side_effect = [str(dev_file), str(prod_file)]
            mock_get_config.return_value = mock_config
            
            # Create dev manager and add data
            dev_manager = ProjectDataManager(data_file=str(dev_file))
            dev_project = dev_manager.add_project("Dev Project", "DZ444", "DEV")
            dev_manager.save_projects(force=True)
            
            # Switch to production environment
            result = dev_manager.switch_environment(Environment.PRODUCTION)
            assert result is True
            
            # Verify environment was updated
            mock_config.set_environment.assert_called_with(Environment.PRODUCTION)
            mock_config.save_config.assert_called_once()
            
            # Verify dev data still exists
            assert dev_file.exists()
            with open(dev_file, 'r') as f:
                dev_data = json.load(f)
                assert len(dev_data["projects"]) == 1
                assert dev_data["projects"][0]["name"] == "Dev Project"


class TestConfigIntegration:
    """Integration tests for configuration management"""
    
    def test_config_environment_data_file_mapping(self, temp_config_dir):
        """Test config correctly maps environments to data files"""
        config_file = temp_config_dir / "config.json"

        # Create config with custom data file mapping
        custom_config = {
            "environment": Environment.DEVELOPMENT.value,
            "data_files": {
                "development": "custom_dev.json",
                "production": "custom_prod.json",
                "test": "custom_test.json"
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(custom_config, f)
        
        # Use full config file path instead of complex mocking
        config = Config(config_file=str(config_file))
        
        # Test development environment
        assert config.get_environment() == Environment.DEVELOPMENT
        data_file = config.get_data_file()
        assert data_file.endswith("custom_dev.json")
        
        # Switch to production
        config.set_environment(Environment.PRODUCTION)
        data_file = config.get_data_file()
        assert data_file.endswith("custom_prod.json")
    
    def test_backup_system_integration(self, temp_config_dir):
        """Test backup system creates and manages backups correctly"""
        data_file = temp_config_dir / "backup_test.json"
        backup_dir = temp_config_dir / "backups"
        backup_dir.mkdir()
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 1
            mock_config.is_backup_enabled.return_value = True
            mock_config.get_backup_directory.return_value = backup_dir
            mock_config.get_max_backups.return_value = 3
            mock_config.get_environment.return_value = Environment.TEST
            mock_config.is_debug_mode.return_value = False
            mock_get_config.return_value = mock_config
            
            # Create initial data file
            initial_data = {"projects": [], "test": "data1"}
            with open(data_file, 'w') as f:
                json.dump(initial_data, f)
            
            manager = ProjectDataManager(data_file=str(data_file))
            
            # Add projects and save multiple times to create backups
            for i in range(5):
                project = manager.add_project(f"Project {i}", f"DZ{i}", f"P{i}")
                manager.save_projects(force=True)
            
            # Check that backups were created
            backup_files = list(backup_dir.glob("*.json"))
            
            # Should have max 3 backups due to cleanup
            assert len(backup_files) <= 3
            
            # Verify backup content
            if backup_files:
                with open(backup_files[0], 'r') as f:
                    backup_data = json.load(f)
                    assert "projects" in backup_data
    
    def test_ui_settings_persistence(self, temp_config_dir):
        """Test UI settings are persisted correctly"""
        config_file = temp_config_dir / "ui_test.json"
        
        with patch('tick_tock_widget.config.Path.__new__') as mock_path, \
             patch('sys.frozen', False, create=True):
            
            mock_path.return_value.parent = temp_config_dir
            mock_path.return_value.__truediv__ = lambda self, other: temp_config_dir / other
            
            # Create config and set tree state
            config = Config(config_file="ui_test.json")
            
            tree_state = {
                "project1": True,
                "project2": False,
                "subitem1": True
            }
            
            config.set_tree_state("project_management", tree_state)
            config.save_config()
            
            # Create new config instance and verify state was saved
            config2 = Config(config_file="ui_test.json")
            loaded_state = config2.get_tree_state("project_management")
            
            assert loaded_state == tree_state
