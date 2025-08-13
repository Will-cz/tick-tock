#!/usr/bin/env python3
"""
Secure Configuration management for Tick-Tock Widget
Prevents users from modifying critical settings in built executables
"""

import os
import sys
import json
from pathlib import Path
from typing import Any, Optional, Dict

from .config import Environment, Config


class SecureConfig(Config):
    """Secure configuration manager that prevents user tampering with critical settings"""

    # Hardcoded critical settings for prototype builds
    PROTOTYPE_LOCKED_CONFIG: Dict[str, Any] = {
        "environment": Environment.PROTOTYPE.value,
        "backup_enabled": True,
        "backup_directory": "backups",  # Relative to user data directory
        "max_backups": 10,
        "debug_mode": False,
        "auto_save_interval": 300,
    }

    # Settings that users are allowed to modify (stored in user preferences)
    ALLOWED_USER_SETTINGS = {
        "ui_settings",  # UI states, tree expansion, etc.
    }

    def __init__(self, config_file: str = "config.json"):
        """Initialize secure configuration manager"""
        self.is_executable = getattr(sys, 'frozen', False)
        self.is_prototype_build = self._is_prototype_build()
        
        if self.is_executable and self.is_prototype_build:
            # For prototype executables, use secure mode
            self._init_secure_mode()
        else:
            # For development, use standard config
            super().__init__(config_file)

    def _is_prototype_build(self) -> bool:
        """Determine if this is a prototype build"""
        # Check environment variable set during build
        build_env = os.environ.get('TICK_TOCK_ENV', '').lower()
        if build_env == 'prototype':
            return True
            
        # Check for embedded prototype marker file in executable
        if self.is_executable:
            try:
                # In PyInstaller, check for the embedded prototype marker
                if hasattr(sys, '_MEIPASS'):
                    # Running from PyInstaller bundle
                    marker_file = Path(sys._MEIPASS) / "prototype_marker.txt"
                    if marker_file.exists():
                        return True
                else:
                    # Check relative to executable location
                    app_dir = Path(sys.executable).parent
                    marker_file = app_dir / "prototype_marker.txt"
                    if marker_file.exists():
                        return True
            except (OSError, AttributeError):
                pass
                
        return False

    def _init_secure_mode(self):
        """Initialize in secure mode for prototype builds"""
        # User data goes to proper OS-specific location
        self.user_data_root = self._get_user_data_directory()
        
        # User preferences file (only for allowed settings)
        self.user_prefs_file = self.user_data_root / "user_preferences.json"
        
        # Initialize parent but override config file path to prevent saving to executable directory
        super().__init__("dummy_config.json")  # This won't be used but satisfies the parent class
        
        # CRITICAL: Override the config_file path to prevent creation in executable directory
        self.config_file = Path("/dev/null/dummy_config.json")  # Invalid path to prevent file creation
        
        # Start with locked prototype configuration
        self.config = self.PROTOTYPE_LOCKED_CONFIG.copy()
        
        # Add default display settings
        self.config.update({
            "data_files": {
                "prototype": "tick_tock_projects_prototype.json"
            },
            "environment_display": self.DEFAULT_CONFIG["environment_display"]
        })
        
        # Load only allowed user preferences
        self._load_user_preferences()
        
        print("🔒 Secure configuration mode enabled for prototype build")
        print(f"📂 User data directory: {self.user_data_root}")
        print(f"🚫 Config file path disabled: {self.config_file}")

    def _load_user_preferences(self) -> None:
        """Load only allowed user preferences"""
        if not self.user_prefs_file.exists():
            return
            
        try:
            with open(self.user_prefs_file, 'r', encoding='utf-8') as f:
                user_prefs = json.load(f)
                
            # Only load allowed settings
            for key in self.ALLOWED_USER_SETTINGS:
                if key in user_prefs:
                    self.config[key] = user_prefs[key]
                    
        except (OSError, json.JSONDecodeError) as e:
            print(f"⚠️  Warning: Could not load user preferences: {e}")

    def save_config(self) -> None:
        """Save configuration - in secure mode, only save allowed user preferences"""
        if self.is_executable and self.is_prototype_build:
            # In secure mode, completely block config file creation
            self._save_user_preferences()
        else:
            # Development mode - use parent implementation
            super().save_config()

    def _save_user_preferences(self) -> None:
        """Save only allowed user preferences"""
        try:
            # Ensure user data directory exists
            self.user_data_root.mkdir(parents=True, exist_ok=True)
            
            # Extract only allowed settings
            user_prefs = {}
            for key in self.ALLOWED_USER_SETTINGS:
                if key in self.config:
                    user_prefs[key] = self.config[key]
            
            # Save to user preferences file
            with open(self.user_prefs_file, 'w', encoding='utf-8') as f:
                json.dump(user_prefs, f, indent=2, ensure_ascii=False)
                
        except (OSError, json.JSONDecodeError) as e:
            print(f"❌ Error saving user preferences: {e}")

    def set_environment(self, environment: Environment) -> None:
        """Set environment - blocked in secure mode"""
        if self.is_executable and self.is_prototype_build:
            print("🔒 Environment switching is disabled in prototype build")
            return
        
        # Development mode - allow environment switching
        super().set_environment(environment)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value - restricted in secure mode"""
        if self.is_executable and self.is_prototype_build:
            # Only allow setting of allowed user settings
            if any(key.startswith(allowed + ".") or key == allowed for allowed in self.ALLOWED_USER_SETTINGS):
                self.config[key] = value
            else:
                print(f"🔒 Setting '{key}' is protected in prototype build")
                return
        
        # Development mode - allow all settings
        super().set(key, value)

    def get_environment(self) -> Environment:
        """Get current environment - always prototype in secure mode"""
        if self.is_executable and self.is_prototype_build:
            return Environment.PROTOTYPE
        
        return super().get_environment()

    def is_backup_enabled(self) -> bool:
        """Check if backup is enabled - always True in secure mode"""
        if self.is_executable and self.is_prototype_build:
            return True
            
        return super().is_backup_enabled()

    def get_auto_save_interval(self) -> int:
        """Get auto-save interval - locked value in secure mode"""
        if self.is_executable and self.is_prototype_build:
            return self.PROTOTYPE_LOCKED_CONFIG["auto_save_interval"]
            
        return super().get_auto_save_interval()

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled - always False in secure mode"""
        if self.is_executable and self.is_prototype_build:
            return False
            
        return super().is_debug_mode()

    def get_data_file(self, environment: Optional[Environment] = None) -> str:
        """Get data file path - forced to prototype in secure mode"""
        if self.is_executable and self.is_prototype_build:
            # Always use prototype data file in user data directory
            return str(self.user_data_root / "tick_tock_projects_prototype.json")
            
        return super().get_data_file(environment)

    def get_backup_directory(self) -> Path:
        """Get backup directory path"""
        if self.is_executable and self.is_prototype_build:
            backup_dir = self.user_data_root / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            return backup_dir
            
        return super().get_backup_directory()


def get_secure_config() -> 'Config':
    """Get global secure configuration instance"""
    # For now, just return a new SecureConfig instance
    # In production, this would integrate with the main config system
    return SecureConfig()


def init_secure_config(config_file: str = "config.json") -> 'Config':
    """Initialize secure configuration with specific file"""
    return SecureConfig(config_file)
