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
        self._last_child_ids = {}
        self.tk = self  # Mock tk attribute
        
        # Make these Mock objects so tests can assert calls
        self.withdraw = Mock()
        self.deiconify = Mock()
        self.option_add = Mock()
        self.geometry = Mock(return_value="400x300+100+100")
        
    def winfo_x(self):
        return self.x
        
    def winfo_y(self):
        return self.y
        
    def winfo_width(self):
        return self.width
        
    def winfo_height(self):
        return self.height
        
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
        
    def winfo_screenwidth(self):
        return 1920
        
    def winfo_screenheight(self):
        return 1080
        
    def update_idletasks(self):
        pass
        
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
        self.children = {}  # Must be dict for tkinter compatibility
        self.pack_info_value = {}
        self.destroyed = False
        self._selection = []
        self.tk = self  # Add tk attribute for MockWidget
        self._last_child_ids = {}  # Add _last_child_ids for tkinter compatibility
        self._w = f".widget_{id(self)}"  # Mock widget identifier for tkinter compatibility
        
    def call(self, *args):
        """Mock tk.call method for tkinter compatibility"""
        return None
        
    def createcommand(self, name, func):
        """Mock tk.createcommand method for tkinter compatibility"""
        pass
        
    def configure(self, *args, **kwargs):
        # Handle both widget.configure(**kwargs) and style.configure(style_name, **kwargs)
        if args:
            # ttk.Style.configure(style_name, **kwargs) pattern
            pass
        else:
            # Normal widget configure(**kwargs) pattern
            self.config_values.update(kwargs)
        
    def config(self, **kwargs):
        self.configure(**kwargs)
        
    def pack(self, **kwargs):
        self.pack_info_value = kwargs
        
    def pack_info(self):
        return self.pack_info_value
    
    def pack_propagate(self, flag=None):
        if flag is None:
            return True
        return flag
        
    def grid(self, **kwargs):
        pass
        
    def place(self, **kwargs):
        pass
        
    def bind(self, event, handler):
        pass
        
    def unbind(self, event):
        pass
        
    def winfo_children(self):
        return list(self.children.values())  # Return list of child widgets
        
    def winfo_class(self):
        return "MockWidget"
        
    def winfo_exists(self):
        return not self.destroyed
    
    def winfo_screenwidth(self):
        return 1920
    
    def winfo_screenheight(self):
        return 1080
    
    def winfo_width(self):
        return 800
    
    def winfo_height(self):
        return 600
    
    def winfo_x(self):
        return 100
    
    def winfo_y(self):
        return 100
        
    def destroy(self):
        self.destroyed = True
        for child in self.children.values():  # Iterate over values (widgets) not keys
            if hasattr(child, 'destroy'):
                child.destroy()
            
    def selection(self):
        return self._selection
        
    def focus(self):
        return "item1" if self._selection else None
        
    def focus_set(self):
        pass
    
    # Dictionary-like access for tkinter widgets (e.g., tree['columns'])
    def __getitem__(self, key):
        return getattr(self, key, None)
    
    def __setitem__(self, key, value):
        setattr(self, key, value)
    
    # Additional treeview methods
    def column(self, column, **kw):
        pass
        
    def heading(self, column, **kw):
        pass
    
    def get_children(self, item=''):
        return list(self.children.keys())  # Return list of child names for treeview compatibility
        
    def insert(self, parent, index, **kw):
        item_id = f"item_{len(self.children)}"
        self.children[item_id] = Mock()  # Add to dict instead of list
        return item_id
        
    def delete(self, *items):
        for item in items:
            if item in self.children:
                del self.children[item]  # Remove from dict instead of list
        
    def item(self, item_id=None, **kwargs):
        return {'open': False, 'text': 'Mock Item'}
    
    # ttk.Style methods
    def theme_use(self, theme_name=None):
        pass
        
    def map(self, style_name, **kw):
        pass
    
    # Scrollable widget methods
    def yview(self, *args):
        pass
        
    def xview(self, *args):
        pass
        
    def yview_moveto(self, fraction):
        pass
        
    def xview_moveto(self, fraction):
        pass
        
    def yview_scroll(self, number, what):
        pass
        
    def xview_scroll(self, number, what):
        pass
    
    # Scrollbar methods / Treeview methods - different signatures
    def set(self, *args):
        # Handle both scrollbar.set(first, last) and tree.set(item, column, value)
        pass


class MockStringVar:
    """Mock StringVar class"""
    def __init__(self, master=None, value=None, name=None):
        self.value = value or ""
        
    def get(self):
        return self.value
        
    def set(self, value):
        self.value = value


class MockIntVar:
    """Mock IntVar class"""
    def __init__(self, master=None, value=None, name=None):
        self.value = value or 0
        
    def get(self):
        return self.value
        
    def set(self, value):
        self.value = value


class MockBooleanVar:
    """Mock BooleanVar class"""
    def __init__(self, master=None, value=None, name=None):
        self.value = value or False
        
    def get(self):
        return self.value
        
    def set(self, value):
        self.value = value


class MockDoubleVar:
    """Mock DoubleVar class"""
    def __init__(self, master=None, value=None, name=None):
        self.value = value or 0.0
        
    def get(self):
        return self.value
        
    def set(self, value):
        self.value = value


