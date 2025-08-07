"""
Enhanced tests for project data management functionality
"""

import unittest
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime, date
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tick_tock_widget.project_data import ProjectDataManager, Project, SubActivity, TimeRecord


class TestTimeRecord(unittest.TestCase):
    """Test TimeRecord functionality"""
    
    def test_time_record_creation(self):
        """Test creating a time record"""
        record = TimeRecord(date="2025-01-01")
        self.assertEqual(record.date, "2025-01-01")
        self.assertEqual(record.total_seconds, 0)
        self.assertFalse(record.is_running)
        self.assertIsNone(record.last_started)
        self.assertEqual(record.sub_activity_seconds, {})
    
    def test_time_record_with_initial_values(self):
        """Test creating a time record with initial values"""
        record = TimeRecord(
            date="2025-01-01",
            total_seconds=3600,
            is_running=True,
            sub_activity_seconds={'dev': 1800}
        )
        self.assertEqual(record.total_seconds, 3600)
        self.assertTrue(record.is_running)
        self.assertEqual(record.sub_activity_seconds['dev'], 1800)
    
    def test_add_time(self):
        """Test adding time to a record"""
        record = TimeRecord(date="2025-01-01")
        record.add_time(3600)  # 1 hour
        self.assertEqual(record.total_seconds, 3600)
        
        record.add_time(1800)  # 30 minutes more
        self.assertEqual(record.total_seconds, 5400)
    
    def test_formatted_time(self):
        """Test time formatting"""
        record = TimeRecord(date="2025-01-01", total_seconds=3661)  # 1:01:01
        self.assertEqual(record.get_formatted_time(), "01:01:01")
        
        # Test edge cases
        record.total_seconds = 0
        self.assertEqual(record.get_formatted_time(), "00:00:00")
        
        record.total_seconds = 86400  # 24 hours
        self.assertEqual(record.get_formatted_time(), "24:00:00")
        
        record.total_seconds = 59
        self.assertEqual(record.get_formatted_time(), "00:00:59")
    
    def test_start_timing(self):
        """Test starting timing on a record"""
        record = TimeRecord(date="2025-01-01")
        record.start_timing()
        
        self.assertTrue(record.is_running)
        self.assertIsNotNone(record.last_started)
        
        # Verify ISO format timestamp
        start_time = datetime.fromisoformat(record.last_started)
        self.assertIsInstance(start_time, datetime)
    
    def test_stop_timing(self):
        """Test stopping timing on a record"""
        record = TimeRecord(date="2025-01-01")
        record.start_timing()
        
        # Wait a short time to accumulate some seconds
        time.sleep(0.1)
        
        initial_total = record.total_seconds
        record.stop_timing()
        
        self.assertFalse(record.is_running)
        self.assertIsNone(record.last_started)
        self.assertGreater(record.total_seconds, initial_total)
    
    def test_get_current_total_seconds_running(self):
        """Test getting current total when timer is running"""
        record = TimeRecord(date="2025-01-01", total_seconds=1000)
        record.start_timing()
        
        # Wait briefly and check that current total includes running time
        time.sleep(0.1)
        current_total = record.get_current_total_seconds()
        self.assertGreater(current_total, 1000)
    
    def test_get_current_total_seconds_not_running(self):
        """Test getting current total when timer is not running"""
        record = TimeRecord(date="2025-01-01", total_seconds=1000)
        current_total = record.get_current_total_seconds()
        self.assertEqual(current_total, 1000)


