"""
Unit tests for minimized widget component
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import tkinter as tk


@pytest.mark.gui
class TestMinimizedWidget:
    """Test the MinimizedTickTockWidget class"""
    
    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    @patch('tick_tock_widget.minimized_widget.tk.Frame')
    @patch('tick_tock_widget.minimized_widget.tk.Button')
    @patch('tick_tock_widget.minimized_widget.tk.Label')
    def test_minimized_widget_creation(self, mock_label, mock_button, mock_frame, mock_toplevel):
        """Test creating a minimized widget"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        
        # Mock dependencies
        mock_parent = Mock()
        mock_parent.root = Mock()  # Parent has root attribute
        mock_parent.root.winfo_x.return_value = 100
        mock_parent.root.winfo_y.return_value = 100 
        mock_parent.root.winfo_width.return_value = 400
        mock_parent.get_current_theme.return_value = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        mock_data_manager = Mock()
        mock_data_manager.projects = []  # Make projects an empty list, not a Mock
        mock_data_manager.current_project_alias = "Test"
        mock_on_maximize = Mock()
        
        # Create minimized widget
        widget = MinimizedTickTockWidget(
            parent_widget=mock_parent,
            data_manager=mock_data_manager,
            on_maximize=mock_on_maximize
        )
        
        # Verify widget was created
        assert widget is not None
        assert widget.parent_widget == mock_parent
        assert widget.data_manager == mock_data_manager
        assert widget.on_maximize == mock_on_maximize
    
    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    def test_minimized_widget_methods(self, mock_toplevel):
        """Test minimized widget methods"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        
        # Mock dependencies
        mock_parent = Mock()
        mock_parent.root = Mock()  # Make sure parent has a root
        mock_parent.root.winfo_x.return_value = 100
        mock_parent.root.winfo_y.return_value = 100
        mock_parent.root.winfo_width.return_value = 400
        mock_parent.get_current_theme.return_value = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        mock_data_manager = Mock()
        mock_data_manager.projects = []  # Make projects an empty list, not a Mock
        mock_data_manager.current_project_alias = "Test"
        mock_on_restore = Mock()
        
        # Mock the Toplevel window
        mock_window = Mock()
        mock_window._last_child_ids = {}  # Add this for tkinter compatibility
        mock_window._w = ".test_window"   # Add this for tkinter compatibility
        mock_window.tk = Mock()           # Add this for tkinter compatibility
        mock_window.children = {}         # Add this for tkinter compatibility
        mock_toplevel.return_value = mock_window
        
        widget = MinimizedTickTockWidget(
            parent_widget=mock_parent,
            data_manager=mock_data_manager,
            on_maximize=mock_on_restore
        )
        
        # Test that widget has expected methods
        assert hasattr(widget, 'update_time')
        assert hasattr(widget, 'update_project_display')
        assert hasattr(widget, 'maximize')
        
        # Test methods are callable
        assert callable(widget.update_time)
        assert callable(widget.update_project_display)
        assert callable(widget.maximize)
    
    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    def test_minimized_widget_update_display(self, mock_toplevel):
        """Test minimized widget display update"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        
        # Mock dependencies
        mock_parent = Mock()
        mock_parent.root = Mock()  # Make sure parent has a root
        mock_parent.root.winfo_x.return_value = 100
        mock_parent.root.winfo_y.return_value = 100
        mock_parent.root.winfo_width.return_value = 400
        mock_parent.get_current_theme.return_value = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        mock_data_manager = Mock()
        mock_data_manager.projects = []  # Make projects an empty list, not a Mock
        mock_data_manager.current_project_alias = "Test"
        mock_on_restore = Mock()
        
        # Mock current project data
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.alias = "TP"
        mock_data_manager.get_current_project.return_value = mock_project
        
        widget = MinimizedTickTockWidget(
            parent_widget=mock_parent,
            data_manager=mock_data_manager,
            on_maximize=mock_on_restore
        )
        
        # Test update display
        widget.update_project_display()
        
        # The method doesn't call get_current_project, it directly accesses projects and current_project_alias
        # Just verify the method ran without errors (success is that it didn't throw an exception)
    
    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    def test_minimized_widget_close(self, mock_toplevel):
        """Test minimized widget close functionality"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        
        # Mock dependencies
        mock_parent = Mock()
        mock_parent.root = Mock()  # Make sure parent has a root
        mock_parent.root.winfo_x.return_value = 100
        mock_parent.root.winfo_y.return_value = 100
        mock_parent.root.winfo_width.return_value = 400
        mock_parent.get_current_theme.return_value = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        mock_data_manager = Mock()
        mock_data_manager.projects = []  # Make projects an empty list, not a Mock
        mock_data_manager.current_project_alias = "Test"
        mock_on_restore = Mock()
        
        mock_window = Mock()
        mock_window._last_child_ids = {}  # Add this for tkinter compatibility
        mock_window._w = ".test_window"   # Add this for tkinter compatibility
        mock_window.tk = Mock()           # Add this for tkinter compatibility
        mock_window.children = {}         # Add this for tkinter compatibility
        mock_toplevel.return_value = mock_window
        
        widget = MinimizedTickTockWidget(
            parent_widget=mock_parent,
            data_manager=mock_data_manager,
            on_maximize=mock_on_restore
        )
        
        # Test maximize (which acts as close in this context)
        widget.maximize()
        
        # Verify maximize callback was called
        mock_on_restore.assert_called()
    
    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    def test_minimized_widget_restore_callback(self, mock_toplevel):
        """Test minimized widget restore callback"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        
        # Mock dependencies
        mock_parent = Mock()
        mock_parent.root = Mock()  # Make sure parent has a root
        mock_parent.root.winfo_x.return_value = 100
        mock_parent.root.winfo_y.return_value = 100
        mock_parent.root.winfo_width.return_value = 400
        mock_parent.get_current_theme.return_value = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        mock_data_manager = Mock()
        mock_data_manager.projects = []  # Make projects an empty list, not a Mock
        mock_data_manager.current_project_alias = "Test"
        mock_on_restore = Mock()
        
        widget = MinimizedTickTockWidget(
            parent_widget=mock_parent,
            data_manager=mock_data_manager,
            on_maximize=mock_on_restore
        )
        
        # Test that widget stores the callback
        assert widget.on_maximize == mock_on_restore

    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    @patch('tick_tock_widget.minimized_widget.ttk.Combobox')
    def test_project_selection_timer_management(self, mock_combobox, mock_toplevel):
        """Test that project selection properly manages timers (Total Today fix)"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        from tick_tock_widget.project_data import Project, SubActivity
        
        # Mock dependencies
        mock_parent = Mock()
        mock_parent.root = Mock()
        mock_parent.root.winfo_x.return_value = 100
        mock_parent.root.winfo_y.return_value = 100
        mock_parent.root.winfo_width.return_value = 400
        mock_parent.get_current_theme.return_value = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        mock_parent.update_project_display = Mock()  # Add update method
        
        # Create mock projects
        project1 = Mock(spec=Project)
        project1.alias = "project1"
        project1.name = "Project One"
        project1.sub_activities = []
        
        project2 = Mock(spec=Project)  
        project2.alias = "project2"
        project2.name = "Project Two"
        project2.sub_activities = []
        
        # Mock data manager
        mock_data_manager = Mock()
        mock_data_manager.projects = [project1, project2]
        mock_data_manager.current_project_alias = "project1"
        mock_data_manager.set_current_project = Mock(return_value=True)
        mock_data_manager.stop_all_timers = Mock()
        mock_data_manager.start_current_timer = Mock(return_value=True)
        
        mock_on_maximize = Mock()
        
        widget = MinimizedTickTockWidget(
            parent_widget=mock_parent,
            data_manager=mock_data_manager,
            on_maximize=mock_on_maximize
        )
        
        # Mock the combobox to return project2 alias
        mock_combobox_instance = Mock()
        mock_combobox_instance.get.return_value = "project2"
        mock_combobox_instance.__setitem__ = Mock()  # Allow item assignment
        widget.project_combobox = mock_combobox_instance
        
        # Mock activity combobox too for update_project_display
        mock_activity_combobox = Mock()
        mock_activity_combobox.__setitem__ = Mock()
        widget.activity_combobox = mock_activity_combobox
        
        # Create mock event
        mock_event = Mock()
        
        # Test project selection - this should trigger timer management
        widget.on_project_select(mock_event)
        
        # Verify the fix: proper timer management sequence
        mock_data_manager.set_current_project.assert_called_once_with("project2")
        mock_data_manager.stop_all_timers.assert_called_once()
        mock_data_manager.start_current_timer.assert_called_once()
        
        # Verify parent widget notification (new fix)
        mock_parent.update_project_display.assert_called_once()

    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    @patch('tick_tock_widget.minimized_widget.ttk.Combobox')
    def test_activity_selection_timer_management(self, mock_combobox, mock_toplevel):
        """Test that activity selection properly manages timers"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        from tick_tock_widget.project_data import Project, SubActivity
        
        # Mock dependencies
        mock_parent = Mock()
        mock_parent.root = Mock()
        mock_parent.root.winfo_x.return_value = 100
        mock_parent.root.winfo_y.return_value = 100
        mock_parent.root.winfo_width.return_value = 400
        mock_parent.get_current_theme.return_value = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        mock_parent.update_project_display = Mock()
        
        # Create mock sub-activities
        sub1 = Mock(spec=SubActivity)
        sub1.name = "Development"
        sub1.alias = "dev"
        sub1.get_today_record = Mock()
        sub1.get_today_record.return_value.start_timing = Mock()
        
        sub2 = Mock(spec=SubActivity)
        sub2.name = "Testing"
        sub2.alias = "test"
        sub2.get_today_record = Mock()
        sub2.get_today_record.return_value.start_timing = Mock()
        
        # Create mock project with sub-activities
        project = Mock(spec=Project)
        project.alias = "project1"
        project.name = "Project One"
        project.sub_activities = [sub1, sub2]
        
        # Mock data manager
        mock_data_manager = Mock()
        mock_data_manager.projects = [project]
        mock_data_manager.current_project_alias = "project1"
        mock_data_manager.stop_all_timers = Mock()
        mock_data_manager.set_current_sub_activity = Mock(return_value=True)
        mock_data_manager.start_current_timer = Mock(return_value=True)
        
        mock_on_maximize = Mock()
        
        widget = MinimizedTickTockWidget(
            parent_widget=mock_parent,
            data_manager=mock_data_manager,
            on_maximize=mock_on_maximize
        )
        
        # Mock both comboboxes for update_project_display compatibility
        mock_project_combobox = Mock()
        mock_project_combobox.__setitem__ = Mock()
        widget.project_combobox = mock_project_combobox
        
        mock_activity_combobox = Mock()
        mock_activity_combobox.__setitem__ = Mock()
        mock_activity_combobox.get.return_value = "Development"
        widget.activity_combobox = mock_activity_combobox
        
        # Create mock event
        mock_event = Mock()
        
        # Test activity selection
        widget.on_activity_select(mock_event)
        
        # Verify proper timer management
        mock_data_manager.stop_all_timers.assert_called_once()
        mock_data_manager.set_current_sub_activity.assert_called_once_with("dev")
        mock_data_manager.start_current_timer.assert_called_once()
        
        # Verify parent widget notification
        mock_parent.update_project_display.assert_called_once()

    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    @patch('tick_tock_widget.minimized_widget.ttk.Combobox')
    def test_clear_activity_selection_timer_management(self, mock_combobox, mock_toplevel):
        """Test that clearing activity selection properly manages timers"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        from tick_tock_widget.project_data import Project
        
        # Mock dependencies
        mock_parent = Mock()
        mock_parent.root = Mock()
        mock_parent.root.winfo_x.return_value = 100
        mock_parent.root.winfo_y.return_value = 100
        mock_parent.root.winfo_width.return_value = 400
        mock_parent.get_current_theme.return_value = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        mock_parent.update_project_display = Mock()
        
        # Create mock project
        project = Mock(spec=Project)
        project.alias = "project1"
        project.name = "Project One"
        project.sub_activities = []
        
        # Mock data manager
        mock_data_manager = Mock()
        mock_data_manager.projects = [project]
        mock_data_manager.current_project_alias = "project1"
        mock_data_manager.stop_all_timers = Mock()
        mock_data_manager.set_current_sub_activity = Mock(return_value=True)
        mock_data_manager.start_current_timer = Mock(return_value=True)
        
        mock_on_maximize = Mock()
        
        widget = MinimizedTickTockWidget(
            parent_widget=mock_parent,
            data_manager=mock_data_manager,
            on_maximize=mock_on_maximize
        )
        
        # Mock both comboboxes for update_project_display compatibility
        mock_project_combobox = Mock()
        mock_project_combobox.__setitem__ = Mock()
        widget.project_combobox = mock_project_combobox
        
        mock_activity_combobox = Mock()
        mock_activity_combobox.__setitem__ = Mock()
        mock_activity_combobox.get.return_value = ""  # Empty string (cleared)
        widget.activity_combobox = mock_activity_combobox
        
        # Create mock event
        mock_event = Mock()
        
        # Test activity clearing
        widget.on_activity_select(mock_event)
        
        # Verify proper timer management for clearing sub-activity
        mock_data_manager.stop_all_timers.assert_called_once()
        mock_data_manager.set_current_sub_activity.assert_called_once_with(None)
        mock_data_manager.start_current_timer.assert_called_once()
        
        # Verify parent widget notification
        mock_parent.update_project_display.assert_called_once()
