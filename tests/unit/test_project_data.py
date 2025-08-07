"""
Unit tests for ProjectDataManager and related classes
"""
import pytest
from unittest.mock import Mock, patch, mock_open
import json
import tempfile
from pathlib import Path
from datetime import datetime, date, timedelta

from tick_tock_widget.project_data import (
    ProjectDataManager, Project, SubActivity, TimeRecord
)
from tick_tock_widget.config import Environment


class TestTimeRecord:
    """Test TimeRecord class"""
    
    def test_time_record_creation(self):
        """Test TimeRecord creation with default values"""
        record = TimeRecord(date="2025-08-13")
        
        assert record.date == "2025-08-13"
        assert record.total_seconds == 0
        assert record.last_started is None
        assert record.is_running is False
        assert record.sub_activity_seconds == {}
    
    def test_time_record_creation_with_values(self):
        """Test TimeRecord creation with provided values"""
        sub_activities = {"coding": 1800, "testing": 900}
        record = TimeRecord(
            date="2025-08-13",
            total_seconds=3600,
            last_started="2025-08-13T10:00:00",
            is_running=True,
            sub_activity_seconds=sub_activities
        )
        
        assert record.date == "2025-08-13"
        assert record.total_seconds == 3600
        assert record.last_started == "2025-08-13T10:00:00"
        assert record.is_running is True
        assert record.sub_activity_seconds == sub_activities
    
    def test_add_time(self):
        """Test adding time to a record"""
        record = TimeRecord(date="2025-08-13", total_seconds=1800)
        record.add_time(900)
        
        assert record.total_seconds == 2700
    
    def test_get_formatted_time(self):
        """Test formatted time display"""
        record = TimeRecord(date="2025-08-13", total_seconds=3661)  # 1h 1m 1s
        
        assert record.get_formatted_time() == "01:01:01"
    
    def test_get_formatted_time_zero(self):
        """Test formatted time with zero seconds"""
        record = TimeRecord(date="2025-08-13", total_seconds=0)
        
        assert record.get_formatted_time() == "00:00:00"
    
    @patch('tick_tock_widget.project_data.datetime')
    def test_get_current_total_seconds_running(self, mock_datetime):
        """Test current total seconds when timer is running"""
        # Setup mock time
        start_time = datetime(2025, 8, 13, 10, 0, 0)
        current_time = datetime(2025, 8, 13, 10, 5, 30)  # 5.5 minutes later
        
        mock_datetime.now.return_value = current_time
        mock_datetime.fromisoformat.return_value = start_time
        
        record = TimeRecord(
            date="2025-08-13",
            total_seconds=1800,
            last_started=start_time.isoformat(),
            is_running=True
        )
        
        # Should include base time (1800) + elapsed time (330 seconds)
        total = record.get_current_total_seconds()
        assert total == 1800 + 330  # 2130 seconds
    
    def test_get_current_total_seconds_not_running(self):
        """Test current total seconds when timer is not running"""
        record = TimeRecord(date="2025-08-13", total_seconds=1800, is_running=False)
        
        assert record.get_current_total_seconds() == 1800
    
    @patch('tick_tock_widget.project_data.datetime')
    def test_start_timing(self, mock_datetime):
        """Test starting the timer"""
        mock_time = datetime(2025, 8, 13, 10, 0, 0)
        mock_datetime.now.return_value = mock_time
        
        record = TimeRecord(date="2025-08-13")
        record.start_timing()
        
        assert record.is_running is True
        assert record.last_started == mock_time.isoformat()
    
    @patch('tick_tock_widget.project_data.datetime')
    def test_stop_timing(self, mock_datetime):
        """Test stopping the timer"""
        start_time = datetime(2025, 8, 13, 10, 0, 0)
        end_time = datetime(2025, 8, 13, 10, 5, 0)  # 5 minutes later
        
        mock_datetime.fromisoformat.return_value = start_time
        mock_datetime.now.return_value = end_time
        
        record = TimeRecord(
            date="2025-08-13",
            total_seconds=1800,
            last_started=start_time.isoformat(),
            is_running=True
        )
        
        record.stop_timing()
        
        assert record.is_running is False
        assert record.last_started is None
        assert record.total_seconds == 1800 + 300  # Added 5 minutes (300 seconds)


