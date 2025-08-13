"""
Unit tests for Config and Environment classes
"""
import pytest
from unittest.mock import Mock, patch, mock_open
import json
import tempfile
from pathlib import Path
import os

from tick_tock_widget.config import Config, Environment


class TestEnvironment:
    """Test Environment enum"""
    
    def test_environment_values(self):
        """Test Environment enum values"""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TEST.value == "test"
        assert Environment.PROTOTYPE.value == "prototype"


class TestConfig:
    """Test Config class"""
    
    def test_default_config_structure(self):
        """Test default configuration structure"""
        default = Config.DEFAULT_CONFIG
        
        assert "environment" in default
        assert "data_files" in default
        assert "environment_display" in default
        assert "auto_save_interval" in default
        assert "backup_enabled" in default
        assert "backup_directory" in default
        assert "max_backups" in default
        assert "debug_mode" in default
        assert "ui_settings" in default
    
    def test_init_with_default_config(self, temp_config_dir):
        """Test Config initialization with default values"""
        config_file = temp_config_dir / "config.json"
        
        with patch('tick_tock_widget.config.Path.__new__') as mock_path, \
             patch('sys.frozen', False, create=True):
            
            # Mock Path behavior
            mock_path.return_value.parent = temp_config_dir
            mock_path.return_value.__truediv__ = lambda self, other: temp_config_dir / other
            
            config = Config(config_file="config.json")
            
            # Should load default values when no config file exists
            assert config.config["environment"] == Environment.PROTOTYPE.value
            assert config.config["auto_save_interval"] == 300
            assert config.config["backup_enabled"] is True
            assert config.config["max_backups"] == 10
    
    def test_init_loads_existing_config(self, temp_config_dir):
        """Test Config initialization loads existing config file"""
        config_file = temp_config_dir / "config.json"
        
        # Create a config file with custom values
        custom_config = {
            "environment": Environment.DEVELOPMENT.value,
            "auto_save_interval": 600,
            "debug_mode": True
        }
        
        with open(config_file, 'w') as f:
            json.dump(custom_config, f)
        
        # Mock the Path and sys to make Config use our temp directory
        with patch('tick_tock_widget.config.Path') as mock_path_class, \
             patch('tick_tock_widget.config.sys') as mock_sys:
            
            # Mock sys.frozen
            mock_sys.frozen = False
            
            # Mock Path constructor to return our config file path
            def mock_path_init(path_str):
                if str(path_str).endswith('config.py'):
                    mock_path = Mock()
                    mock_path.parent = temp_config_dir
                    mock_path.__truediv__ = lambda self, other: temp_config_dir / other
                    return mock_path
                return Path(path_str)
            
            mock_path_class.side_effect = mock_path_init
            
            config = Config(config_file="config.json")
            
            # Should merge with defaults and load custom values
            assert config.config["environment"] == Environment.DEVELOPMENT.value
            assert config.config["auto_save_interval"] == 600
            assert config.config["debug_mode"] is True
            # Should still have default values for unspecified keys
            assert config.config["backup_enabled"] is True  # from defaults
    
    def test_get_environment(self):
        """Test getting current environment"""
        config = Config.__new__(Config)  # Create without calling __init__
        config.config = {"environment": Environment.DEVELOPMENT.value}
        
        result = config.get_environment()
        assert result == Environment.DEVELOPMENT
    
    def test_get_data_file(self):
        """Test getting data file path"""
        config = Config.__new__(Config)
        config.config = {
            "environment": Environment.TEST.value,
            "data_files": {
                "test": "test_data.json",
                "development": "dev_data.json"
            }
        }
        config.user_data_root = Path("/test/root")
        
        result = config.get_data_file()
        expected = Path("/test/root/test_data.json")
        assert result == str(expected)
    
    def test_get_window_title(self):
        """Test getting window title"""
        config = Config.__new__(Config)
        config.config = {
            "environment": Environment.DEVELOPMENT.value,
            "environment_display": {
                "development": {
                    "window_title": "Test Window [DEV]"
                }
            }
        }
        
        result = config.get_window_title()
        assert result == "Test Window [DEV]"
    
    def test_get_title_color(self):
        """Test getting title color"""
        config = Config.__new__(Config)
        config.config = {
            "environment": Environment.DEVELOPMENT.value,
            "environment_display": {
                "development": {
                    "title_color": "#00FF00"
                }
            }
        }
        
        result = config.get_title_color()
        assert result == "#00FF00"
    
    def test_get_border_color(self):
        """Test getting border color"""
        config = Config.__new__(Config)
        config.config = {
            "environment": Environment.DEVELOPMENT.value,
            "environment_display": {
                "development": {
                    "border_color": "#004400"
                }
            }
        }
        
        result = config.get_border_color()
        assert result == "#004400"
    
    def test_get_auto_save_interval(self):
        """Test getting auto save interval"""
        config = Config.__new__(Config)
        config.config = {"auto_save_interval": 600}
        
        result = config.get_auto_save_interval()
        assert result == 600
    
    def test_is_backup_enabled(self):
        """Test checking if backup is enabled"""
        config = Config.__new__(Config)
        config.config = {"backup_enabled": True}
        
        result = config.is_backup_enabled()
        assert result is True
    
    def test_get_backup_directory(self):
        """Test getting backup directory"""
        config = Config.__new__(Config)
        config.config = {"backup_directory": "user_data/backups"}
        config.user_data_root = Path("/test/root")
        
        result = config.get_backup_directory()
        expected = Path("/test/root/user_data/backups")
        assert result == expected
    
    def test_get_max_backups(self):
        """Test getting max backups"""
        config = Config.__new__(Config)
        config.config = {"max_backups": 15}
        
        result = config.get_max_backups()
        assert result == 15
    
    def test_is_debug_mode(self):
        """Test checking debug mode"""
        config = Config.__new__(Config)
        config.config = {"debug_mode": True}
        
        result = config.is_debug_mode()
        assert result is True
    
    def test_get_tree_state(self):
        """Test getting tree state"""
        config = Config.__new__(Config)
        config.config = {
            "ui_settings": {
                "tree_states": {
                    "project_management": {"item1": True, "item2": False}
                }
            }
        }
        
        result = config.get_tree_state("project_management")
        assert result == {"item1": True, "item2": False}
    
    def test_get_tree_state_not_found(self):
        """Test getting tree state for non-existent tree"""
        config = Config.__new__(Config)
        config.config = {
            "ui_settings": {
                "tree_states": {}
            }
        }
        
        result = config.get_tree_state("nonexistent")
        assert result == {}
    
    def test_set_tree_state(self):
        """Test setting tree state"""
        config = Config.__new__(Config)
        config.config = {
            "ui_settings": {
                "tree_states": {}
            }
        }
        config.config_file = Path("test_config.json")  # Add missing config_file attribute
        
        new_state = {"item1": True, "item2": False}
        with patch.object(config, 'save_config'):  # Mock save_config to avoid file operations
            config.set_tree_state("project_management", new_state)
        
        assert config.config["ui_settings"]["tree_states"]["project_management"] == new_state
    
    def test_set_environment(self):
        """Test setting environment"""
        config = Config.__new__(Config)
        config.config = {"environment": Environment.PRODUCTION.value}
        
        config.set_environment(Environment.DEVELOPMENT)
        
        assert config.config["environment"] == Environment.DEVELOPMENT.value
    
    def test_save_config(self, temp_config_dir):
        """Test saving configuration to file"""
        config_file = temp_config_dir / "config.json"
        
        config = Config.__new__(Config)
        config.config_file = config_file
        config.config = {
            "environment": Environment.TEST.value,
            "debug_mode": True
        }
        
        config.save_config()
        
        assert config_file.exists()
        
        # Verify saved content
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
            assert saved_data["environment"] == Environment.TEST.value
            assert saved_data["debug_mode"] is True
    
    def test_save_config_creates_directory(self, temp_config_dir):
        """Test save_config creates directory if it doesn't exist"""
        nested_dir = temp_config_dir / "nested" / "config"
        config_file = nested_dir / "config.json"
        
        config = Config.__new__(Config)
        config.config_file = config_file
        config.config = {"test": "value"}
        
        config.save_config()
        
        assert config_file.exists()
        assert nested_dir.exists()
    
    @patch('tick_tock_widget.config.platform.system')
    def test_get_user_data_directory_windows(self, mock_system):
        """Test getting user data directory on Windows"""
        mock_system.return_value = "Windows"
        
        with patch.dict(os.environ, {'LOCALAPPDATA': 'C:\\Users\\Test\\AppData\\Local'}):
            config = Config.__new__(Config)
            result = config._get_user_data_directory()
            
            expected = Path("C:\\Users\\Test\\AppData\\Local\\TickTock")
            assert result == expected
    
    @patch('tick_tock_widget.config.platform.system')
    def test_get_user_data_directory_macos(self, mock_system):
        """Test getting user data directory on macOS"""
        mock_system.return_value = "Darwin"
        
        with patch('tick_tock_widget.config.Path.home') as mock_home:
            mock_home.return_value = Path("/Users/test")
            
            config = Config.__new__(Config)
            result = config._get_user_data_directory()
            
            expected = Path("/Users/test/Library/Application Support/TickTock")
            assert result == expected
    
    @patch('tick_tock_widget.config.platform.system')
    def test_get_user_data_directory_linux(self, mock_system):
        """Test getting user data directory on Linux"""
        mock_system.return_value = "Linux"
        
        with patch.dict(os.environ, {'XDG_DATA_HOME': '/home/test/.local/share'}):
            config = Config.__new__(Config)
            result = config._get_user_data_directory()
            
            expected = Path("/home/test/.local/share/tick-tock")  # Fix: should be tick-tock not TickTock
            assert result == expected
    
    def test_migrate_data_file(self, temp_config_dir):
        """Test migrating data file between environments"""
        # Create source file
        source_file = temp_config_dir / "dev_data.json"
        source_data = {"projects": [], "test": "data"}
        with open(source_file, 'w') as f:
            json.dump(source_data, f)
        
        config = Config.__new__(Config)
        config.user_data_root = temp_config_dir
        config.config = {
            "data_files": {
                "development": "dev_data.json",
                "production": "prod_data.json"
            }
        }
        
        result = config.migrate_data_file(Environment.DEVELOPMENT, Environment.PRODUCTION)
        
        assert result is True
        
        # Check that target file was created
        target_file = temp_config_dir / "prod_data.json"
        assert target_file.exists()
        
        # Verify content was copied
        with open(target_file, 'r') as f:
            target_data = json.load(f)
            assert target_data == source_data
    
    def test_migrate_data_file_source_not_exists(self, temp_config_dir):
        """Test migrating when source file doesn't exist"""
        config = Config.__new__(Config)
        config.user_data_root = temp_config_dir
        config.config = {
            "data_files": {
                "development": "nonexistent.json",
                "production": "prod_data.json"
            }
        }
        
        result = config.migrate_data_file(Environment.DEVELOPMENT, Environment.PRODUCTION)
        
        assert result is False


@patch('tick_tock_widget.config._config_instance', None)
def test_get_config_singleton():
    """Test get_config returns singleton instance"""
    from tick_tock_widget.config import get_config
    
    with patch.object(Config, '__init__', return_value=None) as mock_init:
        # First call should create instance
        config1 = get_config()
        assert mock_init.call_count == 1
        
        # Second call should return same instance
        config2 = get_config()
        assert config1 is config2
        assert mock_init.call_count == 1  # Should not create new instance
