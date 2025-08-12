"""
Unit tests for project management window components
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import tkinter as tk


@pytest.mark.gui
class TestProjectManagementWindow:
    """Test the ProjectManagementWindow class"""
    
    @patch('tick_tock_widget.project_management.tk.Toplevel')
    @patch('tick_tock_widget.project_management.ttk.Treeview')
    def test_project_management_window_creation(self, mock_treeview, mock_toplevel):
        """Test creating a project management window"""
        from tick_tock_widget.project_management import ProjectManagementWindow

        # Mock dependencies
        mock_parent = Mock()
        mock_parent.root = Mock()
        mock_parent.root.winfo_x.return_value = 100
        mock_parent.root.winfo_y.return_value = 100
        mock_data_manager = Mock()
        mock_data_manager.projects = []
        mock_data_manager.get_project_aliases.return_value = []        # Mock theme
        mock_theme = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        
        window = ProjectManagementWindow(
            parent_widget=mock_parent,
            data_manager=mock_data_manager,
            theme=mock_theme
        )
        
        # Verify window was created
        assert window is not None
        assert window.parent_widget == mock_parent
        assert window.data_manager == mock_data_manager
        assert window.theme == mock_theme
    
    @patch('tick_tock_widget.project_management.tk.Toplevel')
    def test_project_management_window_methods(self, mock_toplevel):
        """Test project management window methods exist"""
        from tick_tock_widget.project_management import ProjectManagementWindow
        
        # Mock dependencies  
        mock_parent = Mock()
        mock_parent.root = Mock()
        mock_parent.root.winfo_x.return_value = 100
        mock_parent.root.winfo_y.return_value = 100
        mock_data_manager = Mock()
        mock_data_manager.projects = []
        mock_data_manager.get_project_aliases.return_value = []
        
        mock_theme = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        
        window = ProjectManagementWindow(
            parent_widget=mock_parent,
            data_manager=mock_data_manager,
            theme=mock_theme
        )
        
        # Check that window has expected methods
        assert hasattr(window, 'create_widgets')
        assert hasattr(window, 'populate_projects')
        assert hasattr(window, 'close')
        
        # Test methods are callable
        assert callable(window.create_widgets)
        assert callable(window.populate_projects)  
        assert callable(window.close)


@pytest.mark.gui
class TestProjectEditDialog:
    """Test the ProjectEditDialog class"""
    
    @patch('tick_tock_widget.project_management.tk.StringVar')
    @patch('tick_tock_widget.project_management.tk.Toplevel')
    def test_project_edit_dialog_creation(self, mock_toplevel, mock_stringvar):
        """Test creating a project edit dialog"""
        from tick_tock_widget.project_management import ProjectEditDialog

        # Mock dependencies
        mock_parent = Mock()
        mock_parent.winfo_x.return_value = 100
        mock_parent.winfo_y.return_value = 100
        mock_data_manager = Mock()
        mock_callback = Mock()
        mock_theme = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        
        # Test creating new project dialog
        dialog = ProjectEditDialog(
            parent=mock_parent,
            title="Test Dialog",
            theme=mock_theme
        )
        
        assert dialog is not None
        assert dialog.parent == mock_parent
        assert dialog.theme == mock_theme
    
    @patch('tick_tock_widget.project_management.tk.StringVar')
    @patch('tick_tock_widget.project_management.tk.Toplevel')
    def test_project_edit_dialog_with_existing_project(self, mock_toplevel, mock_stringvar):
        """Test creating dialog with existing project"""
        from tick_tock_widget.project_management import ProjectEditDialog
        from tick_tock_widget.project_data import Project
        
        # Mock dependencies
        mock_parent = Mock()
        mock_parent.winfo_x.return_value = 100
        mock_parent.winfo_y.return_value = 100
        mock_data_manager = Mock()
        mock_callback = Mock()
        
        # Mock existing project
        mock_project = Mock(spec=Project)
        mock_project.name = "Existing Project"
        mock_project.dz_number = "DZ123"
        mock_project.alias = "EP"
        
        mock_theme = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        
        # Test editing existing project
        dialog = ProjectEditDialog(
            parent=mock_parent,
            title="Edit Project",
            initial_name=mock_project.name,
            initial_dz=mock_project.dz_number,
            initial_alias=mock_project.alias,
            theme=mock_theme
        )
        
        assert dialog is not None
        assert dialog.parent == mock_parent


@pytest.mark.gui  
class TestSubActivityEditDialog:
    """Test the SubActivityEditDialog class"""
    
    @patch('tick_tock_widget.project_management.tk.StringVar')
    @patch('tick_tock_widget.project_management.tk.Toplevel')
    def test_sub_activity_edit_dialog_creation(self, mock_toplevel, mock_stringvar):
        """Test creating a sub-activity edit dialog"""
        from tick_tock_widget.project_management import SubActivityEditDialog
        from tick_tock_widget.project_data import Project
        
        # Mock dependencies
        mock_parent = Mock()
        mock_parent.winfo_x.return_value = 100
        mock_parent.winfo_y.return_value = 100
        mock_project = Mock(spec=Project)
        mock_callback = Mock()
        
        mock_theme = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        
        dialog = SubActivityEditDialog(
            parent=mock_parent,
            title="Test Sub-Activity",
            initial_name="Test Activity",
            theme=mock_theme
        )
        
        assert dialog is not None
        assert dialog.parent == mock_parent


@pytest.mark.gui
class TestMessageDialog:
    """Test the MessageDialog class"""
    
    @patch('tick_tock_widget.project_management.tk.Toplevel')
    def test_message_dialog_creation(self, mock_toplevel):
        """Test creating a message dialog"""
        from tick_tock_widget.project_management import MessageDialog

        mock_parent = Mock()
        mock_parent.winfo_x.return_value = 100
        mock_parent.winfo_y.return_value = 100
        mock_theme = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }
        
        dialog = MessageDialog(
            parent=mock_parent,
            title="Test Message",
            message="This is a test message",
            theme=mock_theme
        )
        
        assert dialog is not None
        assert dialog.parent == mock_parent
        assert dialog.theme['name'] == 'Test'


@pytest.mark.gui
class TestConfirmDialog:
    """Test the ConfirmDialog class"""
    
    @patch('tick_tock_widget.project_management.tk.Toplevel')
    def test_confirm_dialog_creation(self, mock_toplevel):
        """Test creating a confirmation dialog"""
        from tick_tock_widget.project_management import ConfirmDialog

        mock_parent = Mock()
        mock_parent.winfo_x.return_value = 100
        mock_parent.winfo_y.return_value = 100
        mock_callback = Mock()
        mock_theme = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#0078D4',
            'button_bg': '#404040',
            'button_fg': '#FFFFFF',
            'button_active': '#505050'
        }

        dialog = ConfirmDialog(
            parent=mock_parent,
            title="Confirm Action",
            message="Are you sure?"
        )
        
        assert dialog is not None
        assert dialog.parent == mock_parent
        assert dialog.result == False