class TestSubActivity:
    """Test SubActivity class"""
    
    def test_sub_activity_creation(self):
        """Test SubActivity creation"""
        sub_activity = SubActivity(
            name="Coding",
            alias="CODE",
            time_records={}
        )
        
        assert sub_activity.name == "Coding"
        assert sub_activity.alias == "CODE"
        assert sub_activity.time_records == {}
    
    def test_sub_activity_post_init_dict_conversion(self):
        """Test __post_init__ converts dict to TimeRecord objects"""
        time_records_dict = {
            "2025-08-13": {
                "date": "2025-08-13",
                "total_seconds": 1800,
                "last_started": None,
                "is_running": False,
                "sub_activity_seconds": {}
            }
        }
        
        sub_activity = SubActivity(
            name="Testing",
            alias="TEST",
            time_records=time_records_dict
        )
        
        assert isinstance(sub_activity.time_records["2025-08-13"], TimeRecord)
        assert sub_activity.time_records["2025-08-13"].total_seconds == 1800
    
    @patch('tick_tock_widget.project_data.date')
    def test_get_today_record_existing(self, mock_date):
        """Test getting today's record when it exists"""
        mock_date.today.return_value = date(2025, 8, 13)
        
        existing_record = TimeRecord(date="2025-08-13", total_seconds=1800)
        sub_activity = SubActivity(
            name="Coding",
            alias="CODE",
            time_records={"2025-08-13": existing_record}
        )
        
        record = sub_activity.get_today_record()
        assert record is existing_record
        assert record.total_seconds == 1800
    
    @patch('tick_tock_widget.project_data.date')
    def test_get_today_record_new(self, mock_date):
        """Test getting today's record when it doesn't exist"""
        mock_date.today.return_value = date(2025, 8, 13)
        
        sub_activity = SubActivity(
            name="Coding",
            alias="CODE",
            time_records={}
        )
        
        record = sub_activity.get_today_record()
        assert isinstance(record, TimeRecord)
        assert record.date == "2025-08-13"
        assert record.total_seconds == 0
        assert "2025-08-13" in sub_activity.time_records
    
    def test_get_total_time_today(self):
        """Test getting formatted total time for today"""
        with patch.object(SubActivity, 'get_today_record') as mock_get_record:
            mock_record = Mock()
            mock_record.get_formatted_time.return_value = "01:30:00"
            mock_get_record.return_value = mock_record
            
            sub_activity = SubActivity(name="Coding", alias="CODE", time_records={})
            result = sub_activity.get_total_time_today()
            
            assert result == "01:30:00"
            mock_get_record.assert_called_once()
            mock_record.get_formatted_time.assert_called_once()
    
    def test_is_running_today(self):
        """Test checking if sub-activity is running today"""
        with patch.object(SubActivity, 'get_today_record') as mock_get_record:
            mock_record = Mock()
            mock_record.is_running = True
            mock_get_record.return_value = mock_record
            
            sub_activity = SubActivity(name="Coding", alias="CODE", time_records={})
            result = sub_activity.is_running_today()
            
            assert result is True
            mock_get_record.assert_called_once()


class TestProject:
    """Test Project class"""
    
    def test_project_creation(self):
        """Test Project creation"""
        project = Project(
            name="Test Project",
            dz_number="DZ123",
            alias="TP",
            sub_activities=[],
            time_records={}
        )
        
        assert project.name == "Test Project"
        assert project.dz_number == "DZ123"
        assert project.alias == "TP"
        assert project.sub_activities == []
        assert project.time_records == {}
    
    def test_project_post_init_conversion(self):
        """Test __post_init__ converts dicts to proper objects"""
        time_records_dict = {
            "2025-08-13": {
                "date": "2025-08-13",
                "total_seconds": 3600,
                "last_started": None,
                "is_running": False,
                "sub_activity_seconds": {}
            }
        }
        
        sub_activities_list = [
            {
                "name": "Coding",
                "alias": "CODE",
                "time_records": {}
            }
        ]
        
        project = Project(
            name="Test Project",
            dz_number="DZ123",
            alias="TP",
            sub_activities=sub_activities_list,
            time_records=time_records_dict
        )
        
        assert isinstance(project.time_records["2025-08-13"], TimeRecord)
        assert isinstance(project.sub_activities[0], SubActivity)
        assert project.time_records["2025-08-13"].total_seconds == 3600
        assert project.sub_activities[0].name == "Coding"
    
    @patch('tick_tock_widget.project_data.date')
    def test_get_today_record(self, mock_date):
        """Test getting today's record for project"""
        mock_date.today.return_value = date(2025, 8, 13)
        
        project = Project(
            name="Test",
            dz_number="DZ123",
            alias="T", 
            sub_activities=[],
            time_records={}
        )
        record = project.get_today_record()
        
        assert isinstance(record, TimeRecord)
        assert record.date == "2025-08-13"
        assert "2025-08-13" in project.time_records
    
    def test_add_sub_activity(self):
        """Test adding a sub-activity to project"""
        project = Project(
            name="Test",
            dz_number="DZ123",
            alias="T",
            sub_activities=[],
            time_records={}
        )
        
        sub_activity = project.add_sub_activity("Coding", "CODE")
        
        assert isinstance(sub_activity, SubActivity)
        assert sub_activity.name == "Coding"
        assert sub_activity.alias == "CODE"
        assert len(project.sub_activities) == 1
        assert project.sub_activities[0] is sub_activity
    
    def test_remove_sub_activity(self):
        """Test removing a sub-activity from project"""
        project = Project(
            name="Test",
            dz_number="DZ123",
            alias="T",
            sub_activities=[],
            time_records={}
        )
        
        project.add_sub_activity("Coding", "CODE")
        project.add_sub_activity("Testing", "TEST")
        
        result = project.remove_sub_activity("CODE")
        
        assert result is True
        assert len(project.sub_activities) == 1
        assert project.sub_activities[0].alias == "TEST"
    
    def test_remove_sub_activity_not_found(self):
        """Test removing non-existent sub-activity"""
        project = Project(
            name="Test",
            dz_number="DZ123",
            alias="T",
            sub_activities=[],
            time_records={}
        )
        
        result = project.remove_sub_activity("NONEXISTENT")
        
        assert result is False
    
    def test_get_sub_activity(self):
        """Test getting sub-activity by alias"""
        project = Project(
            name="Test",
            dz_number="DZ123",
            alias="T",
            sub_activities=[],
            time_records={}
        )
        
        coding_sub = project.add_sub_activity("Coding", "CODE")
        
        result = project.get_sub_activity("CODE")
        assert result is coding_sub
        
        result = project.get_sub_activity("NONEXISTENT")
        assert result is None


