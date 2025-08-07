"""
Tests for environment management functionality
"""

import unittest
import tempfile
import json
import os
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# We need to properly isolate the config for testing
from tick_tock_widget.config import Config, Environment, reset_config, init_config
from tick_tock_widget.project_data import ProjectDataManager


class TestEnvironmentManagement(unittest.TestCase):
    """Test environment management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear any environment variables that might interfere
        env_vars_to_clear = ['TICK_TOCK_DATA_FILE', 'TICK_TOCK_ENV', 'TICK_TOCK_DEBUG']
        self.original_env = {}
        for var in env_vars_to_clear:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
        
        # Reset global config
        reset_config()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.json"
        self.dev_file = Path(self.temp_dir) / "test_dev.json"
        self.prod_file = Path(self.temp_dir) / "test_prod.json"
        
        # Create test configuration
        test_config = {
            "environment": "development",
            "data_files": {
                "development": str(self.dev_file),
                "production": str(self.prod_file),
                "test": str(Path(self.temp_dir) / "test_test.json")
            },
            "auto_save_interval": 30,
            "backup_enabled": True,
            "backup_directory": str(Path(self.temp_dir) / "backups"),
            "max_backups": 5,
            "debug_mode": True
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        # Initialize config with test file
        self.config = Config(str(self.config_file))
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value
        
        reset_config()
    
    def test_config_initialization(self):
        """Test configuration initialization"""
        self.assertEqual(self.config.get_environment(), Environment.DEVELOPMENT)
        self.assertEqual(self.config.get_data_file(), str(self.dev_file))
        self.assertTrue(self.config.is_backup_enabled())
        self.assertEqual(self.config.get_auto_save_interval(), 30)
    
    def test_environment_switching(self):
        """Test switching between environments"""
        # Start in development
        self.assertEqual(self.config.get_environment(), Environment.DEVELOPMENT)
        
        # Switch to production
        self.config.set_environment(Environment.PRODUCTION)
        self.assertEqual(self.config.get_environment(), Environment.PRODUCTION)
        self.assertEqual(self.config.get_data_file(), str(self.prod_file))
    
    def test_data_file_paths(self):
        """Test data file path retrieval"""
        dev_path = self.config.get_data_file(Environment.DEVELOPMENT)
        prod_path = self.config.get_data_file(Environment.PRODUCTION)
        
        self.assertEqual(dev_path, str(self.dev_file))
        self.assertEqual(prod_path, str(self.prod_file))
    
    def test_data_manager_with_config(self):
        """Test ProjectDataManager integration with configuration"""
        # Create test data in development file
        test_data = {
            "projects": [],
            "current_project_alias": None,
            "current_sub_activity_alias": None,
            "environment": "development"
        }
        
        with open(self.dev_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Create data manager using specific config file
        dm = ProjectDataManager(str(self.dev_file))
        self.assertEqual(dm.data_file, self.dev_file)
        
        # Load projects
        success = dm.load_projects()
        self.assertTrue(success)
    
    def test_data_manager_with_custom_file(self):
        """Test ProjectDataManager with custom data file"""
        custom_file = Path(self.temp_dir) / "custom.json"
        
        # Create test data
        test_data = {
            "projects": [],
            "current_project_alias": None,
            "current_sub_activity_alias": None
        }
        
        with open(custom_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Create data manager with custom file
        dm = ProjectDataManager(str(custom_file))
        self.assertEqual(dm.data_file, custom_file)
        
        # Load projects
        success = dm.load_projects()
        self.assertTrue(success)
    
    def test_environment_switching_in_data_manager(self):
        """Test environment switching in ProjectDataManager"""
        # Create test data for both environments
        dev_data = {
            "projects": [{"name": "Dev Project", "dz_number": "DEV-001", "alias": "dev", "sub_activities": [], "time_records": {}}],
            "current_project_alias": None,
            "current_sub_activity_alias": None,
            "environment": "development"
        }
        
        prod_data = {
            "projects": [{"name": "Prod Project", "dz_number": "PROD-001", "alias": "prod", "sub_activities": [], "time_records": {}}],
            "current_project_alias": None,
            "current_sub_activity_alias": None,
            "environment": "production"
        }
        
        with open(self.dev_file, 'w', encoding='utf-8') as f:
            json.dump(dev_data, f)
        
        with open(self.prod_file, 'w', encoding='utf-8') as f:
            json.dump(prod_data, f)
        
        # Create data manager starting with development
        dm = ProjectDataManager(str(self.dev_file))
        dm.config = self.config  # Set the test config
        dm.load_projects()
        
        # Should start with development project
        self.assertEqual(len(dm.projects), 1)
        self.assertEqual(dm.projects[0].name, "Dev Project")
        
        # Switch to production
        success = dm.switch_environment(Environment.PRODUCTION)
        self.assertTrue(success)
        self.assertEqual(dm.get_current_environment(), Environment.PRODUCTION)
        self.assertEqual(len(dm.projects), 1)
        self.assertEqual(dm.projects[0].name, "Prod Project")
    
    def test_data_migration(self):
        """Test data migration between environments"""
        # Create source data
        source_data = {
            "projects": [{"name": "Migration Test", "dz_number": "MIG-001", "alias": "mig", "sub_activities": [], "time_records": {}}],
            "current_project_alias": None,
            "current_sub_activity_alias": None
        }
        
        with open(self.dev_file, 'w', encoding='utf-8') as f:
            json.dump(source_data, f)
        
        # Migrate from development to production
        success = self.config.migrate_data_file(Environment.DEVELOPMENT, Environment.PRODUCTION)
        self.assertTrue(success)
        
        # Verify production file exists and has correct data
        self.assertTrue(self.prod_file.exists())
        
        with open(self.prod_file, 'r', encoding='utf-8') as f:
            migrated_data = json.load(f)
        
        self.assertEqual(len(migrated_data["projects"]), 1)
        self.assertEqual(migrated_data["projects"][0]["name"], "Migration Test")
    
    def test_backup_functionality(self):
        """Test backup creation"""
        # Create original data
        original_data = {
            "projects": [{"name": "Original", "dz_number": "ORIG-001", "alias": "orig", "sub_activities": [], "time_records": {}}],
            "current_project_alias": None,
            "current_sub_activity_alias": None
        }
        
        with open(self.prod_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f)
        
        # Create data manager and trigger backup during save
        dm = ProjectDataManager(str(self.prod_file))
        dm.config = self.config  # Set the test config
        dm.load_projects()
        
        # Add a project to trigger a save with backup
        dm.add_project("New Project", "NEW-001", "new")
        success = dm.save_projects(force=True)
        self.assertTrue(success)
        
        # Check if backup directory was created (backup only created if file existed before save)
        backup_dir = self.config.get_backup_directory()
        self.assertTrue(backup_dir.exists())
    
    def test_config_save_and_load(self):
        """Test configuration persistence"""
        # Modify configuration
        self.config.set_environment(Environment.PRODUCTION)
        self.config.set("debug_mode", False)
        
        # Save configuration
        self.config.save_config()
        
        # Create new config instance and verify settings
        new_config = Config(str(self.config_file))
        self.assertEqual(new_config.get_environment(), Environment.PRODUCTION)
        self.assertFalse(new_config.is_debug_mode())


if __name__ == '__main__':
    unittest.main()
