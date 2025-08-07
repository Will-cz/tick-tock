#!/usr/bin/env python3
"""
Configuration management for Tick-Tock Widget
Handles environment-specific settings and data file management
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Any, Optional
from enum import Enum


class Environment(Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class Config:
    """Configuration manager for the application"""

    # Default configuration values
    DEFAULT_CONFIG: dict[str, Any] = {
        "environment": Environment.PRODUCTION.value,
        "data_files": {
            "development": "user_data/tick_tock_projects_dev.json",
            "production": "user_data/tick_tock_projects.json",
            "test": "user_data/tick_tock_projects_test.json"
        },
        "environment_display": {
            "development": {
                "window_title": "Tick-Tock Widget [DEV]",
                "title_color": "#00FF00",  # Green for development
                "border_color": "#004400"
            },
            "production": {
                "window_title": "Tick-Tock Widget",
                "title_color": "#FFFFFF",  # White for production
                "border_color": "#444444"
            },
            "test": {
                "window_title": "Tick-Tock Widget [TEST]",
                "title_color": "#FFFF00",  # Yellow for test
                "border_color": "#444400"
            }
        },
        "auto_save_interval": 30,
        "backup_enabled": True,
        "backup_directory": "user_data/backups",
        "max_backups": 10,
        "debug_mode": False
    }

    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager"""
        # Handle PyInstaller bundle path
        if getattr(sys, 'frozen', False):
            # Running as executable - config file is in the same directory as executable
            app_dir = Path(sys.executable).parent
            self.config_file: Path = app_dir / config_file
            # User data goes to AppData/Local on Windows, proper locations on other OS
            self.user_data_root = self._get_user_data_directory()
        else:
            # Running in development - config file is in the same directory as this module
            module_dir = Path(__file__).parent
            self.config_file = module_dir / config_file
            # In development, use project root for user data
            project_root = module_dir.parent.parent
            self.user_data_root = project_root

        self.config: dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self._load_config()

    def _get_user_data_directory(self) -> Path:
        """Get the appropriate user data directory based on the operating system"""
        import platform
        
        system = platform.system()
        if system == "Windows":
            # Use LOCALAPPDATA for Windows
            app_data = os.environ.get('LOCALAPPDATA')
            if app_data:
                return Path(app_data) / "TickTock"
            else:
                # Fallback to user home
                return Path.home() / "AppData" / "Local" / "TickTock"
        elif system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "TickTock"
        else:  # Linux and others
            # Follow XDG Base Directory Specification
            xdg_data_home = os.environ.get('XDG_DATA_HOME')
            if xdg_data_home:
                return Path(xdg_data_home) / "tick-tock"
            else:
                return Path.home() / ".local" / "share" / "tick-tock"

    def _load_config(self) -> None:
        """Load configuration from file or environment variables"""
        # First, try to load from config file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
            except (OSError, json.JSONDecodeError) as e:
                print(f"⚠️  Warning: Could not load config file {self.config_file}: {e}")

        # Override with environment variables if present
        env_mapping: dict[str, Optional[str]] = {
            "TICK_TOCK_ENV": "environment",
            "TICK_TOCK_DEBUG": "debug_mode",
            "TICK_TOCK_DATA_FILE": None,  # Special handling below
            "TICK_TOCK_AUTO_SAVE": "auto_save_interval"
        }

        for env_var, config_key in env_mapping.items():
            env_value: Optional[str] = os.environ.get(env_var)
            if env_value:
                if config_key == "debug_mode":
                    self.config[config_key] = env_value.lower() in ("true", "1", "yes")
                elif config_key == "auto_save_interval":
                    try:
                        self.config[config_key] = int(env_value)
                    except ValueError:
                        print(f"⚠️  Warning: Invalid auto_save_interval value: {env_value}")
                elif config_key:
                    self.config[config_key] = env_value.strip()

        # Special handling for data file override
        data_file_override = os.environ.get("TICK_TOCK_DATA_FILE")
        if data_file_override:
            # Override the data file for current environment
            current_env = self.get_environment()
            self.config["data_files"][current_env.value] = data_file_override

    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"💾 Configuration saved to {self.config_file}")
        except (OSError, json.JSONDecodeError) as e:
            print(f"❌ Error saving configuration: {e}")

    def get_environment(self) -> Environment:
        """Get current environment"""
        env_value = self.config.get("environment", Environment.DEVELOPMENT.value)
        env_str = str(env_value).strip() if env_value else Environment.DEVELOPMENT.value
        try:
            return Environment(env_str)
        except ValueError:
            print(f"⚠️  Warning: Invalid environment '{env_str}', using development")
            return Environment.DEVELOPMENT

    def set_environment(self, environment: Environment) -> None:
        """Set current environment"""
        self.config["environment"] = environment.value
        print(f"🔄 Environment set to: {environment.value}")

    def get_data_file(self, environment: Optional[Environment] = None) -> str:
        """Get data file path for specified environment (or current)"""
        if environment is None:
            environment = self.get_environment()

        relative_path = self.config["data_files"].get(
            environment.value,
            self.DEFAULT_CONFIG["data_files"][environment.value]
        )
        
        # Convert to absolute path based on user data root
        if getattr(sys, 'frozen', False):
            # Running as executable - use user data directory
            return str(self.user_data_root / relative_path.replace('user_data/', ''))
        else:
            # Running in development - use relative to project root
            return str(self.user_data_root / relative_path)

    def get_backup_directory(self) -> Path:
        """Get backup directory path"""
        relative_backup_dir = self.config.get("backup_directory", "user_data/backups")
        
        if getattr(sys, 'frozen', False):
            # Running as executable - use user data directory
            backup_dir = self.user_data_root / relative_backup_dir.replace('user_data/', '')
        else:
            # Running in development - use relative to project root
            backup_dir = self.user_data_root / relative_backup_dir
            
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def is_backup_enabled(self) -> bool:
        """Check if backup is enabled"""
        return self.config.get("backup_enabled", True)

    def get_max_backups(self) -> int:
        """Get maximum number of backups to keep"""
        return self.config.get("max_backups", 10)

    def get_auto_save_interval(self) -> int:
        """Get auto-save interval in seconds"""
        return self.config.get("auto_save_interval", 30)

    def get_window_title(self, environment: Optional[Environment] = None) -> str:
        """Get environment-specific window title"""
        if environment is None:
            environment = self.get_environment()

        display_config = self.config.get("environment_display", {})
        env_display = display_config.get(environment.value, {})

        return env_display.get("window_title", "Tick-Tock Widget")

    def get_title_color(self, environment: Optional[Environment] = None) -> str:
        """Get environment-specific title color"""
        if environment is None:
            environment = self.get_environment()

        display_config = self.config.get("environment_display", {})
        env_display = display_config.get(environment.value, {})

        return env_display.get("title_color", "#FFFFFF")

    def get_border_color(self, environment: Optional[Environment] = None) -> str:
        """Get environment-specific border color"""
        if environment is None:
            environment = self.get_environment()

        display_config = self.config.get("environment_display", {})
        env_display = display_config.get(environment.value, {})

        return env_display.get("border_color", "#444444")

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.config.get("debug_mode", False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value

    def migrate_data_file(self, source_env: Environment, target_env: Environment) -> bool:
        """Migrate data from one environment to another"""
        source_file = Path(self.get_data_file(source_env))
        target_file = Path(self.get_data_file(target_env))

        if not source_file.exists():
            print(f"❌ Source file {source_file} does not exist")
            return False

        try:
            # Create backup if target exists
            if target_file.exists() and self.is_backup_enabled():
                backup_dir = self.get_backup_directory()
                timestamp = Path(target_file).stat().st_mtime
                backup_name = f"{target_file.stem}_backup_{int(timestamp)}.json"
                backup_path = backup_dir / backup_name
                target_file.rename(backup_path)
                print(f"📦 Existing data backed up to {backup_path}")

            # Copy source to target
            shutil.copy2(source_file, target_file)
            print(f"✅ Data migrated from {source_env.value} to {target_env.value}")
            return True

        except (OSError, IOError) as e:
            print(f"❌ Error migrating data: {e}")
            return False

    def create_development_copy(self) -> bool:
        """Create a development copy from production data"""
        return self.migrate_data_file(Environment.PRODUCTION, Environment.DEVELOPMENT)

    def promote_to_production(self) -> bool:
        """Promote development data to production"""
        return self.migrate_data_file(Environment.DEVELOPMENT, Environment.PRODUCTION)


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def init_config(config_file: str = "config.json") -> Config:
    """Initialize configuration with specific file"""
    global _config_instance
    _config_instance = Config(config_file)
    return _config_instance


def reset_config() -> None:
    """Reset configuration instance (mainly for testing)"""
    global _config_instance
    _config_instance = None
