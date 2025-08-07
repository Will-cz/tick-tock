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
        mock_data_manager = Mock()
        mock_config = Mock()
        mock_on_restore = Mock()
        
        # Mock the Toplevel window
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        widget = MinimizedTickTockWidget(
            parent=mock_parent,
            data_manager=mock_data_manager,
            config=mock_config,
            on_restore_callback=mock_on_restore
        )
        
        # Test that widget has expected methods
        assert hasattr(widget, 'update_display')
        assert hasattr(widget, 'update_position')
        assert hasattr(widget, 'close')
        
        # Test methods are callable
        assert callable(widget.update_display)
        assert callable(widget.update_position)
        assert callable(widget.close)
    
    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    def test_minimized_widget_update_display(self, mock_toplevel):
        """Test minimized widget display update"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        
        # Mock dependencies
        mock_parent = Mock()
        mock_data_manager = Mock()
        mock_config = Mock()
        mock_on_restore = Mock()
        
        # Mock current project data
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.alias = "TP"
        mock_data_manager.get_current_project.return_value = mock_project
        
        widget = MinimizedTickTockWidget(
            parent=mock_parent,
            data_manager=mock_data_manager,
            config=mock_config,
            on_restore_callback=mock_on_restore
        )
        
        # Test update display
        widget.update_display()
        
        # Verify data manager was called
        mock_data_manager.get_current_project.assert_called()
    
    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    def test_minimized_widget_close(self, mock_toplevel):
        """Test minimized widget close functionality"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        
        # Mock dependencies
        mock_parent = Mock()
        mock_data_manager = Mock()
        mock_config = Mock()
        mock_on_restore = Mock()
        
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        widget = MinimizedTickTockWidget(
            parent=mock_parent,
            data_manager=mock_data_manager,
            config=mock_config,
            on_restore_callback=mock_on_restore
        )
        
        # Test close
        widget.close()
        
        # Verify window destroy was called
        mock_window.destroy.assert_called_once()
    
    @patch('tick_tock_widget.minimized_widget.tk.Toplevel')
    def test_minimized_widget_restore_callback(self, mock_toplevel):
        """Test minimized widget restore callback"""
        from tick_tock_widget.minimized_widget import MinimizedTickTockWidget
        
        # Mock dependencies
        mock_parent = Mock()
        mock_data_manager = Mock()
        mock_config = Mock()
        mock_on_restore = Mock()
        
        widget = MinimizedTickTockWidget(
            parent=mock_parent,
            data_manager=mock_data_manager,
            config=mock_config,
            on_restore_callback=mock_on_restore
        )
        
        # Test that widget stores the callback
        assert widget.on_restore_callback == mock_on_restore
