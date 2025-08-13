"""
Integration tests for secure configuration functionality
"""
import tempfile
from pathlib import Path
from unittest.mock import patch

from tick_tock_widget.secure_config import SecureConfig
from tick_tock_widget.config import Environment
from tick_tock_widget.project_data import ProjectDataManager


class TestSecureConfigIntegration:
    """Integration tests for secure configuration with other components"""

    def test_secure_config_with_project_data_manager(self):
        """Test that ProjectDataManager works with SecureConfig in prototype mode"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_secure_integration"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict('os.environ', {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir):
            
            # Create secure config
            config = SecureConfig()
            
            # Verify it's in secure mode
            assert config.is_prototype_build
            assert config.get_environment() == Environment.PROTOTYPE
            
            # Mock the global config to return our secure config
            with patch('tick_tock_widget.project_data.get_config', return_value=config):
                # Test that ProjectDataManager can use the secure config
                data_manager = ProjectDataManager()
                
                # Verify data file path is in user directory
                assert test_user_dir.as_posix() in data_manager.data_file.as_posix()
                assert "tick_tock_projects_prototype.json" in data_manager.data_file.name
                
                # Verify backup is enabled
                assert data_manager.config.is_backup_enabled()

    def test_secure_config_data_isolation(self):
        """Test that secure config properly isolates data to prototype environment"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_data_isolation"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict('os.environ', {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir):
            
            config = SecureConfig()
            
            # Should only return prototype data file
            data_file = config.get_data_file()
            assert "tick_tock_projects_prototype.json" in data_file
            
            # Should not be able to access other environment data files
            dev_data_file = config.get_data_file(Environment.DEVELOPMENT)
            assert dev_data_file == data_file  # Should return same prototype file
            
            prod_data_file = config.get_data_file(Environment.PRODUCTION)
            assert prod_data_file == data_file  # Should return same prototype file

    def test_secure_config_backup_enforcement(self):
        """Test that backup functionality cannot be disabled in secure mode"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_backup_enforcement"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict('os.environ', {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir):
            
            config = SecureConfig()
            
            # Verify backup is enabled by default
            assert config.is_backup_enabled()
            
            # Try to disable backup - should be ignored
            config.set("backup_enabled", False)
            assert config.is_backup_enabled()  # Should still be True
            
            # Backup directory should be properly set
            backup_dir = config.get_backup_directory()
            assert backup_dir == test_user_dir / "backups"

    def test_secure_config_environment_lock(self):
        """Test that environment cannot be changed in secure mode"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_env_lock"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict('os.environ', {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir):
            
            config = SecureConfig()
            
            # Verify initial environment
            assert config.get_environment() == Environment.PROTOTYPE
            
            # Try to change environment - should be ignored
            config.set_environment(Environment.DEVELOPMENT)
            assert config.get_environment() == Environment.PROTOTYPE
            
            config.set_environment(Environment.PRODUCTION)
            assert config.get_environment() == Environment.PROTOTYPE
            
            config.set_environment(Environment.TEST)
            assert config.get_environment() == Environment.PROTOTYPE

    def test_secure_config_ui_settings_preservation(self):
        """Test that UI settings can still be saved and loaded in secure mode"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_ui_settings"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict('os.environ', {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir):
            
            config = SecureConfig()
            
            # Should be able to modify UI settings
            test_ui_settings = {
                "tree_states": {
                    "project_management": {
                        "project_test": 1,
                        "project_example": 0
                    }
                }
            }
            
            config.set("ui_settings", test_ui_settings)
            assert config.get("ui_settings") == test_ui_settings
            
            # Should be able to save config (saves only UI settings)
            config.save_config()  # Should not raise exception

    def test_development_vs_secure_mode_behavior(self):
        """Test different behavior between development and secure modes"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_mode_comparison"
        
        # Test development mode
        with patch('sys.frozen', False, create=True), \
             patch.dict('os.environ', {}, clear=True):
            
            dev_config = SecureConfig()
            assert not dev_config.is_prototype_build
            
            # Should allow environment changes in development
            original_env = dev_config.get_environment()
            dev_config.set_environment(Environment.PRODUCTION)
            new_env = dev_config.get_environment()
            assert new_env != original_env  # Should have changed
        
        # Test secure mode
        with patch('sys.frozen', True, create=True), \
             patch.dict('os.environ', {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir):
            
            secure_config = SecureConfig()
            assert secure_config.is_prototype_build
            
            # Should NOT allow environment changes in secure mode
            original_env = secure_config.get_environment()
            secure_config.set_environment(Environment.PRODUCTION)
            new_env = secure_config.get_environment()
            assert new_env == original_env  # Should NOT have changed

    def test_secure_config_critical_settings_lock(self):
        """Test that all critical settings are properly locked in secure mode"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_critical_lock"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict('os.environ', {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir):
            
            config = SecureConfig()
            
            # Test all critical settings are locked
            critical_tests = [
                ("backup_enabled", False, True),
                ("debug_mode", True, False),
                ("auto_save_interval", 600, 300),
                ("max_backups", 5, 10),
            ]
            
            for setting, test_value, expected_value in critical_tests:
                # Try to change the setting
                config.set(setting, test_value)
                
                # Verify it wasn't changed
                if setting == "backup_enabled":
                    actual = config.is_backup_enabled()
                elif setting == "debug_mode":
                    actual = config.is_debug_mode()
                elif setting == "auto_save_interval":
                    actual = config.get_auto_save_interval()
                elif setting == "max_backups":
                    actual = config.get_max_backups()
                
                assert actual == expected_value, f"Setting {setting} should be locked to {expected_value}"
