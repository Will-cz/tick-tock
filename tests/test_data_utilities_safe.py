"""
Safe data utility tests - No GUI creation
Tests data processing utilities without any widget creation
"""

import unittest
import tempfile
import os
from pathlib import Path
from datetime import datetime, date

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tick_tock_widget.project_data import TimeRecord, SubActivity, Project


class TestDataUtilities(unittest.TestCase):
    """Test data processing utility functions"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_file = Path(self.temp_dir) / "test_data.json"
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except (FileNotFoundError, OSError):
            pass
    
    def test_time_record_creation(self):
        """Test TimeRecord creation and basic functionality"""
        today_str = date.today().isoformat()
        
        record = TimeRecord(date=today_str, total_seconds=3600)  # 1 hour
        
        # Test basic properties
        self.assertEqual(record.date, today_str)
        self.assertEqual(record.total_seconds, 3600)
        self.assertFalse(record.is_running)
        self.assertIsNone(record.last_started)
    
    def test_time_record_formatting(self):
        """Test time formatting in TimeRecord"""
        today_str = date.today().isoformat()
        
        # Test various time values
        test_cases = [
            (3600, "01:00:00"),    # 1 hour
            (7200, "02:00:00"),    # 2 hours
            (3661, "01:01:01"),    # 1 hour, 1 minute, 1 second
            (90, "00:01:30"),      # 1.5 minutes
            (0, "00:00:00")        # Zero time
        ]
        
        for seconds, expected_format in test_cases:
            record = TimeRecord(date=today_str, total_seconds=seconds)
            formatted_time = record.get_formatted_time()
            self.assertEqual(formatted_time, expected_format)
    
    def test_time_record_add_time(self):
        """Test adding time to TimeRecord"""
        today_str = date.today().isoformat()
        record = TimeRecord(date=today_str, total_seconds=1800)  # 30 minutes
        
        # Add 30 more minutes
        record.add_time(1800)
        
        self.assertEqual(record.total_seconds, 3600)  # 1 hour total
        self.assertEqual(record.get_formatted_time(), "01:00:00")
    
    def test_sub_activity_creation(self):
        """Test SubActivity creation"""
        sub_activity = SubActivity(
            name="Development",
            alias="Dev",
            time_records={}
        )
        
        self.assertEqual(sub_activity.name, "Development")
        self.assertEqual(sub_activity.alias, "Dev")
        self.assertEqual(len(sub_activity.time_records), 0)
    
    def test_sub_activity_today_record(self):
        """Test getting today's record from SubActivity"""
        sub_activity = SubActivity(
            name="Testing",
            alias="Test",
            time_records={}
        )
        
        # Get today's record (should create if doesn't exist)
        today_record = sub_activity.get_today_record()
        
        self.assertIsInstance(today_record, TimeRecord)
        self.assertEqual(today_record.date, date.today().isoformat())
        self.assertEqual(today_record.total_seconds, 0)
        
        # Should return same record on subsequent calls
        same_record = sub_activity.get_today_record()
        self.assertIs(today_record, same_record)
    
    def test_project_creation(self):
        """Test Project creation"""
        project = Project(
            name="Test Project",
            dz_number="DZ-001",
            alias="TestProj",
            time_records={},
            sub_activities=[]
        )
        
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.dz_number, "DZ-001")
        self.assertEqual(project.alias, "TestProj")
        self.assertEqual(len(project.sub_activities), 0)
    
    def test_project_with_sub_activities(self):
        """Test Project with SubActivities"""
        # Create sub-activities
        dev_activity = SubActivity(
            name="Development",
            alias="Dev",
            time_records={}
        )
        
        test_activity = SubActivity(
            name="Testing",
            alias="Test",
            time_records={}
        )
        
        # Create project with sub-activities
        project = Project(
            name="Test Project",
            dz_number="DZ-001",
            alias="TestProj",
            time_records={},
            sub_activities=[dev_activity, test_activity]
        )
        
        self.assertEqual(len(project.sub_activities), 2)
        self.assertEqual(project.sub_activities[0].name, "Development")
        self.assertEqual(project.sub_activities[1].name, "Testing")
    
    def test_time_record_timing_simulation(self):
        """Test timing functionality without actually waiting"""
        today_str = date.today().isoformat()
        record = TimeRecord(date=today_str)
        
        # Simulate starting timing
        record.start_timing()
        self.assertTrue(record.is_running)
        self.assertIsNotNone(record.last_started)
        
        # Simulate stopping timing (manually add some time)
        record.add_time(300)  # Add 5 minutes manually
        record.stop_timing()
        
        self.assertFalse(record.is_running)
        self.assertIsNone(record.last_started)
        self.assertGreaterEqual(record.total_seconds, 300)
    
    def test_sub_activity_dict_conversion(self):
        """Test SubActivity with dict-based time records (JSON loading simulation)"""
        # Simulate loading from JSON where time_records is a dict
        today_str = date.today().isoformat()
        record_dict = {
            'date': today_str,
            'total_seconds': 3600,
            'is_running': False,
            'last_started': None,
            'sub_activity_seconds': {}
        }
        
        sub_activity = SubActivity(
            name="Development",
            alias="Dev",
            time_records={today_str: record_dict}
        )
        
        # Should convert dict to TimeRecord object
        today_record = sub_activity.get_today_record()
        self.assertIsInstance(today_record, TimeRecord)
        self.assertEqual(today_record.total_seconds, 3600)
    
    def test_data_validation_utilities(self):
        """Test data validation utility functions"""
        # Test valid project data structure
        valid_project_data = {
            "name": "Test Project",
            "dz_number": "DZ-001",
            "alias": "TestProj",
            "time_records": {},
            "sub_activities": []
        }
        
        self.assertTrue(self._validate_project_data(valid_project_data))
        
        # Test invalid project data - missing required fields
        invalid_project_data = {
            "name": "Test Project"
            # Missing required fields
        }
        
        self.assertFalse(self._validate_project_data(invalid_project_data))
    
    def _validate_project_data(self, data: dict) -> bool:
        """Validate project data structure"""
        required_fields = ['name', 'dz_number', 'alias']
        return all(field in data for field in required_fields)
    
    def test_time_formatting_utilities(self):
        """Test time formatting utility functions"""
        # Test seconds to time string conversion
        test_cases = [
            (3600, "01:00:00"),    # 1 hour
            (1800, "00:30:00"),    # 30 minutes
            (90, "00:01:30"),      # 1.5 minutes
            (3661, "01:01:01"),    # 1h 1m 1s
            (0, "00:00:00")        # Zero
        ]
        
        for seconds, expected in test_cases:
            time_str = self._format_seconds(seconds)
            self.assertEqual(time_str, expected)
    
    def _format_seconds(self, total_seconds: int) -> str:
        """Format seconds as HH:MM:SS"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def test_date_handling_utilities(self):
        """Test date handling utilities"""
        # Test date string formatting
        today = date.today()
        today_str = today.isoformat()
        
        self.assertIsInstance(today_str, str)
        self.assertEqual(len(today_str), 10)  # YYYY-MM-DD format
        self.assertRegex(today_str, r'\d{4}-\d{2}-\d{2}')
        
        # Test date parsing
        parsed_date = date.fromisoformat(today_str)
        self.assertEqual(parsed_date, today)
    
    def test_data_structure_consistency(self):
        """Test consistency between data structures"""
        today_str = date.today().isoformat()
        
        # Create a complete data structure
        record = TimeRecord(date=today_str, total_seconds=7200)  # 2 hours
        
        sub_activity = SubActivity(
            name="Development",
            alias="Dev",
            time_records={today_str: record}
        )
        
        project = Project(
            name="Test Project",
            dz_number="DZ-001",
            alias="TestProj",
            time_records={today_str: record},
            sub_activities=[sub_activity]
        )
        
        # Test consistency
        self.assertEqual(record.date, today_str)
        self.assertEqual(sub_activity.time_records[today_str], record)
        self.assertEqual(project.sub_activities[0], sub_activity)
        self.assertEqual(project.time_records[today_str], record)


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
