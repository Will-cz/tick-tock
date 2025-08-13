"""
Unit tests for SecureConfig class and security features
"""
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open, Mock

from tick_tock_widget.secure_config import SecureConfig
from tick_tock_widget.config import Environment, Config


class TestSecureConfig:
    """Test SecureConfig class functionality"""

    def test_development_mode_behavior(self):
        """Test SecureConfig behaves like normal Config in development mode"""
        # Ensure we're not in executable mode
        with patch('sys.frozen', False, create=True), \
             patch.dict('os.environ', {}, clear=True):
            
            config = SecureConfig()
            
            # Should behave like regular config in development
            assert not config.is_executable
            assert not config.is_prototype_build
            # In development mode, SecureConfig falls back to regular Config behavior
            # which loads from config.json with environment "development"
            assert config.get_environment() == Environment.DEVELOPMENT

    def test_prototype_build_detection_via_env_var(self):
        """Test prototype build detection via TICK_TOCK_ENV environment variable"""
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory') as mock_user_dir:
            
            mock_user_dir.return_value = Path(tempfile.gettempdir()) / "test_ticktock"
            
            config = SecureConfig()
            
            assert config.is_executable
            assert config.is_prototype_build

    def test_prototype_build_detection_via_executable(self):
        """Test prototype build detection when running as executable"""
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory') as mock_user_dir, \
             patch.object(SecureConfig, '_is_prototype_build', return_value=True):
            
            mock_user_dir.return_value = Path(tempfile.gettempdir()) / "test_ticktock"
            
            config = SecureConfig()
            
            assert config.is_executable
            # Should be prototype build when frozen and _is_prototype_build returns True
            assert config.is_prototype_build

    def test_secure_mode_initialization(self):
        """Test secure mode initialization with proper directory setup"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_ticktock_secure"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir):
            
            config = SecureConfig()
            
            # Check secure mode properties
            assert config.is_prototype_build
            assert config.user_data_root == test_user_dir
            assert config.user_prefs_file == test_user_dir / "user_preferences.json"
            
            # Check locked configuration
            assert config.get_environment() == Environment.PROTOTYPE
            assert config.is_backup_enabled() is True
            assert config.is_debug_mode() is False
            assert config.get_auto_save_interval() == 300

    def test_environment_switching_blocked_in_secure_mode(self):
        """Test that environment switching is blocked in secure mode"""
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory') as mock_user_dir:
            
            mock_user_dir.return_value = Path(tempfile.gettempdir()) / "test_ticktock"
            
            config = SecureConfig()
            
            # Attempt to change environment
            original_env = config.get_environment()
            config.set_environment(Environment.DEVELOPMENT)
            
            # Environment should remain unchanged
            assert config.get_environment() == original_env
            assert config.get_environment() == Environment.PROTOTYPE

    def test_environment_switching_allowed_in_development(self):
        """Test that environment switching works in development mode"""
        with patch('sys.frozen', False, create=True), \
             patch.dict(os.environ, {}, clear=True):
            
            config = SecureConfig()
            
            # Should allow environment switching in development
            config.set_environment(Environment.PRODUCTION)
            assert config.get_environment() == Environment.PRODUCTION

    def test_critical_settings_protection_in_secure_mode(self):
        """Test that critical settings are protected in secure mode"""
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory') as mock_user_dir:
            
            mock_user_dir.return_value = Path(tempfile.gettempdir()) / "test_ticktock"
            
            config = SecureConfig()
            
            # Test backup_enabled protection
            original_backup = config.is_backup_enabled()
            config.set("backup_enabled", False)
            assert config.is_backup_enabled() == original_backup  # Should be unchanged
            
            # Test debug_mode protection
            original_debug = config.is_debug_mode()
            config.set("debug_mode", True)
            assert config.is_debug_mode() == original_debug  # Should be unchanged
            
            # Test auto_save_interval protection
            original_interval = config.get_auto_save_interval()
            config.set("auto_save_interval", 600)
            assert config.get_auto_save_interval() == original_interval  # Should be unchanged

    def test_allowed_settings_modification_in_secure_mode(self):
        """Test that allowed settings (UI) can be modified in secure mode"""
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory') as mock_user_dir:
            
            mock_user_dir.return_value = Path(tempfile.gettempdir()) / "test_ticktock"
            
            config = SecureConfig()
            
            # UI settings should be modifiable
            test_ui_settings = {"tree_states": {"test": True}}
            config.set("ui_settings", test_ui_settings)
            
            assert config.get("ui_settings") == test_ui_settings

    def test_hardcoded_values_in_secure_mode(self):
        """Test that hardcoded values are returned in secure mode"""
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory') as mock_user_dir:
            
            mock_user_dir.return_value = Path(tempfile.gettempdir()) / "test_ticktock"
            
            config = SecureConfig()
            
            # Test hardcoded values from PROTOTYPE_LOCKED_CONFIG
            assert config.get_environment() == Environment.PROTOTYPE
            assert config.is_backup_enabled() is True
            assert config.is_debug_mode() is False
            assert config.get_auto_save_interval() == 300
            assert config.get_max_backups() == 10

    def test_data_file_path_in_secure_mode(self):
        """Test data file path handling in secure mode"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_ticktock_data"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir):
            
            config = SecureConfig()
            
            data_file = config.get_data_file()
            expected_path = str(test_user_dir / "tick_tock_projects_prototype.json")
            
            assert data_file == expected_path

    def test_backup_directory_in_secure_mode(self):
        """Test backup directory handling in secure mode"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_ticktock_backup"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir):
            
            config = SecureConfig()
            
            backup_dir = config.get_backup_directory()
            expected_path = test_user_dir / "backups"
            
            assert backup_dir == expected_path

    def test_save_config_in_secure_mode(self):
        """Test config saving behavior in secure mode"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_ticktock_save"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir), \
             patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('builtins.open', mock_open()) as mock_file:
            
            config = SecureConfig()
            config.set("ui_settings", {"test_setting": "test_value"})
            
            config.save_config()
            
            # Should create user data directory
            mock_mkdir.assert_called_with(parents=True, exist_ok=True)
            
            # Should save to user preferences file (we verify the call was made)
            assert mock_file.called

    def test_save_config_in_development_mode(self):
        """Test config saving behavior in development mode"""
        with patch('sys.frozen', False, create=True), \
             patch.dict(os.environ, {}, clear=True), \
             patch.object(Config, 'save_config') as mock_save:
            
            config = SecureConfig()
            config.save_config()
            
            # Should call parent save_config method
            mock_save.assert_called_once()

    def test_user_preferences_loading(self):
        """Test loading user preferences from file"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_ticktock_load"
        test_prefs_data = {"ui_settings": {"loaded": True}}
        
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir), \
             patch.object(Path, 'exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(test_prefs_data))):
            
            config = SecureConfig()
            
            # Should have loaded the UI settings
            assert config.get("ui_settings") == test_prefs_data["ui_settings"]

    def test_user_preferences_loading_error_handling(self):
        """Test error handling when loading user preferences fails"""
        test_user_dir = Path(tempfile.gettempdir()) / "test_ticktock_error"
        
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory', return_value=test_user_dir), \
             patch.object(Path, 'exists', return_value=True), \
             patch('builtins.open', side_effect=OSError("File error")):
            
            # Should not raise exception, just continue with defaults
            config = SecureConfig()
            assert config.get("ui_settings", {}) == {}

    def test_config_comparison_with_base_class(self):
        """Test that SecureConfig maintains compatibility with base Config class"""
        with patch('sys.frozen', False, create=True), \
             patch.dict(os.environ, {}, clear=True):
            
            secure_config = SecureConfig()
            
            # Should have same interface
            assert hasattr(secure_config, 'get_environment')
            assert hasattr(secure_config, 'set_environment') 
            assert hasattr(secure_config, 'get_data_file')
            assert hasattr(secure_config, 'is_backup_enabled')
            assert hasattr(secure_config, 'save_config')
            
            # Should return same types
            assert isinstance(secure_config.get_environment(), Environment)
            assert isinstance(secure_config.is_backup_enabled(), bool)


class TestSecureConfigIntegration:
    """Integration tests for SecureConfig with other components"""

    def test_integration_with_tick_tock_widget(self):
        """Test integration with main TickTockWidget config initialization"""
        with patch('sys.frozen', True, create=True), \
             patch.dict('os.environ', {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory') as mock_user_dir:
            
            mock_user_dir.return_value = Path(tempfile.gettempdir()) / "test_integration"
            
            # Test the config detection logic that should run in __init__
            import sys
            is_executable = getattr(sys, 'frozen', False)
            is_prototype_build = os.environ.get('TICK_TOCK_ENV', '').lower() == 'prototype'
            
            assert is_executable
            assert is_prototype_build
            
            # Test that we can create SecureConfig in this scenario
            config = SecureConfig()
            assert isinstance(config, SecureConfig)
            assert config.is_prototype_build

    def test_environment_variable_detection(self):
        """Test environment variable detection logic"""
        with patch.object(SecureConfig, '_get_user_data_directory') as mock_user_dir:
            mock_user_dir.return_value = Path(tempfile.gettempdir()) / "test_env"
            
            # Test that without TICK_TOCK_ENV and not executable, should not be prototype
            with patch.dict(os.environ, {}, clear=True), \
                 patch('sys.frozen', False, create=True):
                
                config = SecureConfig()
                assert not config.is_prototype_build, "Should not be prototype build without env var or executable"
                
            # Test that with TICK_TOCK_ENV=prototype, should be detected
            with patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
                 patch('sys.frozen', False, create=True):
                
                config = SecureConfig()
                assert config.is_prototype_build, "Should detect TICK_TOCK_ENV=prototype"

    def test_prototype_marker_file_detection(self):
        """Test prototype detection via embedded marker file"""
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {}, clear=True), \
             patch.object(SecureConfig, '_get_user_data_directory') as mock_user_dir:
            
            mock_user_dir.return_value = Path(tempfile.gettempdir()) / "test_env"
            
            # Test with MEIPASS (PyInstaller bundle)
            with patch('sys._MEIPASS', '/tmp/meipass', create=True), \
                 patch('pathlib.Path.exists') as mock_exists:
                
                mock_exists.return_value = True
                config = SecureConfig()
                assert config.is_prototype_build == True
                
            # Test without MEIPASS but with marker file next to executable
            with patch('sys._MEIPASS', side_effect=AttributeError(), create=True), \
                 patch('sys.executable', '/path/to/app.exe'), \
                 patch('pathlib.Path.exists') as mock_exists:
                
                mock_exists.return_value = True
                config = SecureConfig()
                assert config.is_prototype_build == True


class TestSecureConfigHelperFunctions:
    """Test helper functions for SecureConfig"""

    def test_config_creation_functions(self):
        """Test that helper functions work without import errors"""
        # Test that we can create configs without import issues
        config1 = SecureConfig()
        config2 = SecureConfig("test_config.json")
        
        assert isinstance(config1, SecureConfig)
        assert isinstance(config2, SecureConfig)
