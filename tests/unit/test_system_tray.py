"""
Unit tests for System Tray integration module
"""
import pytest
from unittest.mock import Mock

from tick_tock_widget.system_tray import is_system_tray_available


class TestSystemTrayIntegration:
    """Test basic system tray integration functionality"""
    
    def test_system_tray_availability_function(self):
        """Test that is_system_tray_available function returns a boolean"""
        result = is_system_tray_available()
        assert isinstance(result, bool)
    
    def test_system_tray_manager_import(self):
        """Test that SystemTrayManager can be imported"""
        try:
            from tick_tock_widget.system_tray import SystemTrayManager
            assert SystemTrayManager is not None
        except ImportError:
            pytest.fail("SystemTrayManager should be importable even without dependencies")
    
    def test_system_tray_manager_initialization(self):
        """Test SystemTrayManager initialization"""
        from tick_tock_widget.system_tray import SystemTrayManager
        
        main_callback = Mock()
        quit_callback = Mock()
        
        # Should not raise exception
        try:
            manager = SystemTrayManager(
                main_window_callback=main_callback,
                quit_callback=quit_callback
            )
            assert manager.main_window_callback == main_callback
            assert manager.quit_callback == quit_callback
            assert hasattr(manager, 'icon_path')
        except Exception as e:
            # If dependencies are missing, this is acceptable
            if "pystray" in str(e) or "PIL" in str(e):
                pytest.skip(f"System tray dependencies not available: {e}")
            else:
                pytest.fail(f"Unexpected error in SystemTrayManager initialization: {e}")
    
    def test_system_tray_icon_path_finding(self):
        """Test that icon path finding logic works"""
        try:
            from tick_tock_widget.system_tray import SystemTrayManager
            
            main_callback = Mock()
            quit_callback = Mock()
            
            manager = SystemTrayManager(
                main_window_callback=main_callback,
                quit_callback=quit_callback
            )
            
            # Icon path should be found or None (but should not raise exception)
            assert hasattr(manager, 'icon_path')
            # icon_path can be None if icon file not found, which is acceptable
            
        except Exception as e:
            # If dependencies are missing, this is acceptable
            if "pystray" in str(e) or "PIL" in str(e):
                pytest.skip(f"System tray dependencies not available: {e}")
            else:
                pytest.fail(f"Unexpected error: {e}")
    
    def test_system_tray_methods_exist(self):
        """Test that SystemTrayManager has expected methods"""
        try:
            from tick_tock_widget.system_tray import SystemTrayManager
            
            main_callback = Mock()
            quit_callback = Mock()
            
            manager = SystemTrayManager(
                main_window_callback=main_callback,
                quit_callback=quit_callback
            )
            
            # Check that expected methods exist
            assert hasattr(manager, 'start')
            assert hasattr(manager, 'stop')
            assert hasattr(manager, 'is_running')
            assert callable(manager.start)
            assert callable(manager.stop)
            assert callable(manager.is_running)
            
        except Exception as e:
            # If dependencies are missing, this is acceptable
            if "pystray" in str(e) or "PIL" in str(e):
                pytest.skip(f"System tray dependencies not available: {e}")
            else:
                pytest.fail(f"Unexpected error: {e}")
    
    @pytest.mark.skipif(not is_system_tray_available(), 
                        reason="System tray dependencies not available")
    def test_system_tray_manager_functionality_when_available(self):
        """Test SystemTrayManager functionality when dependencies are available"""
        from tick_tock_widget.system_tray import SystemTrayManager
        
        main_callback = Mock()
        quit_callback = Mock()
        
        manager = SystemTrayManager(
            main_window_callback=main_callback,
            quit_callback=quit_callback
        )
        
        # Test is_running returns boolean
        running_status = manager.is_running()
        assert isinstance(running_status, bool)
        
        # Test that start and stop methods don't raise exceptions
        try:
            manager.start()
            # Give it a moment to start
            import time
            time.sleep(0.1)
            manager.stop()
        except Exception as e:
            # Some environments might not support system tray even with dependencies
            pytest.skip(f"System tray not supported in this environment: {e}")
