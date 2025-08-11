# Tick-Tock Widget v0.1.0 - API Specification

**Project**: Tick-Tock Widget v0.1.0  
**Phase**: 3 - Alpha Development (Next Branch)  
**Version**: v0.1.0  
**Date**: August 11, 2025  
**Status**: Internal API Specification - Planned for Phase 3  

---

## 🔌 Internal APIs and Data Contracts

### **API Architecture Overview**

The Tick-Tock Widget uses an **event-driven internal API architecture** with clear contracts between Model, View, and Controller layers. All communication happens through well-defined interfaces and events.

```
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER STRUCTURE                      │
├─────────────────────────────────────────────────────────────┤
│  PUBLIC APIS (External Interface)                          │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │  Main App API   │  │  System Tray    │                │
│  │  (Entry Points) │  │     API         │                │
│  └─────────────────┘  └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  INTERNAL APIS (Component Communication)                   │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Timer API     │  │   Project API   │                │
│  │                 │  │                 │                │
│  └─────────────────┘  └─────────────────┘                │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │    Data API     │  │    Event API    │                │
│  │                 │  │                 │                │
│  └─────────────────┘  └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE APIS (Low-level Services)                  │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │   File API      │  │   Config API    │                │
│  │                 │  │                 │                │
│  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Models and JSON Schemas

### **Project Data Model**

#### **Project Schema Definition**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Project Data Schema",
  "type": "object",
  "properties": {
    "projects": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/Project"
      }
    },
    "metadata": {
      "$ref": "#/definitions/Metadata"
    }
  },
  "required": ["projects", "metadata"],
  "definitions": {
    "Project": {
      "type": "object",
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
          "description": "UUID4 identifier"
        },
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Project display name"
        },
        "description": {
          "type": "string",
          "maxLength": 500,
          "description": "Optional project description"
        },
        "color": {
          "type": "string",
          "pattern": "^#[0-9A-Fa-f]{6}$",
          "description": "Hex color code"
        },
        "created_date": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 timestamp"
        },
        "is_active": {
          "type": "boolean",
          "description": "Whether project is available for selection"
        },
        "total_time_seconds": {
          "type": "integer",
          "minimum": 0,
          "description": "Total tracked time in seconds"
        }
      },
      "required": ["id", "name", "color", "created_date", "is_active", "total_time_seconds"]
    }
  }
}
```

#### **Project API Interface**
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Project:
    id: str
    name: str
    description: str
    color: str
    created_date: datetime
    is_active: bool
    total_time_seconds: int = 0

class ProjectAPI(ABC):
    """Internal API for project management operations."""
    
    @abstractmethod
    def create_project(self, name: str, description: str = "", color: str = "#4CAF50") -> Project:
        """Create a new project with generated ID."""
        pass
    
    @abstractmethod
    def get_project(self, project_id: str) -> Optional[Project]:
        """Retrieve a project by ID."""
        pass
    
    @abstractmethod
    def get_all_projects(self, active_only: bool = False) -> List[Project]:
        """Retrieve all projects, optionally filtering by active status."""
        pass
    
    @abstractmethod
    def update_project(self, project_id: str, updates: dict) -> bool:
        """Update project fields. Returns True if successful."""
        pass
    
    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """Soft delete a project (set is_active=False). Returns True if successful."""
        pass
    
    @abstractmethod
    def add_time_to_project(self, project_id: str, seconds: int) -> bool:
        """Add tracked time to project total. Returns True if successful."""
        pass
