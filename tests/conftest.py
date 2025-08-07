"""
Test fixtures and shared utilities for Tick-Tock Widget tests
"""
import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from pathlib import Path
from datetime import datetime, date
import sys
import os

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tick_tock_widget.project_data import ProjectDataManager, Project, SubActivity, TimeRecord
from tick_tock_widget.config import Config, Environment
from tick_tock_widget.theme_colors import ThemeColors


class MockTkRoot:
    """Mock Tk root for testing without creating actual windows"""
    
    def __init__(self):
        self.geometry_value = "400x300+100+100"
        self.title_value = "Test Window"
        self.attributes_calls = []
        self.protocol_handlers = {}
        self.destroyed = False
        self.x = 100
        self.y = 100
        self.width = 400
        self.height = 300
        
    def geometry(self, geom=None):
        if geom:
            self.geometry_value = geom
        return self.geometry_value
        
    def title(self, title=None):
        if title:
            self.title_value = title
        return self.title_value
        
    def configure(self, **kwargs):
        pass
        
    def attributes(self, *args, **kwargs):
        self.attributes_calls.append((args, kwargs))
        
    def protocol(self, protocol, handler):
        self.protocol_handlers[protocol] = handler
        
    def overrideredirect(self, value):
        pass
        
    def winfo_x(self):
        return self.x
        
    def winfo_y(self):
        return self.y
        
    def winfo_width(self):
        return self.width
        
    def winfo_height(self):
        return self.height
        
    def winfo_exists(self):
        return not self.destroyed
        
    def destroy(self):
        self.destroyed = True
        
    def mainloop(self):
        pass
        
    def quit(self):
        pass
        
    def update(self):
        pass
        
    def after(self, ms, func):
        # For testing, just return a mock job ID
        return "mock_job_id"
        
    def after_cancel(self, job_id):
        pass


class MockWidget:
    """Mock widget for testing GUI components"""
    
    def __init__(self, master=None, **kwargs):
        self.master = master
        self.config_values = kwargs
        self.children = []
        self.pack_info_value = {}
        self.destroyed = False
        
    def configure(self, **kwargs):
        self.config_values.update(kwargs)
        
    def config(self, **kwargs):
        self.configure(**kwargs)
        
    def pack(self, **kwargs):
        self.pack_info_value = kwargs
        
    def pack_info(self):
        return self.pack_info_value
        
    def grid(self, **kwargs):
        pass
        
    def place(self, **kwargs):
        pass
        
    def bind(self, event, handler):
        pass
        
    def unbind(self, event):
        pass
        
    def winfo_children(self):
        return self.children
        
    def winfo_class(self):
        return "MockWidget"
        
    def winfo_exists(self):
        return not self.destroyed
        
    def destroy(self):
        self.destroyed = True
        for child in self.children:
            child.destroy()


@pytest.fixture
def mock_tk_root():
    """Fixture providing a mock Tk root"""
    return MockTkRoot()


@pytest.fixture
def temp_config_dir():
    """Fixture providing a temporary directory for config files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_data_file():
    """Fixture providing a temporary data file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        # Create minimal valid project data
        test_data = {
            "projects": {},
            "metadata": {
                "version": "1.0",
                "last_modified": datetime.now().isoformat()
            }
        }
        json.dump(test_data, f)
        temp_file = Path(f.name)
    
    yield temp_file
    
    # Cleanup
    if temp_file.exists():
        temp_file.unlink()


@pytest.fixture
def sample_project_data():
    """Fixture providing sample project data for testing"""
    return {
        "projects": {
            "test-project-1": {
                "name": "Test Project 1",
                "dz_number": "DZ-001",
                "alias": "TP1",
                "total_time": 3600,
                "time_records": {
                    "2025-08-13": {
                        "date": "2025-08-13",
                        "total_seconds": 1800,
                        "last_started": None,
                        "is_running": False,
                        "sub_activity_seconds": {}
                    }
                },
                "sub_activities": {
                    "coding": {
                        "name": "Coding",
                        "alias": "CODE",
                        "time_records": {
                            "2025-08-13": {
                                "date": "2025-08-13",
                                "total_seconds": 900,
                                "last_started": None,
                                "is_running": False,
                                "sub_activity_seconds": {}
                            }
                        }
                    },
                    "testing": {
                        "name": "Testing",
                        "alias": "TEST",
                        "time_records": {
                            "2025-08-13": {
                                "date": "2025-08-13",
                                "total_seconds": 900,
                                "last_started": None,
                                "is_running": False,
                                "sub_activity_seconds": {}
                            }
                        }
                    }
                }
            },
            "test-project-2": {
                "name": "Test Project 2",
                "dz_number": "DZ-002",
                "alias": "TP2",
                "total_time": 7200,
                "time_records": {
                    "2025-08-13": {
                        "date": "2025-08-13",
                        "total_seconds": 3600,
                        "last_started": None,
                        "is_running": False,
                        "sub_activity_seconds": {}
                    }
                },
                "sub_activities": {}
            }
        },
        "metadata": {
            "version": "1.0",
            "last_modified": "2025-08-13T10:30:00"
        }
    }


