"""
End-to-end tests for Tick-Tock Widget user scenarios
These tests simulate complete user workflows
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from pathlib import Path
from datetime import datetime, date

from tick_tock_widget.project_data import ProjectDataManager
from tick_tock_widget.config import Config, Environment


class TestUserScenarios:
    """Test complete user scenarios end-to-end"""
    
    @pytest.mark.e2e
    def test_new_user_first_project_workflow(self, temp_config_dir):
        """Test workflow for new user creating their first project"""
        # Simulate new user - no existing data files
        data_file = temp_config_dir / "first_project.json"
        assert not data_file.exists()
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            # Setup fresh environment
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 300
            mock_config.is_backup_enabled.return_value = True
            mock_config.get_backup_directory.return_value = temp_config_dir / "backups"
            mock_config.get_max_backups.return_value = 10
            mock_config.get_environment.return_value = Environment.PRODUCTION
            mock_config.is_debug_mode.return_value = False
            mock_get_config.return_value = mock_config
            
            # User opens application - creates data manager
            manager = ProjectDataManager(data_file=str(data_file))
            
            # Should start with no projects
            assert len(manager.projects) == 0
            assert manager.current_project_alias is None
            
            # User creates their first project
            project = manager.add_project(
                name="My First Project",
                dz_number="DZ001",
                alias="FIRST"
            )
            
            assert project is not None
            assert project.name == "My First Project"
            assert len(manager.projects) == 1
            
            # User adds sub-activities
            coding_sub = project.add_sub_activity("Development", "DEV")
            testing_sub = project.add_sub_activity("Testing", "TEST")
            
            assert len(project.sub_activities) == 2
            
            # User sets project as current and starts working
            manager.set_current_project("FIRST")
            manager.set_current_sub_activity("DEV")
            
            assert manager.current_project_alias == "FIRST"
            assert manager.current_sub_activity_alias == "DEV"
            
            # Simulate working session
            with patch('tick_tock_widget.project_data.datetime') as mock_datetime, \
                 patch('tick_tock_widget.project_data.date') as mock_date:
                
                work_date = date(2025, 8, 13)
                mock_date.today.return_value = work_date
                
                # Start working at 9 AM
                start_time = datetime(2025, 8, 13, 9, 0, 0)
                mock_datetime.now.return_value = start_time
                mock_datetime.fromisoformat.return_value = start_time
                
                manager.start_current_timer()
                
                # Work for 2 hours
                end_time = datetime(2025, 8, 13, 11, 0, 0)
                mock_datetime.now.return_value = end_time
                manager.stop_all_timers()
                
                # Verify time was tracked
                dev_time = coding_sub.get_today_record().total_seconds
                project_time = project.get_today_record().total_seconds
                
                assert dev_time == 7200  # 2 hours
                assert project_time == 7200  # 2 hours
                
                # Switch to testing
                manager.set_current_sub_activity("TEST")
                
                # Work on testing for 1 hour
                test_start = datetime(2025, 8, 13, 14, 0, 0)
                test_end = datetime(2025, 8, 13, 15, 0, 0)
                
                mock_datetime.now.return_value = test_start
                mock_datetime.fromisoformat.return_value = test_start
                manager.start_current_timer()
                
                mock_datetime.now.return_value = test_end
                manager.stop_all_timers()
                
                # Verify total times
                test_time = testing_sub.get_today_record().total_seconds
                total_project_time = project.get_today_record().total_seconds
                
                assert test_time == 3600  # 1 hour
                assert total_project_time == 10800  # 3 hours total
            
            # User saves work
            result = manager.save_projects(force=True)
            assert result is True
            assert data_file.exists()
            
            # Verify data persists by reloading
            manager2 = ProjectDataManager(data_file=str(data_file))
            manager2.load_projects()
            assert len(manager2.projects) == 1
            reloaded_project = manager2.projects[0]
            assert reloaded_project.name == "My First Project"
            assert len(reloaded_project.sub_activities) == 2
    
    @pytest.mark.e2e
    def test_daily_work_routine_scenario(self, temp_config_dir):
        """Test typical daily work routine with multiple projects"""
        data_file = temp_config_dir / "daily_work.json"
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 300
            mock_config.is_backup_enabled.return_value = False  # Disable for test speed
            mock_config.get_environment.return_value = Environment.PRODUCTION
            mock_get_config.return_value = mock_config
            
            # Setup existing work environment
            manager = ProjectDataManager(data_file=str(data_file))
            
            # Create multiple projects (like a real work scenario)
            web_project = manager.add_project("Website Redesign", "DZ100", "WEB")
            api_project = manager.add_project("API Development", "DZ200", "API") 
            docs_project = manager.add_project("Documentation", "DZ300", "DOCS")
            
            # Add sub-activities
            web_project.add_sub_activity("Frontend", "FE")
            web_project.add_sub_activity("Backend", "BE")
            api_project.add_sub_activity("Development", "DEV")
            api_project.add_sub_activity("Testing", "TEST")
            docs_project.add_sub_activity("Writing", "WRITE")
            
            with patch('tick_tock_widget.project_data.datetime') as mock_datetime, \
                 patch('tick_tock_widget.project_data.date') as mock_date:
                
                work_date = date(2025, 8, 13)
                mock_date.today.return_value = work_date
                
                # Morning: Work on website frontend (9:00-11:00)
                mock_datetime.now.return_value = datetime(2025, 8, 13, 9, 0, 0)
                mock_datetime.fromisoformat.return_value = datetime(2025, 8, 13, 9, 0, 0)
                
                manager.set_current_project("WEB")
                manager.set_current_sub_activity("FE")
                manager.start_current_timer()
                
                mock_datetime.now.return_value = datetime(2025, 8, 13, 11, 0, 0)
                manager.stop_all_timers()
                
                # Break, then API development (11:30-12:30)
                mock_datetime.now.return_value = datetime(2025, 8, 13, 11, 30, 0)
                mock_datetime.fromisoformat.return_value = datetime(2025, 8, 13, 11, 30, 0)
                
                manager.set_current_project("API")
                manager.set_current_sub_activity("DEV")
                manager.start_current_timer()
                
                mock_datetime.now.return_value = datetime(2025, 8, 13, 12, 30, 0)
                manager.stop_all_timers()
                
                # Afternoon: Documentation writing (14:00-15:30)
                mock_datetime.now.return_value = datetime(2025, 8, 13, 14, 0, 0)
                mock_datetime.fromisoformat.return_value = datetime(2025, 8, 13, 14, 0, 0)
                
                manager.set_current_project("DOCS")
                manager.set_current_sub_activity("WRITE")
                manager.start_current_timer()
                
                mock_datetime.now.return_value = datetime(2025, 8, 13, 15, 30, 0)
                manager.stop_all_timers()
                
                # End of day: API testing (15:45-17:00)
                mock_datetime.now.return_value = datetime(2025, 8, 13, 15, 45, 0)
                mock_datetime.fromisoformat.return_value = datetime(2025, 8, 13, 15, 45, 0)
                
                manager.set_current_project("API")
                manager.set_current_sub_activity("TEST")
                manager.start_current_timer()
                
                mock_datetime.now.return_value = datetime(2025, 8, 13, 17, 0, 0)
                manager.stop_all_timers()
                
                # Verify daily totals
                web_fe_time = web_project.sub_activities[0].get_today_record().total_seconds
                api_dev_time = api_project.sub_activities[0].get_today_record().total_seconds
                api_test_time = api_project.sub_activities[1].get_today_record().total_seconds
                docs_write_time = docs_project.sub_activities[0].get_today_record().total_seconds
                
                assert web_fe_time == 7200    # 2 hours frontend
                assert api_dev_time == 3600   # 1 hour API dev  
                assert api_test_time == 4500  # 1.25 hours API testing
                assert docs_write_time == 5400 # 1.5 hours docs
                
                # Total work time should be 6.75 hours
                total_web = web_project.get_today_record().total_seconds
                total_api = api_project.get_today_record().total_seconds
                total_docs = docs_project.get_today_record().total_seconds
                
                assert total_web == 7200    # 2 hours
                assert total_api == 8100    # 2.25 hours
                assert total_docs == 5400   # 1.5 hours
                
                total_day = total_web + total_api + total_docs
                assert total_day == 20700   # 5.75 hours total
    
    @pytest.mark.e2e
    def test_project_management_workflow(self, temp_config_dir):
        """Test complete project management workflow"""
        data_file = temp_config_dir / "project_mgmt.json"
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 1
            mock_config.is_backup_enabled.return_value = False
            mock_config.get_environment.return_value = Environment.DEVELOPMENT
            mock_get_config.return_value = mock_config
            
            manager = ProjectDataManager(data_file=str(data_file))
            
            # User creates initial project
            project1 = manager.add_project("Initial Project", "DZ001", "INIT")
            project1.add_sub_activity("Setup", "SETUP")
            project1.add_sub_activity("Development", "DEV")
            
            # User realizes they need a different project structure
            project2 = manager.add_project("Main Project", "DZ002", "MAIN")
            project2.add_sub_activity("Planning", "PLAN")
            project2.add_sub_activity("Implementation", "IMPL")
            project2.add_sub_activity("Review", "REVIEW")
            
            # User adds another project for different client
            project3 = manager.add_project("Client Work", "DZ003", "CLIENT")
            project3.add_sub_activity("Consultation", "CONSULT")
            project3.add_sub_activity("Development", "DEV")
            
            assert len(manager.projects) == 3
            
            # User does some work on different projects
            with patch('tick_tock_widget.project_data.datetime') as mock_datetime, \
                 patch('tick_tock_widget.project_data.date') as mock_date:
                
                work_date = date(2025, 8, 13)
                mock_date.today.return_value = work_date
                
                # Work on initial project
                mock_datetime.now.return_value = datetime(2025, 8, 13, 9, 0, 0)
                mock_datetime.fromisoformat.return_value = datetime(2025, 8, 13, 9, 0, 0)
                
                manager.set_current_project("INIT")
                manager.set_current_sub_activity("SETUP")
                manager.start_current_timer()
                
                mock_datetime.now.return_value = datetime(2025, 8, 13, 10, 0, 0)
                manager.stop_all_timers()
                
                # Realize initial project is no longer needed
                assert manager.remove_project("INIT") is True
                assert len(manager.projects) == 2
                
                # Current project should be cleared
                assert manager.current_project_alias != "INIT"
                
                # Continue with main project
                manager.set_current_project("MAIN")
                manager.set_current_sub_activity("PLAN")
                
                mock_datetime.now.return_value = datetime(2025, 8, 13, 11, 0, 0)
                mock_datetime.fromisoformat.return_value = datetime(2025, 8, 13, 11, 0, 0)
                manager.start_current_timer()
                
                mock_datetime.now.return_value = datetime(2025, 8, 13, 13, 0, 0)
                manager.stop_all_timers()
                
                # User modifies sub-activities for main project
                # Remove review (not needed yet)
                project2.remove_sub_activity("REVIEW")
                assert len(project2.sub_activities) == 2
                
                # Add new sub-activity
                project2.add_sub_activity("Testing", "TEST")
                assert len(project2.sub_activities) == 3
                
                # Verify remaining projects have correct time
                main_project = manager.get_project("MAIN")
                client_project = manager.get_project("CLIENT")
                
                assert main_project is not None
                assert client_project is not None
                
                main_time = main_project.get_today_record().total_seconds
                client_time = client_project.get_today_record().total_seconds
                
                assert main_time == 7200  # 2 hours on main project
                assert client_time == 0   # No work on client project yet
            
            # Save and verify final state
            manager.save_projects(force=True)
            
            # Reload and verify structure
            manager2 = ProjectDataManager(data_file=str(data_file))
            manager2.load_projects()
            assert len(manager2.projects) == 2
            
            project_aliases = [p.alias for p in manager2.projects]
            assert "MAIN" in project_aliases
            assert "CLIENT" in project_aliases
            assert "INIT" not in project_aliases  # Was removed
    
    @pytest.mark.e2e
    def test_environment_switching_scenario(self, temp_config_dir):
        """Test switching between development and production environments"""
        dev_file = temp_config_dir / "dev_data.json"
        prod_file = temp_config_dir / "prod_data.json"
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            # Start in development environment
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 1
            mock_config.is_backup_enabled.return_value = False
            mock_config.get_environment.return_value = Environment.DEVELOPMENT
            mock_config.set_environment = Mock()
            mock_config.save_config = Mock()
            mock_config.get_data_file.side_effect = [str(dev_file), str(prod_file)]
            mock_get_config.return_value = mock_config
            
            # User works in development environment
            dev_manager = ProjectDataManager(data_file=str(dev_file))
            
            # Create development projects
            dev_project = dev_manager.add_project("Feature Development", "DEV001", "FEATURE")
            test_project = dev_manager.add_project("Testing", "DEV002", "TEST")
            
            dev_project.add_sub_activity("Coding", "CODE")
            test_project.add_sub_activity("Unit Tests", "UNIT")
            
            # Do some development work
            with patch('tick_tock_widget.project_data.datetime') as mock_datetime, \
                 patch('tick_tock_widget.project_data.date') as mock_date:
                
                work_date = date(2025, 8, 13)
                mock_date.today.return_value = work_date
                
                mock_datetime.now.return_value = datetime(2025, 8, 13, 9, 0, 0)
                mock_datetime.fromisoformat.return_value = datetime(2025, 8, 13, 9, 0, 0)
                
                dev_manager.set_current_project("FEATURE")
                dev_manager.set_current_sub_activity("CODE")
                dev_manager.start_current_timer()
                
                mock_datetime.now.return_value = datetime(2025, 8, 13, 12, 0, 0)
                dev_manager.stop_all_timers()
            
            # Save development work
            dev_manager.save_projects(force=True)
            assert dev_file.exists()
            
            # Switch to production environment
            # Mock the data file change
            mock_config.get_data_file.side_effect = None
            mock_config.get_data_file.return_value = str(prod_file)
            
            result = dev_manager.switch_environment(Environment.PRODUCTION)
            assert result is True
            
            # Verify environment switch was called
            mock_config.set_environment.assert_called_with(Environment.PRODUCTION)
            mock_config.save_config.assert_called_once()
            
            # User should now be in production environment with empty data
            # (since production data file doesn't exist yet)
            assert len(dev_manager.projects) == 0  # Should reload empty for production
            
            # Create production projects (different from dev)
            prod_project = dev_manager.add_project("Production Bug Fix", "PROD001", "BUGFIX")
            prod_project.add_sub_activity("Investigation", "INVEST")
            prod_project.add_sub_activity("Fix", "FIX")
            
            # Do production work
            with patch('tick_tock_widget.project_data.datetime') as mock_datetime2, \
                 patch('tick_tock_widget.project_data.date') as mock_date2:
                
                mock_date2.today.return_value = work_date
                
                mock_datetime2.now.return_value = datetime(2025, 8, 13, 14, 0, 0)
                mock_datetime2.fromisoformat.return_value = datetime(2025, 8, 13, 14, 0, 0)
                
                dev_manager.set_current_project("BUGFIX")
                dev_manager.set_current_sub_activity("INVEST")
                dev_manager.start_current_timer()
                
                mock_datetime2.now.return_value = datetime(2025, 8, 13, 16, 0, 0)
                dev_manager.stop_all_timers()
            
            # Save production work
            dev_manager.save_projects(force=True)
            
            # Verify both environments have separate data
            assert dev_file.exists()
            assert prod_file.exists()
            
            # Check development data is preserved
            with open(dev_file, 'r') as f:
                dev_data = json.load(f)
                assert len(dev_data["projects"]) == 2
                dev_aliases = [p["alias"] for p in dev_data["projects"]]
                assert "FEATURE" in dev_aliases
                assert "TEST" in dev_aliases
            
            # Check production data is separate
            with open(prod_file, 'r') as f:
                prod_data = json.load(f)
                assert len(prod_data["projects"]) == 1
                assert prod_data["projects"][0]["alias"] == "BUGFIX"
