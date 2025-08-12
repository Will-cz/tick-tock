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