```

### **Time Entry Data Model**

#### **Time Entry Schema Definition**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Time Entry Data Schema",
  "type": "object",
  "properties": {
    "time_entries": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/TimeEntry"
      }
    },
    "active_session": {
      "anyOf": [
        {"$ref": "#/definitions/ActiveSession"},
        {"type": "null"}
      ]
    },
    "metadata": {
      "$ref": "#/definitions/Metadata"
    }
  },
  "required": ["time_entries", "active_session", "metadata"],
  "definitions": {
    "TimeEntry": {
      "type": "object",
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        },
        "project_id": {
          "type": "string",
          "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        },
        "start_time": {
          "type": "string",
          "format": "date-time"
        },
        "end_time": {
          "type": "string",
          "format": "date-time"
        },
        "duration_seconds": {
          "type": "integer",
          "minimum": 0
        },
        "description": {
          "type": "string",
          "maxLength": 500
        },
        "tags": {
          "type": "array",
          "items": {
            "type": "string",
            "maxLength": 50
          },
          "maxItems": 10
        }
      },
      "required": ["id", "project_id", "start_time", "end_time", "duration_seconds"]
    },
    "ActiveSession": {
      "type": "object",
      "properties": {
        "project_id": {
          "type": "string",
          "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        },
        "start_time": {
          "type": "string",
          "format": "date-time"
        },
        "last_save": {
          "type": "string",
          "format": "date-time"
        },
        "description": {
          "type": "string",
          "maxLength": 500
        }
      },
      "required": ["project_id", "start_time", "last_save"]
    }
  }
}
```

#### **Timer API Interface**
```python
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TimeEntry:
    id: str
    project_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    description: str = ""
    tags: List[str] = None

@dataclass
class ActiveSession:
    project_id: str
    start_time: datetime
    last_save: datetime
    description: str = ""

class TimerAPI(ABC):
    """Internal API for timer operations."""
    
    @abstractmethod
    def start_timer(self, project_id: str, description: str = "") -> bool:
        """Start timing for a project. Returns True if successful."""
        pass
    
    @abstractmethod
    def stop_timer(self) -> Optional[TimeEntry]:
        """Stop current timer and return completed time entry."""
        pass
    
    @abstractmethod
    def pause_timer(self) -> bool:
        """Pause current timer. Returns True if successful."""
        pass
    
    @abstractmethod
    def resume_timer(self) -> bool:
        """Resume paused timer. Returns True if successful."""
        pass
    
    @abstractmethod
    def get_current_duration(self) -> float:
        """Get current session duration in seconds."""
        pass
    
    @abstractmethod
    def get_active_session(self) -> Optional[ActiveSession]:
        """Get current active session details."""
        pass
    
    @abstractmethod
    def is_timer_running(self) -> bool:
        """Check if timer is currently running."""
        pass
    
    @abstractmethod
    def get_time_entries(self, project_id: Optional[str] = None, 
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[TimeEntry]:
        """Retrieve time entries with optional filtering."""
        pass
```

### **Configuration Data Model**