class TestSubActivity(unittest.TestCase):
    """Test SubActivity functionality"""
    
    def test_sub_activity_creation(self):
        """Test creating a sub-activity"""
        sub_activity = SubActivity(name="Testing", alias="test", time_records={})
        self.assertEqual(sub_activity.name, "Testing")
        self.assertEqual(sub_activity.alias, "test")
        self.assertEqual(len(sub_activity.time_records), 0)
    
    def test_sub_activity_with_existing_records(self):
        """Test creating sub-activity with existing time records"""
        records = {
            "2025-01-01": TimeRecord(date="2025-01-01", total_seconds=3600)
        }
        sub_activity = SubActivity(name="Testing", alias="test", time_records=records)
        self.assertEqual(len(sub_activity.time_records), 1)
        self.assertIn("2025-01-01", sub_activity.time_records)
    
    def test_get_today_record(self):
        """Test getting today's record for sub-activity"""
        sub_activity = SubActivity(name="Testing", alias="test", time_records={})
        today_record = sub_activity.get_today_record()
        
        self.assertEqual(today_record.date, date.today().isoformat())
        self.assertIn(date.today().isoformat(), sub_activity.time_records)
    
    def test_get_total_time_today(self):
        """Test getting formatted total time for today"""
        sub_activity = SubActivity(name="Testing", alias="test", time_records={})
        today_record = sub_activity.get_today_record()
        today_record.total_seconds = 3661
        
        total_time = sub_activity.get_total_time_today()
        self.assertEqual(total_time, "01:01:01")
    
    def test_is_running_today(self):
        """Test checking if sub-activity is running today"""
        sub_activity = SubActivity(name="Testing", alias="test", time_records={})
        
        # Initially not running
        self.assertFalse(sub_activity.is_running_today())
        
        # Start timing
        today_record = sub_activity.get_today_record()
        today_record.start_timing()
        
        self.assertTrue(sub_activity.is_running_today())
    
    def test_post_init_dict_conversion(self):
        """Test __post_init__ conversion from dict to TimeRecord objects"""
        # Simulate loading from JSON
        dict_records = {
            "2025-01-01": {
                "date": "2025-01-01",
                "total_seconds": 3600,
                "is_running": False,
                "last_started": None,
                "sub_activity_seconds": {}
            }
        }
        
        sub_activity = SubActivity(name="Testing", alias="test", time_records=dict_records)
        
        # Verify conversion happened
        self.assertIsInstance(sub_activity.time_records["2025-01-01"], TimeRecord)
        self.assertEqual(sub_activity.time_records["2025-01-01"].total_seconds, 3600)


