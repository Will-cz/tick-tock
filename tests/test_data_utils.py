"""
Test utilities for project management tests with efficient dummy data generation
This module provides dummy data generators for testing without file I/O overhead
"""

from typing import Dict, List, Any
from unittest.mock import MagicMock
import json
import io


class DummyDataGenerator:
    """Generates dummy test data for various test scenarios without file I/O"""
    
    @staticmethod
    def create_small_dataset() -> Dict[str, Any]:
        """Create a small dataset for basic testing (1-3 projects)"""
        return {
            "projects": [
                {
                    "name": "Test Project 1",
                    "alias": "TP1",
                    "description": "Basic test project",
                    "time_records": [
                        {"start": "2024-01-01T09:00:00", "end": "2024-01-01T10:00:00", "description": "Work session 1"}
                    ],
                    "metadata": {"priority": "high"},
                    "sub_activities": [
                        {"name": "Sub Activity 1", "alias": "SA1", "metadata": {"status": "active"}}
                    ]
                },
                {
                    "name": "Test Project 2", 
                    "alias": "TP2",
                    "description": "Another test project",
                    "time_records": [],
                    "metadata": {},
                    "sub_activities": []
                }
            ]
        }
    
    @staticmethod
    def create_medium_dataset() -> Dict[str, Any]:
        """Create a medium dataset for performance testing (10-20 projects)"""
        projects = []
        for i in range(15):
            projects.append({
                "name": f"Project {i+1}",
                "alias": f"P{i+1:02d}",
                "description": f"Description for project {i+1}",
                "time_records": [
                    {
                        "start": f"2024-01-{(i%30)+1:02d}T09:00:00",
                        "end": f"2024-01-{(i%30)+1:02d}T{10+(i%8):02d}:00:00",
                        "description": f"Work session {j+1}"
                    }
                    for j in range((i % 3) + 1)  # 1-3 time records per project
                ],
                "metadata": {"priority": "medium" if i % 2 == 0 else "low"},
                "sub_activities": [
                    {
                        "name": f"Sub Activity {j+1}",
                        "alias": f"SA{i+1}_{j+1}",
                        "metadata": {"status": "active" if j % 2 == 0 else "completed"}
                    }
                    for j in range((i % 4) + 1)  # 1-4 sub-activities per project
                ]
            })
        return {"projects": projects}
    
    @staticmethod
    def create_large_dataset() -> Dict[str, Any]:
        """Create a large dataset for stress testing (100+ projects)"""
        projects = []
        for i in range(150):
            projects.append({
                "name": f"Large Project {i+1}",
                "alias": f"LP{i+1:03d}",
                "description": f"Large scale project {i+1} with extensive data",
                "time_records": [
                    {
                        "start": f"2024-{((i//30)%12)+1:02d}-{(i%30)+1:02d}T{9+(j%8):02d}:00:00",
                        "end": f"2024-{((i//30)%12)+1:02d}-{(i%30)+1:02d}T{10+(j%8):02d}:00:00",
                        "description": f"Session {j+1} for project {i+1}"
                    }
                    for j in range((i % 10) + 1)  # 1-10 time records per project
                ],
                "metadata": {
                    "priority": ["high", "medium", "low"][i % 3],
                    "category": f"Category {(i % 5) + 1}",
                    "client": f"Client {(i % 8) + 1}"
                },
                "sub_activities": [
                    {
                        "name": f"Sub Activity {j+1} for Project {i+1}",
                        "alias": f"SA{i+1}_{j+1}",
                        "metadata": {
                            "status": ["active", "completed", "paused"][j % 3],
                            "effort": f"{(j % 5) + 1}h"
                        }
                    }
                    for j in range((i % 6) + 1)  # 1-6 sub-activities per project
                ]
            })
        return {"projects": projects}
    
    @staticmethod
    def create_empty_dataset() -> Dict[str, Any]:
        """Create an empty dataset for edge case testing"""
        return {"projects": []}