class MockToplevel(MockWidget):
    """Mock Toplevel window class for preventing GUI windows during tests"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self._title = "Mock Toplevel"
        self._geometry = "800x600"
        self._bg = "white"
        self._alpha = 1.0
        self._topmost = False
        self._overrideredirect = False
        
    def title(self, text=None):
        if text is not None:
            self._title = text
        return self._title
    
    def geometry(self, geom=None):
        if geom is not None:
            self._geometry = geom
        return self._geometry
    
    def configure(self, **kwargs):
        for key, value in kwargs.items():
            if key == 'bg':
                self._bg = value
            else:
                setattr(self, key, value)
    
    def attributes(self, attr, value=None):
        if attr == '-topmost':
            if value is not None:
                self._topmost = value
            return self._topmost
        elif attr == '-alpha':
            if value is not None:
                self._alpha = value
            return self._alpha
        return None
    
    def overrideredirect(self, boolean=None):
        if boolean is not None:
            self._overrideredirect = boolean
        return self._overrideredirect
    
    def protocol(self, name, func):
        pass
    
    def update_idletasks(self):
        pass
    
    def winfo_x(self):
        return 100
    
    def winfo_y(self):
        return 100
    
    def winfo_screenwidth(self):
        return 1920
    
    def winfo_screenheight(self):
        return 1080


@pytest.fixture
def mock_tk_root():
    """Fixture providing a mock Tk root"""
    return MockTkRoot()


@pytest.fixture
def mock_gui_components():
    """Fixture that mocks all GUI components to prevent windows during tests"""
    patches = [
        patch('tkinter.Tk', MockTkRoot),
        patch('tkinter.Toplevel', MockToplevel),
        patch('tick_tock_widget.monthly_report.tk.Toplevel', MockToplevel),
        patch('tick_tock_widget.minimized_widget.tk.Toplevel', MockToplevel),
        # Add project_management patches  
        patch('tick_tock_widget.project_management.tk.Toplevel', MockToplevel),
        patch('tick_tock_widget.project_management.tk.StringVar', MockStringVar),
        patch('tick_tock_widget.project_management.tk.IntVar', MockIntVar),
        patch('tick_tock_widget.project_management.tk.DoubleVar', MockDoubleVar),
        patch('tick_tock_widget.project_management.tk.BooleanVar', MockBooleanVar),
        patch('tkinter.StringVar', MockStringVar),
        patch('tkinter.IntVar', MockIntVar),
        patch('tkinter.DoubleVar', MockDoubleVar),
        patch('tkinter.BooleanVar', MockBooleanVar),
        # Also patch tk aliases for TickTockWidget
        patch('tick_tock_widget.tick_tock_widget.tk.DoubleVar', MockDoubleVar),
        patch('tick_tock_widget.tick_tock_widget.tk.StringVar', MockStringVar),
        patch('tick_tock_widget.tick_tock_widget.tk.IntVar', MockIntVar),
        patch('tick_tock_widget.tick_tock_widget.tk.BooleanVar', MockBooleanVar),
        patch('tkinter.Frame', MockWidget),
        patch('tkinter.Label', MockWidget),
        patch('tkinter.Button', MockWidget),
        patch('tkinter.Entry', MockWidget),
        patch('tkinter.Text', MockWidget),
        patch('tkinter.Listbox', MockWidget),
        patch('tkinter.Canvas', MockWidget),
        patch('tkinter.Scale', MockWidget),
        patch('tkinter.Scrollbar', MockWidget),
        patch('tkinter.Checkbutton', MockWidget),
        patch('tkinter.Radiobutton', MockWidget),
        patch('tkinter.Spinbox', MockWidget),
        patch('tkinter.Menubutton', MockWidget),
        patch('tkinter.Menu', MockWidget),
        patch('tkinter.OptionMenu', MockWidget),
        patch('tkinter.PanedWindow', MockWidget),
        patch('tkinter.LabelFrame', MockWidget),
        patch('tkinter.ttk.Treeview', MockWidget),
        patch('tkinter.ttk.Style', MockWidget),
        patch('tkinter.ttk.Combobox', MockWidget),
        patch('tkinter.ttk.Scrollbar', MockWidget),
        patch('tkinter.messagebox.showinfo', Mock()),
        patch('tkinter.messagebox.showwarning', Mock()),
        patch('tkinter.messagebox.showerror', Mock()),
        patch('tkinter.messagebox.askquestion', Mock(return_value='yes')),
        patch('tkinter.messagebox.askyesno', Mock(return_value=True)),
        patch('tkinter.messagebox.askokcancel', Mock(return_value=True)),
        patch('tkinter.messagebox.askretrycancel', Mock(return_value=True)),
        patch('tkinter.messagebox.askyesnocancel', Mock(return_value=True)),
        patch('tkinter.filedialog.askopenfilename', Mock(return_value='test_file.txt')),
        patch('tkinter.filedialog.asksaveasfilename', Mock(return_value='test_save.txt')),
        patch('tkinter.filedialog.askdirectory', Mock(return_value='/test/dir')),
    ]
    
    for p in patches:
        p.start()
    
    yield
    
    for p in patches:
        p.stop()


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
        mock_instance.get_auto_save_interval.return_value = 300  # Return actual integer
        mock_instance.is_backup_enabled.return_value = True
        mock_instance.get_backup_directory.return_value = temp_config_dir / "backups"
        mock_instance.get_max_backups.return_value = 10
        
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


@pytest.fixture
def mock_get_config():
    """Fixture providing a mock get_config function with proper return values"""
    with patch('tick_tock_widget.project_data.get_config') as mock_get_config_func:
        mock_config = Mock()
        mock_config.get_data_file.return_value = "test_data.json"
        mock_config.get_auto_save_interval.return_value = 300
        mock_config.is_backup_enabled.return_value = True
        mock_config.get_backup_directory.return_value = Path("backups")
        mock_config.get_max_backups.return_value = 10
        mock_config.get_environment.return_value = Environment.TEST
        mock_config.is_debug_mode.return_value = False
        mock_get_config_func.return_value = mock_config
        yield mock_get_config_func
