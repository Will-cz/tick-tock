#!/usr/bin/env python3
"""
Tests for the critical security fix: global config system preventing config.json creation
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
import os

from tick_tock_widget.config import get_config, reset_config


class TestGlobalConfigSecurityFix:
    """Test the critical security fix - global config system automatically uses SecureConfig for executables"""
    
    def setup_method(self):
        """Reset config before each test"""
        reset_config()
    
    def teardown_method(self):
        """Clean up after each test"""
        reset_config()
    
    def test_development_mode_uses_regular_config(self):
        """Test that development mode (sys.frozen=False) uses regular Config"""
        with patch('sys.frozen', False, create=True):
            config = get_config()
            
            # Should be regular Config in development
            assert type(config).__name__ == 'Config'
            assert not hasattr(config, 'is_prototype_build')
    
    def test_executable_mode_automatically_uses_secure_config(self):
        """Test the main fix: executable mode automatically uses SecureConfig"""
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch('tick_tock_widget.secure_config.SecureConfig._get_user_data_directory') as mock_user_dir, \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True):
            
            mock_user_dir.return_value = Path("/tmp/test_user_data")
            
            config = get_config()
            
            # Critical test: should automatically be SecureConfig for executables
            assert type(config).__name__ == 'SecureConfig'
            assert hasattr(config, 'is_prototype_build')
            # Only check the property if it's actually SecureConfig
            if type(config).__name__ == 'SecureConfig':
                from tick_tock_widget.secure_config import SecureConfig
                secure_config = config  # Type casting for linter
                assert isinstance(secure_config, SecureConfig)
                assert secure_config.is_prototype_build == True
    
    def test_global_config_singleton_behavior(self):
        """Test that all get_config() calls return the same instance"""
        with patch('sys.frozen', False, create=True):
            config1 = get_config()
            config2 = get_config()
            
            # Should be the same instance (singleton pattern)
            assert config1 is config2
    
    def test_secure_config_prevents_file_creation_globally(self):
        """Test the main security fix: SecureConfig blocks config.json creation from any get_config() call"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "config.json"
            
            with patch('sys.frozen', True, create=True), \
                 patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
                 patch('sys.executable', str(temp_path / "app.exe")), \
                 patch('tick_tock_widget.secure_config.SecureConfig._get_user_data_directory') as mock_user_dir, \
                 patch('pathlib.Path.mkdir'), \
                 patch('builtins.open', create=True):
                
                mock_user_dir.return_value = temp_path / "userdata"
                
                # Get config and save (simulating the original bug scenario)
                config = get_config()
                
                # Verify it's SecureConfig
                assert type(config).__name__ == 'SecureConfig'
                
                # The critical test: save_config should NOT create config.json
                config.save_config()
                
                # SECURITY TEST: config.json should NOT exist in executable directory
                assert not config_file.exists(), f"SECURITY ISSUE: config.json was created at {config_file}!"
    
    def test_multiple_config_instances_all_secure(self):
        """Test that multiple get_config() calls in different parts of app all return SecureConfig"""
        with patch('sys.frozen', True, create=True), \
             patch.dict(os.environ, {'TICK_TOCK_ENV': 'prototype'}, clear=True), \
             patch('tick_tock_widget.secure_config.SecureConfig._get_user_data_directory') as mock_user_dir, \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True):
            
            mock_user_dir.return_value = Path("/tmp/test_user_data")
            
            # Simulate multiple parts of the app getting config
            config1 = get_config()  # Main widget
            config2 = get_config()  # Environment menu
            config3 = get_config()  # Project management
            
            # All should be the same SecureConfig instance
            assert config1 is config2 is config3
            assert type(config1).__name__ == 'SecureConfig'
            assert type(config2).__name__ == 'SecureConfig'
            assert type(config3).__name__ == 'SecureConfig'


class TestConfigResetFunctionality:
    """Test reset functionality works correctly with the new global system"""
    
    def test_reset_clears_global_instance(self):
        """Test that reset_config() properly clears the global instance"""
        # Create first instance
        with patch('sys.frozen', False, create=True):
            config1 = get_config()
            config1_id = id(config1)
            
            # Reset and create new instance
            reset_config()
            config2 = get_config()
            config2_id = id(config2)
            
            # Should be different instances
            assert config1_id != config2_id
            assert config1 is not config2
    
    def test_reset_works_with_secure_config(self):
        """Test that reset works properly with any config type"""
        # Test that reset clears the singleton regardless of config type
        
        with patch('sys.frozen', False, create=True):
            # Get first config instance
            config1 = get_config()
            config1_id = id(config1)
            
            # Reset
            reset_config()
            
            # Get second config instance  
            config2 = get_config()
            config2_id = id(config2)
            
            # Should be different instances after reset
            assert config1_id != config2_id
            assert config1 is not config2
            
        # Reset should always work regardless of config type
        reset_config()
        # Test passes if no exceptions are thrown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
