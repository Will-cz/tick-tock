#!/usr/bin/env python3
"""
Configuration Management Testing
Tests configuration loading, validation, and environment-specific settings
Part of Phase 1 Initial Development testing framework
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import configparser

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tick_tock_widget.project_data import ProjectDataManager


class TestConfigurationManagement(unittest.TestCase):
    """Test configuration management and settings"""
    
    def setUp(self):
        """Set up configuration testing environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "config.ini"
        self.json_config_file = Path(self.temp_dir) / "config.json"
        self.env_config_file = Path(self.temp_dir) / ".env"
        
        print(f"\n⚙️ Configuration Test Setup:")
        print(f"   Temp Directory: {self.temp_dir}")
    
    def tearDown(self):
        """Clean up configuration test environment"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_ini_configuration_loading(self):
        """Test INI-style configuration file loading"""
        print("\n=== Configuration Test: INI Configuration Loading ===")
        
        # Create sample INI configuration
        ini_content = """
[General]
data_file_path = ./data/projects.json
auto_save_interval = 300
backup_enabled = true
backup_count = 5

[UI]
theme = dark
window_width = 800
window_height = 600
always_on_top = false
minimize_to_tray = true

[Performance]
max_projects = 1000
cache_enabled = true
cache_size_mb = 50
load_timeout = 30

[Export]
default_format = txt
include_timestamps = true
date_format = %Y-%m-%d
encoding = utf-8