@pytest.fixture
def mock_data_manager(sample_project_data, temp_data_file):
    """Fixture providing a mock ProjectDataManager"""
    with patch('tick_tock_widget.project_data.ProjectDataManager') as mock_class:
        mock_instance = Mock(spec=ProjectDataManager)
        
        # Setup mock data
        projects = {}
        for proj_id, proj_data in sample_project_data["projects"].items():
            project = Project(
                name=proj_data["name"],
                dz_number=proj_data["dz_number"],
                alias=proj_data["alias"],
                time_records={},
                sub_activities=[]
            )
            projects[proj_id] = project
            
        mock_instance.projects = projects
        mock_instance.data_file = temp_data_file
        # Mock commonly used methods 
        mock_instance.get_project.return_value = None
        mock_instance.get_current_project.return_value = None
        mock_instance.save_projects.return_value = True
        mock_instance.load_projects.return_value = True
        
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def test_theme():
    """Fixture providing a test theme"""
    return ThemeColors(
        name='Test',
        bg='#000000',
        fg='#FFFFFF',
        accent='#808080',
        button_bg='#404040',
        button_fg='#FFFFFF',
        button_active='#606060'
    )


@pytest.fixture
def mock_config(temp_config_dir):
    """Fixture providing a mock Config instance"""
    with patch('tick_tock_widget.config.Config') as mock_class:
        mock_instance = Mock(spec=Config)
        mock_instance.config_file = temp_config_dir / "config.json"
        mock_instance.user_data_root = temp_config_dir
        mock_instance.get_environment.return_value = Environment.TEST
        mock_instance.get_data_file.return_value = str(temp_config_dir / "test_data.json")
        mock_instance.get_window_title.return_value = "Test Window"
        mock_instance.get_title_color.return_value = "#FFFFFF"
        mock_instance.get_border_color.return_value = "#808080"
        mock_instance.is_debug_mode.return_value = False
        mock_instance.get_tree_state.return_value = {}
        mock_instance.set_tree_state.return_value = None
        mock_instance.save_config.return_value = None
        
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def patch_tkinter():
    """Fixture to patch tkinter modules to prevent actual GUI creation"""
    with patch('tkinter.Tk') as mock_tk, \
         patch('tkinter.Toplevel') as mock_toplevel, \
         patch('tkinter.Frame') as mock_frame, \
         patch('tkinter.Label') as mock_label, \
         patch('tkinter.Button') as mock_button, \
         patch('tkinter.Entry') as mock_entry, \
         patch('tkinter.messagebox') as mock_messagebox, \
         patch('tkinter.ttk.Treeview') as mock_treeview, \
         patch('tkinter.ttk.Style') as mock_style:
        
        # Configure mocks to return MockWidget instances
        mock_tk.return_value = MockTkRoot()
        mock_toplevel.return_value = MockWidget()
        mock_frame.return_value = MockWidget()
        mock_label.return_value = MockWidget()
        mock_button.return_value = MockWidget()
        mock_entry.return_value = MockWidget()
        mock_treeview.return_value = MockWidget()
        mock_style.return_value = Mock()
        
        # Mock messagebox functions
        mock_messagebox.showinfo.return_value = None
        mock_messagebox.showwarning.return_value = None
        mock_messagebox.showerror.return_value = None
        mock_messagebox.askyesno.return_value = True
        mock_messagebox.askokcancel.return_value = True
        
        yield {
            'tk': mock_tk,
            'toplevel': mock_toplevel,
            'frame': mock_frame,
            'label': mock_label,
            'button': mock_button,
            'entry': mock_entry,
            'messagebox': mock_messagebox,
            'treeview': mock_treeview,
            'style': mock_style
        }


@pytest.fixture
def sample_time_record():
    """Fixture providing a sample TimeRecord"""
    return TimeRecord(
        date="2025-08-13",
        total_seconds=3600,
        last_started=None,
        is_running=False,
        sub_activity_seconds={"coding": 1800, "testing": 1800}
    )


@pytest.fixture
def sample_sub_activity():
    """Fixture providing a sample SubActivity"""
    time_records = {
        "2025-08-13": TimeRecord(
            date="2025-08-13",
            total_seconds=1800,
            last_started=None,
            is_running=False
        )
    }
    return SubActivity(
        name="Coding",
        alias="CODE",
        time_records=time_records
    )


@pytest.fixture
def sample_project(sample_time_record, sample_sub_activity):
    """Fixture providing a sample Project"""
    time_records = {"2025-08-13": sample_time_record}
    sub_activities = [sample_sub_activity]

    return Project(
        name="Test Project",
        dz_number="DZ-TEST",
        alias="TP",
        time_records=time_records,
        sub_activities=sub_activities
    )
@pytest.fixture
def freeze_time():
    """Fixture to freeze time for consistent testing"""
    test_time = datetime(2025, 8, 13, 10, 30, 0)
    with patch('tick_tock_widget.project_data.datetime') as mock_datetime, \
         patch('tick_tock_widget.project_data.date') as mock_date:
        
        mock_datetime.now.return_value = test_time
        mock_datetime.fromisoformat = datetime.fromisoformat
        mock_date.today.return_value = test_time.date()
        mock_date.fromisoformat = date.fromisoformat
        
        yield test_time
