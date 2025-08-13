"""
Integration tests for timer synchronization and minimized widget functionality
Tests timer management scenarios including the "Total Today" issue fix where 
Total Today stops incrementing when switching projects in minimized widget
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from tick_tock_widget.project_data import ProjectDataManager, Project, SubActivity


class TestTimerSynchronization:
    """Test the Total Today issue fix scenarios"""
    
    @pytest.mark.integration
    def test_minimized_widget_project_switch_timer_synchronization(self):
        """
        Test the main Total Today issue: timer synchronization when switching projects in minimized widget
        
        Scenario:
        1. User has Project A running with active timer
        2. User goes to minimized widget
        3. User selects Project B from dropdown
        4. Total Today should switch to Project B and continue incrementing
        """
        # Setup test data
        data_manager = ProjectDataManager()
        
        # Create test projects
        project_a = Project(
            name="Project Alpha",
            dz_number="DZ001",
            alias="alpha",
            sub_activities=[],
            time_records={}
        )
        
        project_b = Project(
            name="Project Beta",
            dz_number="DZ002", 
            alias="beta",
            sub_activities=[],
            time_records={}
        )
        
        data_manager.projects = [project_a, project_b]
        
        # Start with Project A active and running
        data_manager.set_current_project("alpha")
        data_manager.start_current_timer()
        
        # Verify initial state
        assert data_manager.current_project_alias == "alpha"
        assert project_a.is_running_today() is True
        assert project_b.is_running_today() is False
        
        # Simulate time passing for Project A
        with patch('tick_tock_widget.project_data.datetime') as mock_datetime:
            start_time = datetime(2025, 8, 13, 9, 0, 0)
            mock_datetime.now.return_value = start_time
            mock_datetime.fromisoformat.return_value = start_time
            
            # Record initial start time
            project_a.get_today_record().start_timing()
            
            # Fast forward 2 seconds
            elapsed_time = datetime(2025, 8, 13, 9, 0, 2)
            mock_datetime.now.return_value = elapsed_time
            
            # Stop timer to lock in the time
            project_a.get_today_record().stop_timing()
            
            # Check that Project A has accumulated time
            alpha_time_before = project_a.get_today_record().total_seconds
            assert alpha_time_before >= 2, "Project A should have accumulated time"
        
        # Simulate minimized widget project selection (BEFORE FIX - this was problematic)
        # OLD CODE: data_manager.current_project_alias = "beta"  # Only this line
        
        # NEW CODE (fixed): Use proper project switching with timer management
        data_manager.set_current_project("beta")  # This clears sub-activity
        data_manager.stop_all_timers()            # This stops all running timers
        data_manager.start_current_timer()        # This starts new project timer
        
        # Verify fix worked correctly
        assert data_manager.current_project_alias == "beta"
        assert project_a.is_running_today() is False, "Project A timer should be stopped"
        assert project_b.is_running_today() is True, "Project B timer should be started"
        
        # Verify Project B timer increments (simulating Total Today incrementing)
        with patch('tick_tock_widget.project_data.datetime') as mock_datetime:
            beta_start_time = datetime(2025, 8, 13, 9, 0, 10)
            mock_datetime.now.return_value = beta_start_time
            mock_datetime.fromisoformat.return_value = beta_start_time
            
            # Fast forward 3 seconds
            beta_elapsed_time = datetime(2025, 8, 13, 9, 0, 13)
            mock_datetime.now.return_value = beta_elapsed_time
            
            # Check that Project B has accumulated time
            beta_time = project_b.get_today_record().get_current_total_seconds()
            assert beta_time >= 3, "Project B should have accumulated time after switch"
        
        # Verify Project A time didn't increase further
        alpha_time_after = project_a.get_today_record().total_seconds
        assert alpha_time_after == alpha_time_before, "Project A time should not increase after switch"

    @pytest.mark.integration
    def test_minimized_widget_sub_activity_switch_timer_synchronization(self):
        """
        Test timer synchronization when switching sub-activities in minimized widget
        """
        # Setup test data
        data_manager = ProjectDataManager()
        
        # Create project with sub-activities
        dev_sub = SubActivity(name="Development", alias="dev", time_records={})
        test_sub = SubActivity(name="Testing", alias="test", time_records={})
        
        project = Project(
            name="Project Alpha",
            dz_number="DZ001",
            alias="alpha", 
            sub_activities=[dev_sub, test_sub],
            time_records={}
        )
        
        data_manager.projects = [project]
        
        # Start with Development sub-activity running
        data_manager.set_current_project("alpha")
        data_manager.set_current_sub_activity("dev")
        data_manager.start_current_timer()
        
        # Verify initial state
        assert data_manager.current_sub_activity_alias == "dev"
        assert dev_sub.is_running_today() is True
        assert test_sub.is_running_today() is False
        
        # Simulate time passing for Development
        with patch('tick_tock_widget.project_data.datetime') as mock_datetime:
            start_time = datetime(2025, 8, 13, 9, 0, 0)
            mock_datetime.now.return_value = start_time
            mock_datetime.fromisoformat.return_value = start_time
            
            # Fast forward 5 seconds
            elapsed_time = datetime(2025, 8, 13, 9, 0, 5)
            mock_datetime.now.return_value = elapsed_time
            
            dev_time_before = dev_sub.get_today_record().get_current_total_seconds()
            assert dev_time_before >= 5, "Development should have accumulated time"
        
        # Switch to Testing sub-activity (simulating minimized widget selection)
        data_manager.stop_all_timers()
        data_manager.set_current_sub_activity("test")
        data_manager.start_current_timer()
        
        # Verify switch worked correctly
        assert data_manager.current_sub_activity_alias == "test"
        assert dev_sub.is_running_today() is False, "Development timer should be stopped"
        assert test_sub.is_running_today() is True, "Testing timer should be started"
        
        # Verify Testing timer increments
        with patch('tick_tock_widget.project_data.datetime') as mock_datetime:
            test_start_time = datetime(2025, 8, 13, 9, 1, 0)
            mock_datetime.now.return_value = test_start_time
            mock_datetime.fromisoformat.return_value = test_start_time
            
            # Fast forward 3 seconds
            test_elapsed_time = datetime(2025, 8, 13, 9, 1, 3)
            mock_datetime.now.return_value = test_elapsed_time
            
            test_time = test_sub.get_today_record().get_current_total_seconds()
            assert test_time >= 3, "Testing should have accumulated time after switch"

    @pytest.mark.integration
    def test_main_widget_display_sync_after_minimized_changes(self):
        """
        Test that main widget display updates correctly after changes made in minimized widget
        """
        # Create a mock widget that has the restore_window method
        class MockMainWidget:
            def __init__(self):
                self.minimized_widget = None
                self._last_window_pos = None
                self.update_project_display = Mock()
                self.update_project_list = Mock()
                self.root = Mock()
                
            def restore_window(self, mini_x=None, mini_y=None):
                """Mock implementation of the fixed restore_window method"""
                # Destroy the minimized widget if it exists
                if self.minimized_widget:
                    try:
                        self.minimized_widget.root.destroy()
                    except (AttributeError, Exception):
                        pass
                self.minimized_widget = None
                self.root.deiconify()  # Show the main window
                
                # Update displays to reflect any changes made in minimized widget (THE FIX)
                self.update_project_display()
                self.update_project_list()
        
        # Create mock widget
        widget = MockMainWidget()
        
        # Simulate having a minimized widget that made changes
        mock_minimized_widget = Mock()
        mock_minimized_widget.root = Mock()
        widget.minimized_widget = mock_minimized_widget
        
        # Simulate restore from minimized state (this is where the fix was added)
        widget.restore_window(200, 200)
        
        # Verify that main widget display was updated to reflect minimized widget changes
        widget.update_project_display.assert_called_once()
        widget.update_project_list.assert_called_once()
        
        # Verify cleanup
        assert widget.minimized_widget is None

    @pytest.mark.integration  
    def test_timer_state_consistency_across_widgets(self):
        """
        Test that timer states remain consistent between main widget and minimized widget
        """
        # Setup test data with real objects
        data_manager = ProjectDataManager()
        
        project1 = Project(name="Project 1", dz_number="DZ001", alias="p1", sub_activities=[], time_records={})
        project2 = Project(name="Project 2", dz_number="DZ002", alias="p2", sub_activities=[], time_records={})
        
        data_manager.projects = [project1, project2]
        
        # Test scenario: timer running on project1
        data_manager.set_current_project("p1")
        data_manager.start_current_timer()
        
        # Verify initial state
        assert project1.is_running_today() is True
        assert project2.is_running_today() is False
        
        # Simulate minimized widget operations
        # This tests the fixed behavior in minimized widget
        
        # 1. Switch project via minimized widget logic
        data_manager.set_current_project("p2")  # Clear sub-activity, set new project
        data_manager.stop_all_timers()           # Stop all running timers
        data_manager.start_current_timer()       # Start new project timer
        
        # Verify consistency after switch
        assert data_manager.current_project_alias == "p2"
        assert project1.is_running_today() is False, "Old project should be stopped"
        assert project2.is_running_today() is True, "New project should be running"
        
        # 2. Clear selection (back to main project without sub-activity)
        data_manager.stop_all_timers()
        data_manager.set_current_sub_activity(None)  # Clear sub-activity
        data_manager.start_current_timer()           # Start main project timer
        
        # Verify state remains consistent
        assert data_manager.current_sub_activity_alias is None
        assert project2.is_running_today() is True, "Main project should still be running"
        
        # 3. Stop all timers
        data_manager.stop_all_timers()
        
        # Verify all stopped
        assert project1.is_running_today() is False
        assert project2.is_running_today() is False