class TestProjectDataManager:
    """Test ProjectDataManager class"""
    
    @patch('tick_tock_widget.project_data.get_config')
    def test_init_default(self, mock_get_config):
        """Test ProjectDataManager initialization with defaults"""
        mock_config = Mock()
        mock_config.get_data_file.return_value = "test_data.json"
        mock_config.get_auto_save_interval.return_value = 300
        mock_get_config.return_value = mock_config
        
        with patch.object(ProjectDataManager, 'load_projects', return_value=True):
            manager = ProjectDataManager()
            
            assert manager.data_file == Path("test_data.json")
            assert manager.projects == []
            assert manager.current_project_alias is None
            assert manager.current_sub_activity_alias is None
            mock_config.get_data_file.assert_called_once()
    
    @patch('tick_tock_widget.project_data.get_config')
    def test_init_custom_file(self, mock_get_config):
        """Test ProjectDataManager initialization with custom file"""
        mock_config = Mock()
        mock_config.get_auto_save_interval.return_value = 300
        mock_get_config.return_value = mock_config
        
        with patch.object(ProjectDataManager, 'load_projects', return_value=True):
            manager = ProjectDataManager(data_file="custom.json")
            
            assert manager.data_file == Path("custom.json")
            # Should not call config.get_data_file when custom file provided
            mock_config.get_data_file.assert_not_called()
    
    def test_load_projects_valid_file(self, temp_config_dir):
        """Test loading projects from valid file"""
        data_file = temp_config_dir / "test_data.json"
        
        # Create test data matching the actual format  
        test_data = {
            "projects": [
                {
                    "name": "Test Project 1",
                    "dz_number": "DZ123",
                    "alias": "TP1",
                    "sub_activities": [],
                    "time_records": {}
                },
                {
                    "name": "Test Project 2", 
                    "dz_number": "DZ456",
                    "alias": "TP2",
                    "sub_activities": [],
                    "time_records": {}
                }
            ],
            "current_project_alias": "TP1",
            "current_sub_activity_alias": None,
            "last_saved": "2025-08-13T10:30:00",
            "environment": "test"
        }
        
        with open(data_file, 'w') as f:
            json.dump(test_data, f)
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 300
            mock_get_config.return_value = mock_config
            
            manager = ProjectDataManager(data_file=str(data_file))
            manager.load_projects()
            
            assert len(manager.projects) == 2
            assert manager.projects[0].name == "Test Project 1"
            assert manager.projects[0].alias == "TP1"
            assert manager.projects[1].name == "Test Project 2" 
            assert manager.projects[1].alias == "TP2"
            assert manager.current_project_alias == "TP1"
    
    @patch('tick_tock_widget.project_data.get_config')
    def test_load_projects_corrupted_file(self, mock_get_config, temp_config_dir):
        """Test loading data from corrupted file"""
        mock_config = Mock()
        mock_config.get_auto_save_interval.return_value = 300
        mock_get_config.return_value = mock_config
        
        data_file = temp_config_dir / "corrupted.json"
        with open(data_file, 'w') as f:
            f.write("invalid json content")
        
        manager = ProjectDataManager(data_file=str(data_file))
        
        # Should have empty project list when file is corrupted
        assert manager.projects == []
    
    def test_save_projects(self, temp_config_dir):
        """Test saving projects to file"""
        data_file = temp_config_dir / "save_test.json"
        
        with patch('tick_tock_widget.project_data.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_auto_save_interval.return_value = 300
            mock_config.is_backup_enabled.return_value = False  # Disable backup for test
            mock_config.get_environment.return_value = Environment.TEST
            mock_get_config.return_value = mock_config
            
            manager = ProjectDataManager(data_file=str(data_file))
            
            # Add a test project  
            project = Project(
                name="Test",
                dz_number="DZ123",
                alias="T",
                sub_activities=[],
                time_records={}
            )
            manager.projects.append(project)
            
            result = manager.save_projects(force=True)
            
            assert result is True
            assert data_file.exists()
            
            # Verify saved content
            with open(data_file, 'r') as f:
                data = json.load(f)
                assert "projects" in data
                assert len(data["projects"]) == 1
                assert data["projects"][0]["name"] == "Test"
                assert data["projects"][0]["alias"] == "T"
    
    def test_add_project(self):
        """Test adding a new project"""
        with patch('tick_tock_widget.project_data.get_config'):
            with patch.object(ProjectDataManager, 'load_projects', return_value=True):
                manager = ProjectDataManager()
                
                project = manager.add_project("Test Project", "DZ123", "TP")
                
                assert project is not None
                assert len(manager.projects) == 1
                assert manager.projects[0] is project
                assert project.name == "Test Project"
                assert project.dz_number == "DZ123"
                assert project.alias == "TP"
    
    def test_add_project_duplicate_alias(self):
        """Test adding project with duplicate alias"""
        with patch('tick_tock_widget.project_data.get_config'):
            with patch.object(ProjectDataManager, 'load_projects', return_value=True):
                manager = ProjectDataManager()
                
                # Add first project
                manager.add_project("Project 1", "DZ123", "TEST")
                
                # Try to add second project with same alias
                result = manager.add_project("Project 2", "DZ456", "TEST")
                
                assert result is None
                assert len(manager.projects) == 1
    
    def test_remove_project(self):
        """Test removing a project"""
        with patch('tick_tock_widget.project_data.get_config'):
            with patch.object(ProjectDataManager, 'load_projects', return_value=True):
                manager = ProjectDataManager()
                
                # Add a project
                project = manager.add_project("Test", "DZ123", "T")
                assert len(manager.projects) == 1
                
                # Remove the project
                result = manager.remove_project("T")
                
                assert result is True
                assert len(manager.projects) == 0
    
    def test_remove_project_not_found(self):
        """Test removing non-existent project"""
        with patch('tick_tock_widget.project_data.get_config'):
            with patch.object(ProjectDataManager, 'load_projects', return_value=True):
                manager = ProjectDataManager()
                
                result = manager.remove_project("nonexistent")
                
                assert result is False
    
    def test_get_project(self):
        """Test getting project by alias"""
        with patch('tick_tock_widget.project_data.get_config'):
            with patch.object(ProjectDataManager, 'load_projects', return_value=True):
                manager = ProjectDataManager()
                
                project = manager.add_project("Test", "DZ123", "T")
                
                result = manager.get_project("T")
                assert result is project
                
                result = manager.get_project("NONEXISTENT")
                assert result is None
    
    def test_set_current_project(self):
        """Test setting current project"""
        with patch('tick_tock_widget.project_data.get_config'):
            with patch.object(ProjectDataManager, 'load_projects', return_value=True):
                manager = ProjectDataManager()
                
                project = manager.add_project("Test", "DZ123", "T")
                
                result = manager.set_current_project("T")
                assert result is True
                assert manager.current_project_alias == "T"
                assert manager.current_sub_activity_alias is None  # Should reset
                
                result = manager.set_current_project("NONEXISTENT")
                assert result is False
    
    def test_get_current_project(self):
        """Test getting current project"""
        with patch('tick_tock_widget.project_data.get_config'):
            with patch.object(ProjectDataManager, 'load_projects', return_value=True):
                manager = ProjectDataManager()
                
                project = manager.add_project("Test", "DZ123", "T")
                manager.set_current_project("T")
                
                result = manager.get_current_project()
                assert result is project
                
                manager.current_project_alias = None
                result = manager.get_current_project()
                assert result is None
    
    def test_start_stop_timers(self):
        """Test starting and stopping timers"""
        with patch('tick_tock_widget.project_data.get_config'), \
             patch('tick_tock_widget.project_data.date') as mock_date:
            
            mock_date.today.return_value = date(2025, 8, 13)
            
            with patch.object(ProjectDataManager, 'load_projects', return_value=True):
                manager = ProjectDataManager()
                
                # Add project and set as current
                project = manager.add_project("Test", "DZ123", "T")
                manager.set_current_project("T")
                
                # Start timer
                result = manager.start_current_timer()
                assert result is True
                
                # Check that project timer is running
                today_record = project.get_today_record()
                assert today_record.is_running is True
                
                # Stop all timers
                manager.stop_all_timers()
                assert today_record.is_running is False
