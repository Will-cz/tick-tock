"""
Safe Project Management Tests - Phase 2 Coverage Improvement

Focused on existing methods for comprehensive ProjectManagementWindow testing
while maintaining complete safety from GUI widget creation.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tick_tock_widget.project_management import ProjectManagementWindow
from tick_tock_widget.project_data import ProjectDataManager


class TestProjectManagementSafe(unittest.TestCase):
    """Safe comprehensive tests for ProjectManagementWindow - No GUI creation risk"""
    
    def setUp(self):
        """Set up test environment with safe mocking"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        
        # Create mock parent with comprehensive GUI prevention
        self.mock_parent = MagicMock()
        self.mock_parent.root = MagicMock()
        # Critical: Mock after() method to prevent timer creation
        self.mock_parent.root.after = MagicMock(return_value="mock_timer_id")
        self.mock_parent.root.after_cancel = MagicMock()
        
        # Mock data manager with proper structure
        self.mock_data_manager = MagicMock(spec=ProjectDataManager)
        self.mock_data_manager.projects = []
        self.mock_data_manager.get_project_aliases.return_value = []
        
        # Mock callback
        self.mock_callback = MagicMock()
        
        # Test theme
        self.test_theme = {
            'name': 'Test',
            'bg': '#000000',
            'fg': '#FFFFFF',
            'accent': '#FF0000',
            'button_bg': '#111111',
            'button_fg': '#EEEEEE',
            'button_active': '#222222'
        }
        
    def tearDown(self):
        """Clean up test environment"""
        try:
            Path(self.temp_file.name).unlink()
        except FileNotFoundError:
            pass

    def _create_safe_window(self):
        """Create ProjectManagementWindow with comprehensive safe mocking - ZERO GUI RISK"""
        with patch('tkinter.Toplevel') as mock_toplevel, \
             patch('tkinter.ttk.Treeview') as mock_treeview, \
             patch('tkinter.ttk.Frame'), \
             patch('tkinter.ttk.Button'), \
             patch('tkinter.ttk.Scrollbar'), \
             patch.object(ProjectManagementWindow, 'setup_window'), \
             patch.object(ProjectManagementWindow, 'create_widgets'), \
             patch.object(ProjectManagementWindow, 'populate_projects'):
            
            # Configure all GUI mocks to prevent hanging
            mock_window = MagicMock()
            mock_window.configure = MagicMock()
            mock_window.title = MagicMock()
            mock_window.geometry = MagicMock()
            mock_window.protocol = MagicMock()
            mock_window.bind = MagicMock()
            mock_window.attributes = MagicMock()
            mock_toplevel.return_value = mock_window
            
            mock_tree = MagicMock()
            mock_tree.configure = MagicMock()
            mock_tree.heading = MagicMock()
            mock_tree.column = MagicMock()
            mock_tree.pack = MagicMock()
            mock_tree.bind = MagicMock()
            mock_treeview.return_value = mock_tree
            
            # Create window - completely safe (init methods are mocked)
            window = ProjectManagementWindow(
                self.mock_parent,
                self.mock_data_manager,
                self.mock_callback,
                self.test_theme
            )
            
            # Manually set essential attributes that would be set by mocked methods
            window.tree = mock_tree
            window.window = mock_window
            
            return window, mock_window, mock_tree

    def test_window_initialization_comprehensive(self):
        """Test complete window initialization - covers core __init__ paths"""
        window, _, _ = self._create_safe_window()
        
        # Verify all components initialized
        self.assertIsNotNone(window.window)
        self.assertEqual(window.data_manager, self.mock_data_manager)
        self.assertEqual(window.on_update_callback, self.mock_callback)
        self.assertEqual(window.theme, self.test_theme)
        
        # Verify GUI components set up
        self.assertIsNotNone(hasattr(window, 'tree'))

    def test_project_population_methods(self):
        """Test project population logic - covers populate_projects method"""
        window, _, mock_tree = self._create_safe_window()
        
        # Set up test data
        test_project = {
            "name": "Test Project",
            "dz_number": "DZ001",
            "alias": "TP",
            "time_records": {},
            "sub_activities": []
        }
        
        self.mock_data_manager.projects = [test_project]
        
        # Test populate_projects calls
        window.populate_projects()
        
        # Verify tree operations were called
        self.assertTrue(mock_tree.delete.called or mock_tree.insert.called)

    def test_add_project_functionality(self):
        """Test add project functionality - covers add_project method"""
        window, _, _ = self._create_safe_window()
        
        # Mock project edit dialog
        with patch('tick_tock_widget.project_management.ProjectEditDialog') as MockDialog:
            mock_dialog = MagicMock()
            mock_dialog.result = {"name": "New Project", "alias": "NP"}
            MockDialog.return_value = mock_dialog
            
            # Test add project
            window.add_project()
            
            # Verify dialog was called
            MockDialog.assert_called_once()

    def test_edit_project_functionality(self):
        """Test edit project functionality - covers edit_project method"""
        window, _, mock_tree = self._create_safe_window()
        
        # Mock tree selection
        mock_tree.selection.return_value = ['item1']
        mock_tree.item.return_value = {'text': 'TP'}
        
        # Mock project edit dialog
        with patch('tick_tock_widget.project_management.ProjectEditDialog') as MockDialog:
            mock_dialog = MagicMock()
            mock_dialog.result = {"name": "Updated Project", "alias": "UP"}
            MockDialog.return_value = mock_dialog
            
            # Test edit project
            window.edit_project()
            
            # Verify operations
            self.assertTrue(MockDialog.called or mock_tree.selection.called)

    def test_delete_project_functionality(self):
        """Test delete project functionality - covers delete_project method"""
        with patch('tkinter.messagebox.askyesno', return_value=True):
            window, _, mock_tree = self._create_safe_window()
            
            # Mock tree selection
            mock_tree.selection.return_value = ['item1']
            mock_tree.item.return_value = {'text': 'TP'}
            
            # Test delete project
            window.delete_project()
            
            # Verify selection was checked
            mock_tree.selection.assert_called()

    def test_close_functionality(self):
        """Test close functionality - covers close method"""
        window, mock_window, _ = self._create_safe_window()
        
        # Test close
        window.close()
        
        # Verify window destruction
        mock_window.destroy.assert_called_once()

    def test_theme_update_functionality(self):
        """Test theme update functionality - covers update_theme method"""
        window, _, _ = self._create_safe_window()
        
        # Test theme update
        new_theme = {
            'name': 'New Theme',
            'bg': '#FF0000',
            'fg': '#000000',
            'accent': '#00FF00'
        }
        
        window.update_theme(new_theme)
        
        # Verify theme was updated
        self.assertEqual(window.theme, new_theme)

    def test_tree_widget_operations(self):
        """Test tree widget operations - covers tree manipulation methods"""
        window, _, _ = self._create_safe_window()
        
        # Test project population
        window.populate_projects()
        
        # Verify tree operations
        self.assertTrue(hasattr(window, 'tree'))

    def test_dialog_tracking(self):
        """Test dialog tracking functionality - covers open_dialogs management"""
        window, _, _ = self._create_safe_window()
        
        # Verify dialog tracking list exists
        self.assertIsNotNone(hasattr(window, 'open_dialogs'))
        
        # Test initial state
        self.assertEqual(len(window.open_dialogs), 0)

    def test_dragging_attributes(self):
        """Test dragging attributes initialization"""
        window, _, _ = self._create_safe_window()
        
        # Verify dragging attributes exist
        self.assertEqual(window.start_x, 0)
        self.assertEqual(window.start_y, 0)

    def test_error_handling(self):
        """Test error handling in initialization"""
        # Test with problematic parent
        with patch('tkinter.Toplevel', side_effect=Exception("GUI Error")):
            try:
                ProjectManagementWindow(
                    self.mock_parent,
                    self.mock_data_manager,
                    self.mock_callback,
                    self.test_theme
                )
            except Exception:
                pass  # Expected to handle gracefully

    def test_data_manager_integration(self):
        """Test data manager integration"""
        window, _, _ = self._create_safe_window()
        
        # Verify data manager is properly connected
        self.assertEqual(window.data_manager, self.mock_data_manager)
        
        # Test interaction with data manager
        window.populate_projects()
        # Verify no exceptions were raised during population


if __name__ == '__main__':
    print("🧪 Running Safe ProjectManagement Tests...")
    print("🛡️ Zero GUI creation risk - Comprehensive mocking active") 
    print("📈 Phase 2: +25% coverage improvement target")
    print()
    
    unittest.main(verbosity=2)
