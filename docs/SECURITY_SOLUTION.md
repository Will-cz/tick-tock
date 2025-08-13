# Secure Configuration Solution

## Problem Analysis

The original Tick-Tock Widget had a critical security vulnerability where the application created a user-accessible `config.json` file that contained:

- **Environment settings** - Users could change from "prototype" to other environments
- **Critical settings** - Backup configuration, auto-save intervals, debug mode
- **System behavior** - All configuration was user-modifiable

This allowed users to:
1. Switch environments and access different data files
2. Disable backups and lose data protection
3. Modify critical application behavior
4. Potentially break the application by editing JSON incorrectly

## Solution Implementation

### 1. Secure Configuration Class (`secure_config.py`)

Created a `SecureConfig` class that extends the original `Config` class with security features:

**Key Features:**
- **Environment Detection**: Automatically detects if running as a prototype executable
- **Hardcoded Critical Settings**: Environment, backup settings, and other critical values are locked
- **Protected Setting Access**: Blocks modification of critical settings
- **User Preferences Only**: Only allows modification of safe UI settings
- **No Config File Creation**: Prevents creation of `config.json` in executable directory

**Critical Settings Locked in Prototype Build:**
```python
PROTOTYPE_LOCKED_CONFIG = {
    "environment": "prototype",
    "backup_enabled": True,
    "backup_directory": "backups",
    "max_backups": 10,
    "debug_mode": False,
    "auto_save_interval": 300,
}
```

**Allowed User Settings:**
```python
ALLOWED_USER_SETTINGS = {
    "ui_settings",  # UI states, tree expansion, etc.
}
```

### 2. Integration Points

**Main Application (`tick_tock_widget.py`)**:
- Detects prototype executable mode using `TICK_TOCK_ENV` environment variable
- Automatically uses `SecureConfig` when appropriate
- Falls back to regular config in development mode

**Build Process (`tick_tock_widget.spec`)**:
- **Removed** `config.json` inclusion from PyInstaller build
- Prevents users from accessing embedded configuration

**Build Script (`build_exe.py`)**:
- Sets `TICK_TOCK_ENV=prototype` environment variable during build
- Provides clear feedback about security measures

### 3. User Data Separation

**Secure Mode Behavior:**
- **User Data Directory**: `%LOCALAPPDATA%\TickTock\` (Windows)
- **User Preferences**: `user_preferences.json` (only UI settings)
- **Data Files**: Stored in user data directory (not executable directory)
- **Backups**: Always enabled, stored in user data directory

**File Locations:**
```
Executable Directory:
├── TickTockWidget.exe     # Protected, no config file
└── LICENSE

User Data Directory (%LOCALAPPDATA%\TickTock\):
├── tick_tock_projects_prototype.json
├── user_preferences.json  # Only UI settings
└── backups/
    ├── tick_tock_projects_prototype_backup_20250813_120000.json
    └── ...
```

## Security Benefits

### 1. Environment Protection
- **Cannot change environment**: Users cannot switch from prototype to other environments
- **Data isolation**: Prototype always uses its own data file
- **Behavior consistency**: Application always behaves as prototype

### 2. Critical Setting Protection
- **Backup always enabled**: Users cannot disable data protection
- **Auto-save locked**: Consistent data persistence behavior
- **Debug mode disabled**: No verbose output or debug features in production

### 3. User Access Control
- **No config file**: No user-accessible configuration file in executable directory
- **Protected directory**: User data stored in proper OS location
- **UI preferences only**: Users can only modify safe display preferences

### 4. Development Flexibility
- **Development mode unchanged**: Full configuration access during development
- **Testing support**: Secure config can be tested without affecting development
- **Backwards compatibility**: Existing development workflow unaffected

## Implementation Details

### Detection Logic
```python
def _is_prototype_build(self) -> bool:
    # Check environment variable set during build
    build_env = os.environ.get('TICK_TOCK_ENV', '').lower()
    if build_env == 'prototype':
        return True
    
    # Additional checks for executable context
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        return True
    
    return False
```

### Setting Protection
```python
def set(self, key: str, value: Any) -> None:
    if self.is_executable and self.is_prototype_build:
        # Only allow setting of allowed user settings
        if any(key.startswith(allowed + ".") or key == allowed 
               for allowed in self.ALLOWED_USER_SETTINGS):
            self.config[key] = value
        else:
            print(f"🔒 Setting '{key}' is protected in prototype build")
            return
```

### Environment Switching Protection
```python
def set_environment(self, environment: Environment) -> None:
    if self.is_executable and self.is_prototype_build:
        print("🔒 Environment switching is disabled in prototype build")
        return
    
    # Development mode - allow environment switching
    super().set_environment(environment)
```

## Testing

The solution includes comprehensive testing in `test_secure_config.py`:

1. **Development Mode Test**: Verifies normal operation in development
2. **Prototype Mode Test**: Verifies security restrictions in prototype build
3. **Environment Protection**: Confirms environment switching is blocked
4. **Setting Protection**: Confirms critical settings are protected
5. **UI Settings**: Confirms allowed settings can still be modified

## Usage

### Building Secure Executable
```bash
# Build with secure configuration
python scripts/build_exe.py

# The resulting executable will:
# - Run in secure prototype mode
# - Block environment switching
# - Protect critical settings
# - Store user data safely
```

### Development Mode
```python
# Regular development - full access
from tick_tock_widget.config import get_config
config = get_config()  # Full configuration access

# Secure testing
from tick_tock_widget.secure_config import SecureConfig
config = SecureConfig()  # Test secure behavior
```

## Future Enhancements

1. **Code Signing**: Add digital signatures to prevent executable tampering
2. **Encrypted Settings**: Encrypt sensitive configuration data
3. **Audit Logging**: Log configuration access attempts
4. **Remote Configuration**: Support for centralized configuration management
5. **License Validation**: Integrate with licensing system

## Migration Guide

### For Existing Users
- **Automatic Migration**: User data automatically moves to proper location
- **Settings Preserved**: UI preferences are preserved
- **Backup Protection**: Enhanced backup system protects user data

### For Developers
- **Development Unchanged**: Full configuration access in development mode
- **Testing Enhanced**: New secure config testing capabilities
- **Build Process**: Updated build script with security features

This solution provides robust protection against configuration tampering while maintaining development flexibility and user experience.