#### **Configuration Schema Definition**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Configuration Schema",
  "type": "object",
  "properties": {
    "ui": {
      "$ref": "#/definitions/UIConfig"
    },
    "timer": {
      "$ref": "#/definitions/TimerConfig"
    },
    "data": {
      "$ref": "#/definitions/DataConfig"
    },
    "system": {
      "$ref": "#/definitions/SystemConfig"
    },
    "metadata": {
      "$ref": "#/definitions/Metadata"
    }
  },
  "required": ["ui", "timer", "data", "system", "metadata"],
  "definitions": {
    "UIConfig": {
      "type": "object",
      "properties": {
        "theme": {
          "type": "string",
          "enum": ["light", "dark", "high_contrast"],
          "default": "light"
        },
        "always_on_top": {
          "type": "boolean",
          "default": false
        },
        "start_minimized": {
          "type": "boolean",
          "default": false
        },
        "show_seconds": {
          "type": "boolean",
          "default": true
        },
        "window_opacity": {
          "type": "number",
          "minimum": 0.1,
          "maximum": 1.0,
          "default": 1.0
        }
      }
    },
    "TimerConfig": {
      "type": "object",
      "properties": {
        "auto_save_interval": {
          "type": "integer",
          "minimum": 60,
          "maximum": 3600,
          "default": 300,
          "description": "Auto-save interval in seconds"
        },
        "idle_detection": {
          "type": "boolean",
          "default": false
        },
        "idle_threshold": {
          "type": "integer",
          "minimum": 60,
          "maximum": 1800,
          "default": 300,
          "description": "Idle threshold in seconds"
        },
        "round_to_minutes": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "DataConfig": {
      "type": "object",
      "properties": {
        "backup_enabled": {
          "type": "boolean",
          "default": true
        },
        "backup_frequency": {
          "type": "string",
          "enum": ["daily", "weekly", "monthly"],
          "default": "weekly"
        },
        "max_backup_files": {
          "type": "integer",
          "minimum": 1,
          "maximum": 50,
          "default": 5
        },
        "data_export_format": {
          "type": "string",
          "enum": ["json", "csv", "xlsx"],
          "default": "csv"
        }
      }
    },
    "SystemConfig": {
      "type": "object",
      "properties": {
        "start_with_system": {
          "type": "boolean",
          "default": false
        },
        "minimize_to_tray": {
          "type": "boolean",
          "default": true
        },
        "close_to_tray": {
          "type": "boolean",
          "default": false
        },
        "update_check_enabled": {
          "type": "boolean",
          "default": true
        }
      }
    }
  }
}
```

#### **Configuration API Interface**
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class UIConfig:
    theme: str = "light"
    always_on_top: bool = False
    start_minimized: bool = False
    show_seconds: bool = True
    window_opacity: float = 1.0

@dataclass
class TimerConfig:
    auto_save_interval: int = 300  # 5 minutes
    idle_detection: bool = False
    idle_threshold: int = 300  # 5 minutes
    round_to_minutes: bool = False

@dataclass
class DataConfig:
    backup_enabled: bool = True
    backup_frequency: str = "weekly"
    max_backup_files: int = 5
    data_export_format: str = "csv"

@dataclass
class SystemConfig:
    start_with_system: bool = False
    minimize_to_tray: bool = True
    close_to_tray: bool = False
    update_check_enabled: bool = True

class ConfigAPI(ABC):
    """Internal API for configuration management."""
    
    @abstractmethod
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration settings."""
        pass
    
    @abstractmethod
    def get_timer_config(self) -> TimerConfig:
        """Get timer configuration settings."""
        pass
    
    @abstractmethod
    def get_data_config(self) -> DataConfig:
        """Get data management configuration."""
        pass
    
    @abstractmethod
    def get_system_config(self) -> SystemConfig:
        """Get system integration configuration."""
        pass
    
    @abstractmethod
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """Update a configuration value. Returns True if successful."""
        pass
    
    @abstractmethod
    def reset_to_defaults(self, section: Optional[str] = None) -> bool:
        """Reset configuration to defaults. If section is None, reset all."""
        pass
```

---

## 🔄 Event System API

### **Event Types and Payloads**

#### **Event Type Definitions**
```python
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime

class EventType(Enum):
    # Timer Events
    TIMER_STARTED = "timer_started"
    TIMER_STOPPED = "timer_stopped"
    TIMER_PAUSED = "timer_paused"
    TIMER_RESUMED = "timer_resumed"
    TIMER_UPDATED = "timer_updated"
    
    # Project Events
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    PROJECT_SELECTED = "project_selected"
    
    # Data Events
    DATA_SAVED = "data_saved"
    DATA_LOADED = "data_loaded"
    DATA_ERROR = "data_error"
    
    # UI Events
    WINDOW_MINIMIZED = "window_minimized"
    WINDOW_RESTORED = "window_restored"
    THEME_CHANGED = "theme_changed"
    
    # System Events
    APP_STARTED = "app_started"
    APP_CLOSING = "app_closing"
    ERROR_OCCURRED = "error_occurred"
    
    # Sleep Detection Events
    SYSTEM_SLEEP_DETECTED = "system_sleep_detected"
    SYSTEM_WAKE_DETECTED = "system_wake_detected"

@dataclass
class Event:
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str
```

#### **Event Payload Schemas**

##### **Timer Event Payloads**
```python
# TIMER_STARTED
{
    "project_id": "uuid4-string",
    "project_name": "Project Name",
    "start_time": "2025-08-11T10:30:00Z"
}

# TIMER_STOPPED
{
    "project_id": "uuid4-string",
    "duration_seconds": 3600,
    "time_entry_id": "uuid4-string"
}

# TIMER_UPDATED
{
    "current_duration": 1234.56,
    "formatted_time": "20:34"
}

# TIMER_PAUSED/RESUMED
{
    "project_id": "uuid4-string",
    "duration_at_pause": 1800
}
```

##### **Project Event Payloads**
```python
# PROJECT_CREATED/UPDATED
{
    "project": {
        "id": "uuid4-string",
        "name": "Project Name",
        "description": "Description",
        "color": "#4CAF50",
        "is_active": True
    }
}

# PROJECT_DELETED
{
    "project_id": "uuid4-string",
    "project_name": "Deleted Project"
}

# PROJECT_SELECTED
{
    "project_id": "uuid4-string",
    "project_name": "Selected Project"
}
```

#### **Event Manager API**
```python
from abc import ABC, abstractmethod
from typing import Callable, List
from collections import defaultdict

class EventManager(ABC):
    """Central event management system."""
    
    @abstractmethod
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> str:
        """Subscribe to an event type. Returns subscription ID."""
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from an event. Returns True if successful."""
        pass
    
    @abstractmethod
    def publish(self, event_type: EventType, data: Dict[str, Any], source: str = "unknown") -> None:
        """Publish an event to all subscribers."""
        pass
    
    @abstractmethod
    def get_event_history(self, event_type: Optional[EventType] = None, 
                         limit: int = 100) -> List[Event]:
        """Get recent events, optionally filtered by type."""
        pass

class EventManagerImpl(EventManager):
    """Concrete implementation of event manager."""
    
    def __init__(self):
        self._subscribers = defaultdict(list)
        self._subscription_counter = 0
        self._event_history = []
        self._max_history = 1000
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> str:
        subscription_id = f"sub_{self._subscription_counter}"
        self._subscription_counter += 1
        
        self._subscribers[event_type].append({
            "id": subscription_id,
            "callback": callback
        })
        
        return subscription_id
    
    def publish(self, event_type: EventType, data: Dict[str, Any], source: str = "unknown") -> None:
        event = Event(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=data,
            source=source
        )
        
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify subscribers
        for subscriber in self._subscribers[event_type]:
            try:
                subscriber["callback"](event)
            except Exception as e:
                # Log error but don't crash
                print(f"Error in event callback: {e}")
```

---

## 💾 Data Access API

### **Data Manager Interface**

#### **Core Data Operations**
```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path

class DataAPI(ABC):
    """Internal API for data persistence operations."""
    
    @abstractmethod
    def initialize_storage(self, data_dir: Path) -> bool:
        """Initialize data storage directory and files."""
        pass
    
    @abstractmethod
    def save_projects(self, projects_data: Dict[str, Any]) -> bool:
        """Save projects data to storage."""
        pass
    
    @abstractmethod
    def load_projects(self) -> Optional[Dict[str, Any]]:
        """Load projects data from storage."""
        pass
    
    @abstractmethod
    def save_time_entries(self, time_data: Dict[str, Any]) -> bool:
        """Save time entries data to storage."""
        pass
    
    @abstractmethod
    def load_time_entries(self) -> Optional[Dict[str, Any]]:
        """Load time entries data from storage."""
        pass
    
    @abstractmethod
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """Save configuration data to storage."""
        pass
    
    @abstractmethod
    def load_config(self) -> Optional[Dict[str, Any]]:
        """Load configuration data from storage."""
        pass
    
    @abstractmethod
    def create_backup(self, backup_name: str) -> bool:
        """Create a backup of all data files."""
        pass
    
    @abstractmethod
    def restore_backup(self, backup_name: str) -> bool:
        """Restore data from a backup."""
        pass
    
    @abstractmethod
    def get_data_integrity_status(self) -> Dict[str, Any]:
        """Check data file integrity and return status report."""
        pass
```

#### **File Operations API**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

class FileAPI(ABC):
    """Low-level file operations API."""
    
    @abstractmethod
    def atomic_write(self, filepath: Path, data: Dict[str, Any]) -> bool:
        """Write data to file atomically with locking."""
        pass
    
    @abstractmethod
    def safe_read(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Read data from file with error handling."""
        pass
    
    @abstractmethod
    def acquire_lock(self, filepath: Path) -> bool:
        """Acquire exclusive lock on file."""
        pass
    
    @abstractmethod
    def release_lock(self, filepath: Path) -> bool:
        """Release lock on file."""
        pass
    
    @abstractmethod
    def is_file_locked(self, filepath: Path) -> bool:
        """Check if file is currently locked."""
        pass
    
    @abstractmethod
    def validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate data against JSON schema."""
        pass
```

---

## 🎨 UI Component APIs

### **Main Widget API**

#### **Widget Communication Interface**
```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable

class MainWidgetAPI(ABC):
    """API for main window component interactions."""
    
    @abstractmethod
    def update_timer_display(self, formatted_time: str) -> None:
        """Update the timer display with new time."""
        pass
    
    @abstractmethod
    def update_project_list(self, projects: List[Project]) -> None:
        """Update the project selection dropdown."""
        pass
    
    @abstractmethod
    def set_timer_state(self, is_running: bool, is_paused: bool = False) -> None:
        """Update UI to reflect timer state."""
        pass
    
    @abstractmethod
    def show_notification(self, message: str, notification_type: str = "info") -> None:
        """Display a notification to the user."""
        pass
    
    @abstractmethod
    def get_selected_project_id(self) -> Optional[str]:
        """Get the currently selected project ID."""
        pass
    
    @abstractmethod
    def set_selected_project(self, project_id: str) -> None:
        """Programmatically select a project."""
        pass
    
    @abstractmethod
    def apply_theme(self, theme_name: str) -> None:
        """Apply a theme to the UI."""
        pass
    
    @abstractmethod
    def minimize_to_tray(self) -> None:
        """Minimize the window to system tray."""
        pass
    
    @abstractmethod
    def restore_from_tray(self) -> None:
        """Restore window from system tray."""
        pass
```

### **System Tray API**

#### **Tray Integration Interface**
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable

class SystemTrayAPI(ABC):
    """API for system tray integration."""
    
    @abstractmethod
    def create_tray_icon(self, icon_path: str) -> bool:
        """Create system tray icon."""
        pass
    
    @abstractmethod
    def update_tray_icon(self, icon_path: str) -> None:
        """Update tray icon image."""
        pass
    
    @abstractmethod
    def update_tooltip(self, text: str) -> None:
        """Update tray icon tooltip."""
        pass
    
    @abstractmethod
    def create_context_menu(self, menu_items: List[Dict[str, Any]]) -> None:
        """Create right-click context menu."""
        pass
    
    @abstractmethod
    def show_balloon_notification(self, title: str, message: str) -> None:
        """Show balloon notification from tray."""
        pass
    
    @abstractmethod
    def set_tray_callback(self, event: str, callback: Callable) -> None:
        """Set callback for tray events (click, double-click, etc.)."""
        pass
    
    @abstractmethod
    def destroy_tray_icon(self) -> None:
        """Remove tray icon and cleanup."""
        pass
```

---

## 🔌 Plugin/Extension API (Future)

### **Extension Point Definitions**

#### **Plugin Interface (v0.2.0+)**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class PluginAPI(ABC):
    """Base interface for plugins/extensions."""
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """Return plugin metadata (name, version, description, etc.)."""
        pass
    
    @abstractmethod
    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Initialize plugin with app context."""
        pass
    
    @abstractmethod
    def on_timer_event(self, event: Event) -> None:
        """Handle timer-related events."""
        pass
    
    @abstractmethod
    def on_project_event(self, event: Event) -> None:
        """Handle project-related events."""
        pass
    
    @abstractmethod
    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return menu items to add to UI."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup plugin resources."""
        pass

class ReportingPlugin(PluginAPI):
    """Example plugin for custom reporting."""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "Advanced Reporting",
            "version": "1.0.0",
            "description": "Generate detailed time tracking reports",
            "author": "Plugin Author"
        }
    
    def get_menu_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "label": "Generate Report",
                "callback": self.generate_report,
                "icon": "report_icon.png"
            }
        ]