[Logging]
level = INFO
file_path = ./logs/tick_tock.log
max_file_size_mb = 10
backup_count = 3
"""
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write(ini_content.strip())
        
        # Test configuration parsing
        config = configparser.ConfigParser()
        config.read(self.config_file)
        
        # Verify sections exist
        expected_sections = ['General', 'UI', 'Performance', 'Export', 'Logging']
        actual_sections = config.sections()
        
        for section in expected_sections:
            self.assertIn(section, actual_sections, f"Section '{section}' should exist")
        
        print(f"✓ INI file loaded successfully")
        print(f"✓ Sections found: {', '.join(actual_sections)}")
        
        # Test configuration value retrieval and type conversion
        config_tests = [
            {
                'section': 'General',
                'key': 'auto_save_interval',
                'expected_value': 300,
                'value_type': int,
                'description': 'Auto-save interval'
            },
            {
                'section': 'General',
                'key': 'backup_enabled',
                'expected_value': True,
                'value_type': bool,
                'description': 'Backup enabled flag'
            },
            {
                'section': 'UI',
                'key': 'theme',
                'expected_value': 'dark',
                'value_type': str,
                'description': 'UI theme'
            },
            {
                'section': 'UI',
                'key': 'window_width',
                'expected_value': 800,
                'value_type': int,
                'description': 'Window width'
            },
            {
                'section': 'Performance',
                'key': 'cache_size_mb',
                'expected_value': 50,
                'value_type': int,
                'description': 'Cache size'
            }
        ]
        
        for test in config_tests:
            section = test['section']
            key = test['key']
            expected = test['expected_value']
            value_type = test['value_type']
            
            # Get raw value
            raw_value = config.get(section, key)
            
            # Convert to expected type
            if value_type == bool:
                actual_value = config.getboolean(section, key)
            elif value_type == int:
                actual_value = config.getint(section, key)
            elif value_type == float:
                actual_value = config.getfloat(section, key)
            else:
                actual_value = raw_value
            
            self.assertEqual(actual_value, expected, 
                           f"{test['description']} should be {expected}")
            
            print(f"✓ {test['description']}: {actual_value} ({value_type.__name__})")
    
    def test_json_configuration_loading(self):
        """Test JSON-style configuration file loading"""
        print("\n=== Configuration Test: JSON Configuration Loading ===")
        
        # Create comprehensive JSON configuration
        json_config = {
            "application": {
                "name": "Tick Tock Widget",
                "version": "2.0.0",
                "debug_mode": False,
                "data_directory": "./data",
                "temp_directory": "./temp"
            },
            "database": {
                "file_path": "./data/projects.json",
                "backup_enabled": True,
                "backup_directory": "./backups",
                "backup_retention_days": 30,
                "auto_save_interval_seconds": 300,
                "compression_enabled": False
            },
            "user_interface": {
                "theme": {
                    "name": "dark",
                    "primary_color": "#2D2D2D",
                    "secondary_color": "#404040",
                    "accent_color": "#007ACC",
                    "text_color": "#FFFFFF"
                },
                "window": {
                    "default_width": 800,
                    "default_height": 600,
                    "resizable": True,
                    "always_on_top": False,
                    "remember_position": True
                },
                "features": {
                    "minimize_to_tray": True,
                    "show_notifications": True,
                    "auto_start_timer": False,
                    "confirm_actions": True
                }
            },
            "performance": {
                "max_projects": 1000,
                "max_time_records_per_project": 10000,
                "cache_enabled": True,
                "cache_size_mb": 50,
                "lazy_loading": True,
                "background_save": True
            },
            "export": {
                "formats": ["txt", "csv", "json", "xml"],
                "default_format": "txt",
                "include_metadata": True,
                "date_format": "%Y-%m-%d %H:%M:%S",
                "timezone": "local",
                "encoding": "utf-8"
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "file_path": "./logs/application.log",
                "max_file_size_mb": 10,
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "security": {
                "data_validation": True,
                "input_sanitization": True,
                "backup_encryption": False,
                "session_timeout_minutes": 60,
                "max_failed_attempts": 3
            }
        }
        
        with open(self.json_config_file, 'w', encoding='utf-8') as f:
            json.dump(json_config, f, indent=2)
        
        # Test JSON configuration loading
        with open(self.json_config_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        
        # Verify structure and values
        structure_tests = [
            {
                'path': ['application', 'name'],
                'expected': 'Tick Tock Widget',
                'description': 'Application name'
            },
            {
                'path': ['application', 'debug_mode'],
                'expected': False,
                'description': 'Debug mode flag'
            },
            {
                'path': ['user_interface', 'theme', 'name'],
                'expected': 'dark',
                'description': 'Theme name'
            },
            {
                'path': ['user_interface', 'window', 'default_width'],
                'expected': 800,
                'description': 'Window width'
            },
            {
                'path': ['performance', 'max_projects'],
                'expected': 1000,
                'description': 'Maximum projects'
            },
            {
                'path': ['export', 'formats'],
                'expected': ["txt", "csv", "json", "xml"],
                'description': 'Export formats'
            }
        ]
        
        for test in structure_tests:
            # Navigate to nested value
            current = loaded_config
            path_str = " -> ".join(test['path'])
            
            try:
                for key in test['path']:
                    current = current[key]
                
                self.assertEqual(current, test['expected'], 
                               f"{test['description']} should match expected value")
                
                print(f"✓ {test['description']}: {current}")
                
            except KeyError as e:
                self.fail(f"Configuration path {path_str} not found: {e}")
        
        # Test configuration validation
        print("\n--- Testing Configuration Validation ---")
        
        validation_tests = [
            {
                'check': lambda c: isinstance(c['application']['version'], str),
                'description': 'Version should be string'
            },
            {
                'check': lambda c: c['performance']['max_projects'] > 0,
                'description': 'Max projects should be positive'
            },
            {
                'check': lambda c: c['performance']['cache_size_mb'] > 0,
                'description': 'Cache size should be positive'
            },
            {
                'check': lambda c: c['logging']['level'] in ['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                'description': 'Log level should be valid'
            },
            {
                'check': lambda c: len(c['export']['formats']) > 0,
                'description': 'Should have at least one export format'
            }
        ]
        
        for test in validation_tests:
            try:
                result = test['check'](loaded_config)
                self.assertTrue(result, test['description'])
                print(f"✓ {test['description']}")
            except Exception as e:
                self.fail(f"Validation failed for '{test['description']}': {e}")
    
    def test_environment_based_configuration(self):
        """Test environment-specific configuration loading"""
        print("\n=== Configuration Test: Environment-Based Configuration ===")
        
        # Create environment configurations
        environments = {
            'development': {
                'debug_mode': True,
                'auto_save_interval': 60,
                'log_level': 'DEBUG',
                'data_file': './dev_data.json',
                'backup_enabled': False
            },
            'testing': {
                'debug_mode': False,
                'auto_save_interval': 30,
                'log_level': 'WARNING',
                'data_file': './test_data.json',
                'backup_enabled': False
            },
            'production': {
                'debug_mode': False,
                'auto_save_interval': 300,
                'log_level': 'ERROR',
                'data_file': './production_data.json',
                'backup_enabled': True
            }
        }
        
        for env_name, env_config in environments.items():
            config_file = Path(self.temp_dir) / f"config_{env_name}.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(env_config, f, indent=2)
            
            print(f"✓ Created {env_name} configuration")
        
        # Test environment-specific loading
        def load_environment_config(environment):
            """Load configuration for specific environment"""
            config_file = Path(self.temp_dir) / f"config_{environment}.json"
            
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration for {environment} not found")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Test each environment
        for env_name in environments.keys():
            config = load_environment_config(env_name)
            expected = environments[env_name]
            
            # Verify configuration matches environment
            for key, expected_value in expected.items():
                actual_value = config.get(key)
                self.assertEqual(actual_value, expected_value,
                               f"{env_name} config: {key} should be {expected_value}")
            
            print(f"✓ {env_name.capitalize()} config validated")
        
        # Test environment variable override
        print("\n--- Testing Environment Variable Override ---")
        
        with patch.dict(os.environ, {
            'TICK_TOCK_DEBUG': 'true',
            'TICK_TOCK_LOG_LEVEL': 'DEBUG',
            'TICK_TOCK_DATA_FILE': '/custom/path/data.json',
            'TICK_TOCK_AUTO_SAVE': '120'
        }):
            
            # Simulate environment variable parsing
            env_overrides = {
                'debug_mode': os.getenv('TICK_TOCK_DEBUG', 'false').lower() == 'true',
                'log_level': os.getenv('TICK_TOCK_LOG_LEVEL', 'INFO'),
                'data_file': os.getenv('TICK_TOCK_DATA_FILE', './default.json'),
                'auto_save_interval': int(os.getenv('TICK_TOCK_AUTO_SAVE', '300'))
            }
            
            # Verify environment overrides
            self.assertTrue(env_overrides['debug_mode'], 
                           "Debug mode should be enabled via environment")
            self.assertEqual(env_overrides['log_level'], 'DEBUG',
                           "Log level should be overridden via environment")
            self.assertEqual(env_overrides['data_file'], '/custom/path/data.json',
                           "Data file path should be overridden via environment")
            self.assertEqual(env_overrides['auto_save_interval'], 120,
                           "Auto-save interval should be overridden via environment")
            
            print("✓ Environment variable overrides working correctly")
            for key, value in env_overrides.items():
                print(f"   {key}: {value}")
    
    def test_configuration_validation_and_defaults(self):
        """Test configuration validation and default value fallback"""
        print("\n=== Configuration Test: Validation and Defaults ===")
        
        # Define configuration schema with defaults and validation
        config_schema = {
            'auto_save_interval': {
                'type': int,
                'default': 300,
                'min': 30,
                'max': 3600,
                'description': 'Auto-save interval in seconds'
            },
            'window_width': {
                'type': int,
                'default': 800,
                'min': 400,
                'max': 2560,
                'description': 'Window width in pixels'
            },
            'window_height': {
                'type': int,
                'default': 600,
                'min': 300,
                'max': 1440,
                'description': 'Window height in pixels'
            },
            'theme': {
                'type': str,
                'default': 'light',
                'allowed': ['light', 'dark', 'auto'],
                'description': 'UI theme'
            },
            'backup_enabled': {
                'type': bool,
                'default': True,
                'description': 'Enable automatic backups'
            },
            'max_projects': {
                'type': int,
                'default': 100,
                'min': 1,
                'max': 10000,
                'description': 'Maximum number of projects'
            }
        }
        
        def validate_config_value(key, value, schema):
            """Validate a configuration value against schema"""
            if key not in schema:
                return False, f"Unknown configuration key: {key}"
            
            spec = schema[key]
            expected_type = spec['type']
            
            # Type validation
            if not isinstance(value, expected_type):
                return False, f"{key}: Expected {expected_type.__name__}, got {type(value).__name__}"
            
            # Range validation for numeric types
            if expected_type in (int, float):
                if 'min' in spec and value < spec['min']:
                    return False, f"{key}: Value {value} below minimum {spec['min']}"
                if 'max' in spec and value > spec['max']:
                    return False, f"{key}: Value {value} above maximum {spec['max']}"
            
            # Allowed values validation
            if 'allowed' in spec and value not in spec['allowed']:
                return False, f"{key}: Value '{value}' not in allowed values {spec['allowed']}"
            
            return True, "Valid"
        
        # Test valid configurations
        print("\n--- Testing Valid Configurations ---")
        
        valid_configs = [
            {'auto_save_interval': 300, 'expected': True},
            {'window_width': 1024, 'expected': True},
            {'theme': 'dark', 'expected': True},
            {'backup_enabled': False, 'expected': True},
            {'max_projects': 500, 'expected': True}
        ]
        
        for test_config in valid_configs:
            for key, value in test_config.items():
                if key == 'expected':
                    continue
                
                is_valid, message = validate_config_value(key, value, config_schema)
                self.assertTrue(is_valid, f"Valid config should pass: {key}={value}")
                print(f"✓ {key}={value}: {message}")
        
        # Test invalid configurations
        print("\n--- Testing Invalid Configurations ---")
        
        invalid_configs = [
            {'auto_save_interval': 10, 'expected_error': 'below minimum'},  # Too low
            {'auto_save_interval': 5000, 'expected_error': 'above maximum'},  # Too high
            {'window_width': "800", 'expected_error': 'Expected int'},  # Wrong type
            {'theme': 'purple', 'expected_error': 'not in allowed values'},  # Invalid value
            {'backup_enabled': 'yes', 'expected_error': 'Expected bool'},  # Wrong type
            {'max_projects': 0, 'expected_error': 'below minimum'}  # Below minimum
        ]
        
        for test_config in invalid_configs:
            for key, value in test_config.items():
                if key == 'expected_error':
                    continue
                
                is_valid, message = validate_config_value(key, value, config_schema)
                expected_error = test_config['expected_error']
                
                self.assertFalse(is_valid, f"Invalid config should fail: {key}={value}")
                self.assertIn(expected_error, message, 
                             f"Error message should contain '{expected_error}'")
                print(f"✓ {key}={value}: Correctly rejected ({message})")
        
        # Test default value application
        print("\n--- Testing Default Value Application ---")
        
        def apply_defaults(config, schema):
            """Apply default values for missing configuration keys"""
            complete_config = config.copy()
            
            for key, spec in schema.items():
                if key not in complete_config:
                    complete_config[key] = spec['default']
                    print(f"✓ Applied default: {key}={spec['default']}")
            
            return complete_config
        
        # Test with partial configuration
        partial_config = {
            'theme': 'dark',
            'window_width': 1200
        }
        
        complete_config = apply_defaults(partial_config, config_schema)
        
        # Verify all schema keys are present
        for key in config_schema.keys():
            self.assertIn(key, complete_config, f"Default should be applied for {key}")
        
        # Verify existing values are preserved
        self.assertEqual(complete_config['theme'], 'dark', "Existing values should be preserved")
        self.assertEqual(complete_config['window_width'], 1200, "Existing values should be preserved")
        
        # Verify defaults are applied
        self.assertEqual(complete_config['auto_save_interval'], 300, "Default should be applied")
        self.assertEqual(complete_config['backup_enabled'], True, "Default should be applied")
        
        print(f"✓ Configuration completed with {len(complete_config)} values")
    
    def test_configuration_persistence_and_updates(self):
        """Test configuration saving and runtime updates"""
        print("\n=== Configuration Test: Persistence and Updates ===")
        
        # Initial configuration
        initial_config = {
            'application': {
                'name': 'Tick Tock Widget',
                'version': '1.0.0'
            },
            'settings': {
                'theme': 'light',
                'auto_save': True,
                'interval': 300
            }
        }
        
        config_file = Path(self.temp_dir) / "runtime_config.json"
        
        # Save initial configuration
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(initial_config, f, indent=2)
        
        print("✓ Initial configuration saved")
        
        # Simulate configuration updates
        def update_configuration(file_path, updates):
            """Update configuration with new values"""
            # Load current configuration
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Apply updates (supports nested updates)
            def deep_update(d, updates):
                for key, value in updates.items():
                    if isinstance(value, dict) and key in d and isinstance(d[key], dict):
                        deep_update(d[key], value)
                    else:
                        d[key] = value
            
            deep_update(config, updates)
            
            # Save updated configuration
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return config
        
        # Test configuration updates
        update_tests = [
            {
                'updates': {'settings': {'theme': 'dark'}},
                'description': 'Theme change'
            },
            {
                'updates': {'settings': {'interval': 600}},
                'description': 'Interval update'
            },
            {
                'updates': {'application': {'version': '1.1.0'}},
                'description': 'Version bump'
            },
            {
                'updates': {'settings': {'new_feature': True}},
                'description': 'New setting addition'
            }
        ]
        
        for test in update_tests:
            updated_config = update_configuration(config_file, test['updates'])
            
            # Verify updates were applied
            for key_path, expected_value in self._flatten_dict(test['updates']).items():
                actual_value = self._get_nested_value(updated_config, key_path.split('.'))
                self.assertEqual(actual_value, expected_value,
                               f"{test['description']}: {key_path} should be updated")
            
            print(f"✓ {test['description']}: Applied successfully")
        
        # Verify final configuration state
        with open(config_file, 'r', encoding='utf-8') as f:
            final_config = json.load(f)
        
        expected_final = {
            'theme': 'dark',
            'interval': 600,
            'auto_save': True,
            'new_feature': True
        }
        
        for key, expected_value in expected_final.items():
            actual_value = final_config['settings'][key]
            self.assertEqual(actual_value, expected_value,
                           f"Final config: {key} should be {expected_value}")
        
        print("✓ Configuration persistence verified")
        print(f"✓ Final theme: {final_config['settings']['theme']}")
        print(f"✓ Final interval: {final_config['settings']['interval']}")
        print(f"✓ New feature: {final_config['settings']['new_feature']}")
    
    def _flatten_dict(self, d, parent_key='', sep='.'):
        """Flatten nested dictionary for easier comparison"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _get_nested_value(self, d, keys):
        """Get value from nested dictionary using key path"""
        for key in keys:
            d = d[key]
        return d


if __name__ == '__main__':
    unittest.main(verbosity=2)