class TestProject(unittest.TestCase):
    """Test Project functionality"""
    
    def test_project_creation(self):
        """Test creating a project"""
        project = Project(
            name="Test Project",
            dz_number="12345",
            alias="test",
            sub_activities=[],
            time_records={}
        )
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.dz_number, "12345")
        self.assertEqual(project.alias, "test")
        self.assertEqual(len(project.sub_activities), 0)
        self.assertEqual(len(project.time_records), 0)
    
    def test_project_with_existing_data(self):
        """Test creating project with existing data"""
        sub_activities = [
            SubActivity(name="Development", alias="dev", time_records={})
        ]
        time_records = {
            "2025-01-01": TimeRecord(date="2025-01-01", total_seconds=7200)
        }
        
        project = Project(
            name="Test Project",
            dz_number="12345",
            alias="test",
            sub_activities=sub_activities,
            time_records=time_records
        )
        
        self.assertEqual(len(project.sub_activities), 1)
        self.assertEqual(len(project.time_records), 1)
    
    def test_add_sub_activity(self):
        """Test adding a sub-activity to a project"""
        project = Project(
            name="Test Project",
            dz_number="12345", 
            alias="test",
            sub_activities=[],
            time_records={}
        )
        
        sub_activity = project.add_sub_activity("Development", "dev")
        
        self.assertEqual(len(project.sub_activities), 1)
        self.assertEqual(sub_activity.name, "Development")
        self.assertEqual(sub_activity.alias, "dev")
        self.assertIn(sub_activity, project.sub_activities)
    
    def test_remove_sub_activity(self):
        """Test removing a sub-activity from a project"""
        project = Project(
            name="Test Project",
            dz_number="12345",
            alias="test",
            sub_activities=[],
            time_records={}
        )
        
        # Add sub-activity
        project.add_sub_activity("Development", "dev")
        project.add_sub_activity("Testing", "test")
        self.assertEqual(len(project.sub_activities), 2)
        
        # Remove one
        result = project.remove_sub_activity("dev")
        self.assertTrue(result)
        self.assertEqual(len(project.sub_activities), 1)
        self.assertEqual(project.sub_activities[0].alias, "test")
        
        # Try to remove non-existent
        result = project.remove_sub_activity("nonexistent")
        self.assertFalse(result)
        self.assertEqual(len(project.sub_activities), 1)
    
    def test_get_sub_activity(self):
        """Test getting a sub-activity by alias"""
        project = Project(
            name="Test Project",
            dz_number="12345",
            alias="test", 
            sub_activities=[],
            time_records={}
        )
        
        project.add_sub_activity("Development", "dev")
        project.add_sub_activity("Testing", "test_sub")
        
        # Get existing sub-activity
        sub_activity = project.get_sub_activity("dev")
        self.assertIsNotNone(sub_activity)
        self.assertEqual(sub_activity.alias, "dev")
        
        # Try to get non-existent
        sub_activity = project.get_sub_activity("nonexistent")
        self.assertIsNone(sub_activity)
    
    def test_get_today_record(self):
        """Test getting today's record for project"""
        project = Project(
            name="Test Project",
            dz_number="12345",
            alias="test",
            sub_activities=[],
            time_records={}
        )
        
        today_record = project.get_today_record()
        self.assertEqual(today_record.date, date.today().isoformat())
        self.assertIn(date.today().isoformat(), project.time_records)
    
    def test_get_total_time_today(self):
        """Test getting formatted total time for today"""
        project = Project(
            name="Test Project",
            dz_number="12345",
            alias="test",
            sub_activities=[],
            time_records={}
        )
        
        today_record = project.get_today_record()
        today_record.total_seconds = 7200  # 2 hours
        
        total_time = project.get_total_time_today()
        self.assertEqual(total_time, "02:00:00")
    
    def test_is_running_today(self):
        """Test checking if project is running today"""
        project = Project(
            name="Test Project",
            dz_number="12345",
            alias="test",
            sub_activities=[],
            time_records={}
        )
        
        # Initially not running
        self.assertFalse(project.is_running_today())
        
        # Start timing
        today_record = project.get_today_record()
        today_record.start_timing()
        
        self.assertTrue(project.is_running_today())
    
    def test_post_init_dict_conversion(self):
        """Test __post_init__ conversion from dict to proper objects"""
        # Simulate loading from JSON - sub_activities as dicts
        dict_sub_activities = [
            {
                "name": "Development",
                "alias": "dev",
                "time_records": {}
            }
        ]
        
        # time_records as dicts
        dict_time_records = {
            "2025-01-01": {
                "date": "2025-01-01",
                "total_seconds": 3600,
                "is_running": False,
                "last_started": None,
                "sub_activity_seconds": {}
            }
        }
        
        project = Project(
            name="Test Project",
            dz_number="12345",
            alias="test",
            sub_activities=dict_sub_activities,
            time_records=dict_time_records
        )
        
        # Verify conversions
        self.assertIsInstance(project.sub_activities[0], SubActivity)
        self.assertEqual(project.sub_activities[0].name, "Development")
        
        self.assertIsInstance(project.time_records["2025-01-01"], TimeRecord)
        self.assertEqual(project.time_records["2025-01-01"].total_seconds, 3600)