```

---

## 🧪 Testing API Integration

### **Test Fixtures and Mocking**

#### **Mock API Implementations**
```python
class MockTimerAPI(TimerAPI):
    """Mock implementation for testing."""
    
    def __init__(self):
        self.is_running = False
        self.current_session = None
        self.time_entries = []
    
    def start_timer(self, project_id: str, description: str = "") -> bool:
        if self.is_running:
            return False
        
        self.current_session = ActiveSession(
            project_id=project_id,
            start_time=datetime.utcnow(),
            last_save=datetime.utcnow(),
            description=description
        )
        self.is_running = True
        return True

class MockProjectAPI(ProjectAPI):
    """Mock implementation for testing."""
    
    def __init__(self):
        self.projects = []
        self.next_id = 1
    
    def create_project(self, name: str, description: str = "", color: str = "#4CAF50") -> Project:
        project = Project(
            id=f"test-{self.next_id}",
            name=name,
            description=description,
            color=color,
            created_date=datetime.utcnow(),
            is_active=True
        )
        self.projects.append(project)
        self.next_id += 1
        return project
```

#### **API Testing Utilities**
```python
class APITestHelper:
    """Utilities for API testing."""
    
    @staticmethod
    def create_test_project_data() -> Dict[str, Any]:
        return {
            "projects": [
                {
                    "id": "test-project-1",
                    "name": "Test Project",
                    "description": "Test project for unit tests",
                    "color": "#4CAF50",
                    "created_date": "2025-08-11T10:00:00Z",
                    "is_active": True,
                    "total_time_seconds": 0
                }
            ],
            "metadata": {
                "version": "1.0",
                "last_modified": "2025-08-11T10:00:00Z"
            }
        }
    
    @staticmethod
    def create_test_time_entry() -> Dict[str, Any]:
        return {
            "id": "test-entry-1",
            "project_id": "test-project-1",
            "start_time": "2025-08-11T10:00:00Z",
            "end_time": "2025-08-11T11:00:00Z",
            "duration_seconds": 3600,
            "description": "Test time entry",
            "tags": ["testing", "unit-test"]
        }