class MockDataManager:
    """Mock data manager that uses in-memory data without file I/O"""
    
    def __init__(self, dataset: Dict[str, Any]):
        """Initialize with dummy dataset"""
        self.data = dataset
        self.projects = []
        # Mock the project loading without actual file operations
        
    def load_projects(self):
        """Mock project loading"""
        pass
    
    def save_projects(self):
        """Mock project saving"""
        pass
    
    def add_project(self, name: str, alias: str, description: str) -> bool:
        """Mock project addition"""
        return True
    
    def remove_project(self, alias: str) -> bool:
        """Mock project removal"""
        return True
    
    def add_sub_activity(self, project_alias: str, name: str, alias: str) -> bool:
        """Mock sub-activity addition"""
        return True
    
    def remove_sub_activity(self, project_alias: str, sub_alias: str) -> bool:
        """Mock sub-activity removal"""
        return True


class MockProjectManagementTestBase:
    """Base class for project management tests with efficient dummy data"""
    
    @staticmethod
    def create_mock_parent_widget():
        """Create a properly mocked parent widget"""
        mock_parent = MagicMock()
        mock_parent.root = MagicMock()
        mock_parent.winfo_toplevel.return_value = MagicMock()
        mock_parent.project_mgmt_window = None
        return mock_parent
    
    @staticmethod
    def create_mock_data_manager(dataset_size: str = "small"):
        """Create a mock data manager with specified dataset size"""
        if dataset_size == "small":
            data = DummyDataGenerator.create_small_dataset()
        elif dataset_size == "medium":
            data = DummyDataGenerator.create_medium_dataset()
        elif dataset_size == "large":
            data = DummyDataGenerator.create_large_dataset()
        elif dataset_size == "empty":
            data = DummyDataGenerator.create_empty_dataset()
        else:
            data = DummyDataGenerator.create_small_dataset()
        
        return MockDataManager(data)
    
    @staticmethod
    def get_comprehensive_mocking_context():
        """Get the standard comprehensive mocking context"""
        from unittest.mock import patch
        return (
            patch('tick_tock_widget.project_management.tk'),
            patch('tick_tock_widget.project_management.ttk'), 
            patch('tick_tock_widget.project_management.ProjectEditDialog'),
            patch('tick_tock_widget.project_management.MessageDialog'),
            patch('tick_tock_widget.project_management.ConfirmDialog'),
            patch('tick_tock_widget.project_management.SubActivityEditDialog')
        )
    
    @staticmethod
    def configure_mock_widgets(mock_tk, mock_ttk, tree_data=None):
        """Configure mock widgets consistently"""
        mock_window = MagicMock()
        mock_tree = MagicMock()
        mock_frame = MagicMock()
        mock_button = MagicMock()
        
        # Configure tree data if provided
        if tree_data:
            mock_tree.get_children.return_value = tree_data.get('children', [])
            mock_tree.selection.return_value = tree_data.get('selection', ())
            mock_tree.item.return_value = tree_data.get('item_data', {'values': []})
            mock_tree.identify.return_value = tree_data.get('identify', "item")
        else:
            mock_tree.get_children.return_value = []
            mock_tree.selection.return_value = ()
            mock_tree.item.return_value = {'values': []}
            mock_tree.identify.return_value = "item"
        
        mock_tk.Toplevel.return_value = mock_window
        mock_ttk.Treeview.return_value = mock_tree
        mock_ttk.Frame.return_value = mock_frame
        mock_ttk.Button.return_value = mock_button
        
        return mock_window, mock_tree, mock_frame, mock_button


def create_performance_test_data():
    """Create test data specifically for performance testing"""
    return {
        "small_load": DummyDataGenerator.create_small_dataset(),
        "medium_load": DummyDataGenerator.create_medium_dataset(), 
        "large_load": DummyDataGenerator.create_large_dataset(),
        "edge_case": DummyDataGenerator.create_empty_dataset()
    }


def mock_file_operations():
    """Mock all file operations to prevent disk I/O during tests"""
    from unittest.mock import patch, mock_open
    
    def mock_json_load(fp):
        # Return dummy data instead of reading from file
        return DummyDataGenerator.create_small_dataset()
    
    def mock_json_dump(obj, fp, **kwargs):
        # Mock the dump operation without actual file write
        pass
    
    return (
        patch('json.load', side_effect=mock_json_load),
        patch('json.dump', side_effect=mock_json_dump),
        patch('builtins.open', mock_open()),
        patch('tempfile.NamedTemporaryFile')
    )