class TestProjectDataManager(unittest.TestCase):
    """Test ProjectDataManager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.data_manager = ProjectDataManager(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test environment"""
        if Path(self.temp_file.name).exists():
            Path(self.temp_file.name).unlink()
    
    def test_initialization(self):
        """Test ProjectDataManager initialization"""
        self.assertEqual(self.data_manager.data_file, Path(self.temp_file.name))
        self.assertEqual(len(self.data_manager.projects), 0)
        self.assertIsNone(self.data_manager.current_project_alias)
        self.assertIsNone(self.data_manager.current_sub_activity_alias)
        self.assertEqual(self.data_manager.auto_save_interval, 30)
    
    def test_add_project(self):
        """Test adding a project"""
        project = self.data_manager.add_project("Test Project", "12345", "test")
        
        self.assertIsNotNone(project)
        self.assertEqual(len(self.data_manager.projects), 1)
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.dz_number, "12345")
        self.assertEqual(project.alias, "test")
    
    def test_add_project_empty_alias(self):
        """Test adding project with empty alias uses name"""
        project = self.data_manager.add_project("Test Project", "12345", "")
        
        self.assertIsNotNone(project)
        self.assertEqual(project.alias, "Test Project")
    
    def test_add_project_duplicate_alias(self):
        """Test adding project with duplicate alias"""
        # Add first project
        project1 = self.data_manager.add_project("Test Project 1", "12345", "test")
        self.assertIsNotNone(project1)
        
        # Try to add second project with same alias
        project2 = self.data_manager.add_project("Test Project 2", "67890", "test")
        self.assertIsNone(project2)
        self.assertEqual(len(self.data_manager.projects), 1)
    
    def test_get_project(self):
        """Test getting a project by alias"""
        self.data_manager.add_project("Test Project", "12345", "test")
        
        project = self.data_manager.get_project("test")
        self.assertIsNotNone(project)
        self.assertEqual(project.alias, "test")
        
        # Try non-existent project
        project = self.data_manager.get_project("nonexistent")
        self.assertIsNone(project)
    
    def test_remove_project(self):
        """Test removing a project"""
        self.data_manager.add_project("Test Project", "12345", "test")
        self.assertEqual(len(self.data_manager.projects), 1)
        
        result = self.data_manager.remove_project("test")
        self.assertTrue(result)
        self.assertEqual(len(self.data_manager.projects), 0)
        
        # Try removing non-existent project
        result = self.data_manager.remove_project("nonexistent")
        self.assertFalse(result)
    
    def test_remove_current_project(self):
        """Test removing currently selected project"""
        self.data_manager.add_project("Test Project", "12345", "test")
        self.data_manager.set_current_project("test")
        self.data_manager.set_current_sub_activity("sub1")
        
        # Verify current selections
        self.assertEqual(self.data_manager.current_project_alias, "test")
        self.assertEqual(self.data_manager.current_sub_activity_alias, "sub1")
        
        # Remove the current project
        result = self.data_manager.remove_project("test")
        self.assertTrue(result)
        
        # Verify current selections are cleared
        self.assertIsNone(self.data_manager.current_project_alias)
        self.assertIsNone(self.data_manager.current_sub_activity_alias)
    
    def test_set_current_project(self):
        """Test setting current project"""
        self.data_manager.add_project("Test Project", "12345", "test")
        
        result = self.data_manager.set_current_project("test")
        self.assertTrue(result)
        self.assertEqual(self.data_manager.current_project_alias, "test")
        
        # Setting current project should clear sub-activity
        self.data_manager.current_sub_activity_alias = "some_sub"
        result = self.data_manager.set_current_project("test")
        self.assertTrue(result)
        self.assertIsNone(self.data_manager.current_sub_activity_alias)
        
        # Try setting non-existent project
        result = self.data_manager.set_current_project("nonexistent")
        self.assertFalse(result)
    
    def test_set_current_sub_activity(self):
        """Test setting current sub-activity"""
        project = self.data_manager.add_project("Test Project", "12345", "test")
        project.add_sub_activity("Development", "dev")
        self.data_manager.set_current_project("test")
        
        result = self.data_manager.set_current_sub_activity("dev")
        self.assertTrue(result)
        self.assertEqual(self.data_manager.current_sub_activity_alias, "dev")
        
        # Test clearing sub-activity
        result = self.data_manager.set_current_sub_activity(None)
        self.assertTrue(result)
        self.assertIsNone(self.data_manager.current_sub_activity_alias)
        
        # Try setting non-existent sub-activity
        result = self.data_manager.set_current_sub_activity("nonexistent")
        self.assertFalse(result)
    
    def test_get_current_project(self):
        """Test getting current project"""
        # No current project
        self.assertIsNone(self.data_manager.get_current_project())
        
        # Set current project
        self.data_manager.add_project("Test Project", "12345", "test")
        self.data_manager.set_current_project("test")
        
        current = self.data_manager.get_current_project()
        self.assertIsNotNone(current)
        self.assertEqual(current.alias, "test")
    
    def test_get_current_sub_activity(self):
        """Test getting current sub-activity"""
        # No current project or sub-activity
        self.assertIsNone(self.data_manager.get_current_sub_activity())
        
        # Set current project but no sub-activity
        project = self.data_manager.add_project("Test Project", "12345", "test")
        self.data_manager.set_current_project("test")
        self.assertIsNone(self.data_manager.get_current_sub_activity())
        
        # Add and set current sub-activity
        project.add_sub_activity("Development", "dev")
        self.data_manager.set_current_sub_activity("dev")
        
        current = self.data_manager.get_current_sub_activity()
        self.assertIsNotNone(current)
        self.assertEqual(current.alias, "dev")
    
    def test_start_current_timer(self):
        """Test starting current timer"""
        # No current project
        result = self.data_manager.start_current_timer()
        self.assertFalse(result)
        
        # With current project only
        project = self.data_manager.add_project("Test Project", "12345", "test")
        self.data_manager.set_current_project("test")
        
        result = self.data_manager.start_current_timer()
        self.assertTrue(result)
        self.assertTrue(project.is_running_today())
        
        # With current project and sub-activity
        sub_activity = project.add_sub_activity("Development", "dev")
        self.data_manager.set_current_sub_activity("dev")
        
        result = self.data_manager.start_current_timer()
        self.assertTrue(result)
        self.assertTrue(project.is_running_today())
        self.assertTrue(sub_activity.is_running_today())
    
    def test_stop_all_timers(self):
        """Test stopping all timers"""
        # Create multiple projects with running timers
        project1 = self.data_manager.add_project("Project 1", "123", "proj1")
        project2 = self.data_manager.add_project("Project 2", "456", "proj2")
        
        sub1 = project1.add_sub_activity("Dev1", "dev1")
        sub2 = project2.add_sub_activity("Dev2", "dev2")
        
        # Start timers
        project1.get_today_record().start_timing()
        project2.get_today_record().start_timing()
        sub1.get_today_record().start_timing()
        sub2.get_today_record().start_timing()
        
        # Verify all are running
        self.assertTrue(project1.is_running_today())
        self.assertTrue(project2.is_running_today())
        self.assertTrue(sub1.is_running_today())
        self.assertTrue(sub2.is_running_today())
        
        # Stop all
        self.data_manager.stop_all_timers()
        
        # Verify all are stopped
        self.assertFalse(project1.is_running_today())
        self.assertFalse(project2.is_running_today())
        self.assertFalse(sub1.is_running_today())
        self.assertFalse(sub2.is_running_today())
    
    def test_get_project_aliases(self):
        """Test getting list of project aliases"""
        self.assertEqual(len(self.data_manager.get_project_aliases()), 0)
        
        self.data_manager.add_project("Project 1", "123", "proj1")
        self.data_manager.add_project("Project 2", "456", "proj2")
        
        aliases = self.data_manager.get_project_aliases()
        self.assertEqual(len(aliases), 2)
        self.assertIn("proj1", aliases)
        self.assertIn("proj2", aliases)
    
    def test_save_and_load_projects(self):
        """Test saving and loading projects"""
        # Add test data
        project = self.data_manager.add_project("Test Project", "12345", "test")
        project.add_sub_activity("Development", "dev")
        project.get_today_record().add_time(3600)
        
        self.data_manager.set_current_project("test")
        self.data_manager.set_current_sub_activity("dev")
        
        # Save to file
        result = self.data_manager.save_projects(force=True)
        self.assertTrue(result)
        
        # Create new manager and load
        new_manager = ProjectDataManager(self.temp_file.name)
        result = new_manager.load_projects()
        self.assertTrue(result)
        
        # Verify data was loaded correctly
        self.assertEqual(len(new_manager.projects), 1)
        
        loaded_project = new_manager.get_project("test")
        self.assertIsNotNone(loaded_project)
        self.assertEqual(loaded_project.name, "Test Project")
        self.assertEqual(loaded_project.dz_number, "12345")
        self.assertEqual(len(loaded_project.sub_activities), 1)
        self.assertEqual(loaded_project.sub_activities[0].alias, "dev")
        
        self.assertEqual(new_manager.current_project_alias, "test")
        self.assertEqual(new_manager.current_sub_activity_alias, "dev")
    
    def test_load_projects_no_file(self):
        """Test loading when no file exists"""
        # Use non-existent file
        manager = ProjectDataManager("nonexistent_file.json")
        result = manager.load_projects()
        self.assertFalse(result)
        self.assertEqual(len(manager.projects), 0)
    
    def test_save_projects_auto_save_interval(self):
        """Test auto-save interval behavior"""
        self.data_manager.add_project("Test Project", "12345", "test")
        
        # First save should work
        result = self.data_manager.save_projects(force=False)
        self.assertTrue(result)
        
        # Immediate second save should be skipped due to interval
        result = self.data_manager.save_projects(force=False)
        self.assertFalse(result)
        
        # Forced save should work regardless of interval
        result = self.data_manager.save_projects(force=True)
        self.assertTrue(result)
    
    def test_project_to_dict(self):
        """Test converting project to dictionary"""
        project = self.data_manager.add_project("Test Project", "12345", "test")
        sub_activity = project.add_sub_activity("Development", "dev")
        
        # Add some time data
        project.get_today_record().add_time(3600)
        sub_activity.get_today_record().add_time(1800)
        
        project_dict = self.data_manager._project_to_dict(project)
        
        # Verify structure
        self.assertIn('name', project_dict)
        self.assertIn('dz_number', project_dict)
        self.assertIn('alias', project_dict)
        self.assertIn('sub_activities', project_dict)
        self.assertIn('time_records', project_dict)
        
        self.assertEqual(project_dict['name'], "Test Project")
        self.assertEqual(len(project_dict['sub_activities']), 1)
        self.assertEqual(project_dict['sub_activities'][0]['alias'], "dev")
    
    @patch('builtins.print')
    def test_error_handling_load(self, mock_print):
        """Test error handling during load"""
        # Create invalid JSON file
        with open(self.temp_file.name, 'w') as f:
            f.write("invalid json")
        
        result = self.data_manager.load_projects()
        self.assertFalse(result)
        
        # Check that error was printed
        mock_print.assert_called()
        args = str(mock_print.call_args_list)
        self.assertIn("Error loading projects", args)
    
    @patch('builtins.print')
    def test_error_handling_save(self, mock_print):
        """Test error handling during save"""
        # Use invalid file path to trigger save error
        self.data_manager.data_file = Path("/invalid/path/file.json")
        
        result = self.data_manager.save_projects(force=True)
        self.assertFalse(result)
        
        # Check that error was printed
        mock_print.assert_called()
        args = str(mock_print.call_args_list)
        self.assertIn("Error saving projects", args)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for common usage scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.data_manager = ProjectDataManager(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test environment"""
        if Path(self.temp_file.name).exists():
            Path(self.temp_file.name).unlink()
    
    def test_typical_workflow(self):
        """Test a typical time tracking workflow"""
        # 1. Add projects
        project1 = self.data_manager.add_project("Client Website", "WEB-001", "web")
        project2 = self.data_manager.add_project("Mobile App", "APP-002", "app")
        
        # 2. Add sub-activities
        project1.add_sub_activity("Frontend Development", "frontend")
        project1.add_sub_activity("Backend Development", "backend")
        project2.add_sub_activity("UI Design", "ui")
        
        # 3. Start working on web project frontend
        self.data_manager.set_current_project("web")
        self.data_manager.set_current_sub_activity("frontend")
        self.data_manager.start_current_timer()
        
        # Verify timer is running
        self.assertTrue(project1.is_running_today())
        self.assertTrue(project1.get_sub_activity("frontend").is_running_today())
        
        # 4. Switch to backend work
        self.data_manager.set_current_sub_activity("backend")
        self.data_manager.start_current_timer()
        
        # Verify frontend stopped, backend started
        self.assertFalse(project1.get_sub_activity("frontend").is_running_today())
        self.assertTrue(project1.get_sub_activity("backend").is_running_today())
        
        # 5. Switch to different project
        self.data_manager.set_current_project("app")
        self.data_manager.set_current_sub_activity("ui")
        self.data_manager.start_current_timer()
        
        # Verify all web project timers stopped
        self.assertFalse(project1.is_running_today())
        self.assertFalse(project1.get_sub_activity("frontend").is_running_today())
        self.assertFalse(project1.get_sub_activity("backend").is_running_today())
        
        # Verify app project started
        self.assertTrue(project2.is_running_today())
        self.assertTrue(project2.get_sub_activity("ui").is_running_today())
        
        # 6. Save and verify persistence
        self.data_manager.save_projects(force=True)
        
        new_manager = ProjectDataManager(self.temp_file.name)
        new_manager.load_projects()
        
        self.assertEqual(len(new_manager.projects), 2)
        self.assertEqual(new_manager.current_project_alias, "app")
        self.assertEqual(new_manager.current_sub_activity_alias, "ui")
    
    def test_multi_day_tracking(self):
        """Test tracking across multiple days"""
        project = self.data_manager.add_project("Long Project", "LONG-001", "long")
        sub_activity = project.add_sub_activity("Development", "dev")
        
        # Simulate work on day 1
        day1_record = TimeRecord(date="2025-01-01", total_seconds=28800)  # 8 hours
        project.time_records["2025-01-01"] = day1_record
        sub_activity.time_records["2025-01-01"] = TimeRecord(date="2025-01-01", total_seconds=14400)  # 4 hours
        
        # Simulate work on day 2
        day2_record = TimeRecord(date="2025-01-02", total_seconds=25200)  # 7 hours
        project.time_records["2025-01-02"] = day2_record
        sub_activity.time_records["2025-01-02"] = TimeRecord(date="2025-01-02", total_seconds=18000)  # 5 hours
        
        # Verify data integrity
        self.assertEqual(len(project.time_records), 2)
        self.assertEqual(len(sub_activity.time_records), 2)
        
        # Test persistence
        self.data_manager.save_projects(force=True)
        
        new_manager = ProjectDataManager(self.temp_file.name)
        new_manager.load_projects()
        
        loaded_project = new_manager.get_project("long")
        loaded_sub = loaded_project.get_sub_activity("dev")
        
        self.assertEqual(len(loaded_project.time_records), 2)
        self.assertEqual(len(loaded_sub.time_records), 2)
        self.assertEqual(loaded_project.time_records["2025-01-01"].total_seconds, 28800)
        self.assertEqual(loaded_sub.time_records["2025-01-02"].total_seconds, 18000)
    
    def test_complex_project_structure(self):
        """Test complex project with multiple sub-activities"""
        project = self.data_manager.add_project("Complex Project", "COMP-001", "complex")
        
        # Add multiple sub-activities
        sub_activities = [
            ("Requirements Analysis", "req"),
            ("System Design", "design"),
            ("Frontend Development", "frontend"),
            ("Backend Development", "backend"),
            ("Testing", "test"),
            ("Documentation", "docs"),
            ("Deployment", "deploy")
        ]
        
        for name, alias in sub_activities:
            project.add_sub_activity(name, alias)
        
        self.assertEqual(len(project.sub_activities), 7)
        
        # Test getting each sub-activity
        for name, alias in sub_activities:
            sub = project.get_sub_activity(alias)
            self.assertIsNotNone(sub)
            self.assertEqual(sub.name, name)
            self.assertEqual(sub.alias, alias)
        
        # Test removing sub-activities
        project.remove_sub_activity("deploy")
        self.assertEqual(len(project.sub_activities), 6)
        self.assertIsNone(project.get_sub_activity("deploy"))
        
        # Test persistence of complex structure
        self.data_manager.save_projects(force=True)
        
        new_manager = ProjectDataManager(self.temp_file.name)
        new_manager.load_projects()
        
        loaded_project = new_manager.get_project("complex")
        self.assertEqual(len(loaded_project.sub_activities), 6)
        
        # Verify all sub-activities loaded correctly
        for name, alias in sub_activities[:-1]:  # Exclude the removed one
            sub = loaded_project.get_sub_activity(alias)
            self.assertIsNotNone(sub)
            self.assertEqual(sub.name, name)


if __name__ == '__main__':
    unittest.main()