```

---

## 📊 API Usage Examples

### **Common Integration Patterns**

#### **Timer Management Integration**
```python
class TimerController:
    def __init__(self, timer_api: TimerAPI, project_api: ProjectAPI, 
                 event_manager: EventManager):
        self.timer_api = timer_api
        self.project_api = project_api
        self.event_manager = event_manager
        
        # Subscribe to relevant events
        self.event_manager.subscribe(EventType.TIMER_STARTED, self._on_timer_started)
        self.event_manager.subscribe(EventType.TIMER_STOPPED, self._on_timer_stopped)
    
    def start_timer_for_project(self, project_id: str) -> bool:
        # Validate project exists
        project = self.project_api.get_project(project_id)
        if not project or not project.is_active:
            return False
        
        # Start timer
        if self.timer_api.start_timer(project_id):
            self.event_manager.publish(
                EventType.TIMER_STARTED,
                {"project_id": project_id, "project_name": project.name}
            )
            return True
        return False
    
    def _on_timer_started(self, event: Event):
        # Update UI, log event, etc.
        pass
```

#### **Data Synchronization Pattern**
```python
class DataSynchronizer:
    def __init__(self, data_api: DataAPI, event_manager: EventManager):
        self.data_api = data_api
        self.event_manager = event_manager
        
        # Subscribe to data change events
        self.event_manager.subscribe(EventType.PROJECT_CREATED, self._sync_projects)
        self.event_manager.subscribe(EventType.TIMER_STOPPED, self._sync_time_entries)
    
    def _sync_projects(self, event: Event):
        # Auto-save when projects change
        projects_data = self._build_projects_data()
        if self.data_api.save_projects(projects_data):
            self.event_manager.publish(EventType.DATA_SAVED, {"type": "projects"})
```

---

## 🎯 API Implementation Priorities

### **Phase 1: Core APIs (Week 1-2)**
1. **Event Manager** - Central communication system
2. **Timer API** - Core timing functionality  
3. **Project API** - Basic project management
4. **Data API** - File persistence

### **Phase 2: UI Integration (Week 3-4)**
1. **Main Widget API** - UI component communication
2. **System Tray API** - Minimized state integration
3. **Configuration API** - Settings management

### **Phase 3: Advanced Features (Week 5-6)**
1. **Testing APIs** - Mock implementations and test utilities
2. **Plugin API Framework** - Extension point preparation
3. **Error Handling APIs** - Robust error management

---

*This API specification provides comprehensive internal interfaces enabling clean separation of concerns, testability, and future extensibility for Tick-Tock Widget v0.1.0.*
