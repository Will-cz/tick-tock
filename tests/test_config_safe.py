"""
Safe configuration module tests - No GUI creation
Tests the config.py module functionality without any widget creation
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tick_tock_widget.config import get_config, Config, Environment, reset_config


class TestConfigModule(unittest.TestCase):
    """Test configuration module functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = Path(self.temp_dir) / "test_config.json"
        reset_config()  # Reset singleton for clean tests
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        reset_config()  # Clean up singleton
        try:
            shutil.rmtree(self.temp_dir)
        except (FileNotFoundError, OSError):
            pass
    
    def test_environment_enum(self):
        """Test Environment enum values"""
        self.assertEqual(Environment.DEVELOPMENT.value, "development")
        self.assertEqual(Environment.PRODUCTION.value, "production")
        self.assertEqual(Environment.TEST.value, "test")
    
    def test_config_creation_with_defaults(self):
        """Test config creation with default values"""
        config = Config()
        
        # Test default values
        env = config.get_environment()
        self.assertIn(env, [Environment.DEVELOPMENT, Environment.PRODUCTION, Environment.TEST])
        self.assertTrue(config.is_backup_enabled())
        self.assertEqual(config.get_max_backups(), 10)
        self.assertEqual(config.get_auto_save_interval(), 30)  # Default is 30 seconds
    
    def test_config_file_operations(self):
        """Test config file loading"""
        # Create test config data
        test_config_data = {
            "environment": "production",
            "backup_enabled": False,
            "max_backups": 5,
            "auto_save_interval": 600
        }
        
        # Write test config
        with open(self.test_config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config_data, f)
        
        # Test config loading with specific config file
        config = Config(str(self.test_config_file))
        
        self.assertEqual(config.get_environment(), Environment.PRODUCTION)
        self.assertFalse(config.is_backup_enabled())
        self.assertEqual(config.get_max_backups(), 5)
        self.assertEqual(config.get_auto_save_interval(), 600)
    
    def test_backup_directory_creation(self):
        """Test backup directory handling"""
        config = Config()
        backup_dir = config.get_backup_directory()
        
        # Should return a Path object
        self.assertIsInstance(backup_dir, Path)
        
        # Directory should be created automatically
        self.assertTrue(backup_dir.exists())
    
    def test_data_file_path_resolution(self):
        """Test data file path resolution"""
        config = Config()
        
        # Test default data file
        data_file = config.get_data_file()
        self.assertIsInstance(data_file, str)
        self.assertTrue(data_file.endswith('.json'))
        
        # Test environment variable override
        test_data_file = str(Path(self.temp_dir) / "custom_data.json")
        with patch.dict(os.environ, {'TICK_TOCK_DATA_FILE': test_data_file}):
            config = Config()
            self.assertEqual(config.get_data_file(), test_data_file)
    
    def test_config_validation_with_public_api(self):
        """Test config parameter validation using public API"""
        config = Config()
        
        # Test valid environment setting
        for env in Environment:
            config.set_environment(env)
            self.assertEqual(config.get_environment(), env)
        
        # Test backup count validation via config dict
        config.set('max_backups', 0)
        self.assertEqual(config.get_max_backups(), 0)
        
        config.set('max_backups', 100)
        self.assertEqual(config.get_max_backups(), 100)
    
    def test_get_config_singleton(self):
        """Test get_config function returns singleton"""
        config1 = get_config()
        config2 = get_config()
        
        # Should return the same instance
        self.assertIs(config1, config2)
        self.assertIsInstance(config1, Config)
    
    def test_display_configuration(self):
        """Test environment-specific display configuration"""
        config = Config()
        
        # Test window title for different environments
        for env in Environment:
            title = config.get_window_title(env)
            self.assertIsInstance(title, str)
            self.assertTrue(len(title) > 0)
            
            # Test colors
            title_color = config.get_title_color(env)
            self.assertIsInstance(title_color, str)
            self.assertTrue(title_color.startswith('#'))
            
            border_color = config.get_border_color(env)
            self.assertIsInstance(border_color, str)
            self.assertTrue(border_color.startswith('#'))
    
    def test_config_error_handling(self):
        """Test config error handling for invalid files"""
        # Create invalid JSON file
        invalid_config_file = Path(self.temp_dir) / "invalid.json"
        with open(invalid_config_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content {")
        
        # Should handle invalid JSON gracefully
        config = Config(str(invalid_config_file))
        # Should fall back to defaults
        env = config.get_environment()
        self.assertIn(env, [Environment.DEVELOPMENT, Environment.PRODUCTION, Environment.TEST])
    
    def test_environment_specific_settings(self):
        """Test environment-specific configuration"""
        # Test development environment
        with patch.dict(os.environ, {'TICK_TOCK_ENV': 'development'}):
            config = Config()
            self.assertEqual(config.get_environment(), Environment.DEVELOPMENT)
        
        # Test production environment  
        with patch.dict(os.environ, {'TICK_TOCK_ENV': 'production'}):
            config = Config()
            self.assertEqual(config.get_environment(), Environment.PRODUCTION)
        
        # Test test environment
        with patch.dict(os.environ, {'TICK_TOCK_ENV': 'test'}):
            config = Config()
            self.assertEqual(config.get_environment(), Environment.TEST)
    
    def test_debug_mode(self):
        """Test debug mode configuration"""
        config = Config()
        
        # Test default debug mode
        debug_mode = config.is_debug_mode()
        self.assertIsInstance(debug_mode, bool)
        
        # Test setting debug mode
        config.set('debug_mode', True)
        self.assertTrue(config.is_debug_mode())
        
        config.set('debug_mode', False)
        self.assertFalse(config.is_debug_mode())
    
    def test_data_migration(self):
        """Test data migration between environments"""
        config = Config()
        
        # Create mock data file for development
        dev_file = Path(config.get_data_file(Environment.DEVELOPMENT))
        dev_file.parent.mkdir(parents=True, exist_ok=True)
        test_data = {"projects": [{"name": "test"}]}
        with open(dev_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Test migration
        result = config.migrate_data_file(Environment.DEVELOPMENT, Environment.TEST)
        self.assertTrue(result)
        
        # Verify migration
        test_file = Path(config.get_data_file(Environment.TEST))
        self.assertTrue(test_file.exists())
        
        with open(test_file, 'r', encoding='utf-8') as f:
            migrated_data = json.load(f)
        self.assertEqual(migrated_data, test_data)


if __name__ == '__main__':
    unittest.main()
