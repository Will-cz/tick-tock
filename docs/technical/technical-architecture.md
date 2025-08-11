# Tick-Tock Widget v0.1.0 - Technical Architecture

**Project**: Tick-Tock Widget v0.1.0  
**Phase**: 3 - Alpha Development (Next Branch)  
**Version**: v0.1.0  
**Date**: August 11, 2025  
**Status**: Technical Specification - Planned for Phase 3  

---

## 🏗️ System Architecture Overview

### **Architecture Pattern: Model-View-Controller (MVC)**

```
┌─────────────────────────────────────────────────────────────┐
│                     TICK-TOCK WIDGET                        │
├─────────────────────────────────────────────────────────────┤
│  VIEW LAYER (Presentation)                                 │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Main Widget   │  │ Minimized Widget│                │
│  │   (tkinter)     │  │   (tkinter)     │                │
│  └─────────────────┘  └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  CONTROLLER LAYER (Business Logic)                         │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │ Timer Manager   │  │ Project Manager │                │
│  │                 │  │                 │                │
│  └─────────────────┘  └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  MODEL LAYER (Data)                                        │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │ Project Data    │  │ Time Data       │                │
│  │ (JSON)          │  │ (JSON)          │                │
│  └─────────────────┘  └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE LAYER                                      │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │ File Manager    │  │ System Tray     │                │
│  │ (atomic writes) │  │ (pystray)       │                │
│  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Technology Stack Specification

### **Core Technologies**

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Runtime** | Python | 3.9+ | Core language |
| **GUI Framework** | Tkinter | Built-in | User interface |
| **System Tray** | pystray | 0.19+ | Minimized state |
| **File Locking** | filelock | 3.12+ | Data integrity |
| **Packaging** | PyInstaller | 5.13+ | Distribution |

### **Development Dependencies**

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Testing** | pytest | 7.4+ | Unit testing |
| **Coverage** | pytest-cov | 4.1+ | Test coverage |
| **Linting** | pylint | 2.17+ | Code quality |
| **Formatting** | black | 23.7+ | Code formatting |

### **Python Version Requirements**
- **Minimum**: Python 3.9.0
- **Recommended**: Python 3.10+ or 3.11+
- **Maximum**: Python 3.12 (tested compatibility)

---

## 📁 Module Structure

### **Directory Layout**
```
src/
├── tick_tock/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Application entry point
│   ├── config.py                # Configuration management
│   │
│   ├── models/                  # Data layer
│   │   ├── __init__.py
│   │   ├── project_data.py      # Project data model
│   │   ├── time_data.py         # Time tracking data
│   │   └── config_data.py       # Configuration data
│   │
│   ├── controllers/             # Business logic
│   │   ├── __init__.py
│   │   ├── timer_manager.py     # Timer operations
│   │   ├── project_manager.py   # Project operations
│   │   └── data_manager.py      # Data persistence
│   │
│   ├── views/                   # Presentation layer
│   │   ├── __init__.py
│   │   ├── main_widget.py       # Main UI window
│   │   ├── minimized_widget.py  # System tray UI
│   │   └── theme_manager.py     # UI theming
│   │
│   └── utils/                   # Infrastructure
│       ├── __init__.py
│       ├── file_manager.py      # File operations
│       ├── system_tray.py       # System integration
│       └── error_handler.py     # Error management
```

### **Module Dependencies**

```
main.py
├── controllers/timer_manager.py
├── controllers/project_manager.py
├── views/main_widget.py
└── utils/system_tray.py

controllers/timer_manager.py
├── models/time_data.py
├── controllers/data_manager.py
└── utils/error_handler.py

controllers/project_manager.py
├── models/project_data.py
├── controllers/data_manager.py
└── utils/error_handler.py

views/main_widget.py
├── views/theme_manager.py
├── controllers/timer_manager.py
├── controllers/project_manager.py
└── utils/error_handler.py

controllers/data_manager.py
├── models/project_data.py
├── models/time_data.py
├── models/config_data.py
├── utils/file_manager.py
└── utils/error_handler.py
```

---

## 🔄 Data Flow Architecture

### **Core Data Flows**

#### **1. Timer Start/Stop Flow**
```
User Action (View) 
→ Timer Manager (Controller)
→ Time Data Model (Model)
→ Data Manager (Controller)
→ File Manager (Infrastructure)
→ JSON File (Storage)
```

#### **2. Project Selection Flow**
```
User Selection (View)
→ Project Manager (Controller)
→ Project Data Model (Model)
→ Timer Manager (Controller)
→ View Update (View)
```

#### **3. Auto-Save Flow**
```
Timer Tick (System)
→ Timer Manager (Controller)
→ Data Manager (Controller)
→ File Lock Check (Infrastructure)
→ Atomic Write (Infrastructure)
→ JSON File Update (Storage)
```

### **Event System Architecture**

#### **Observer Pattern Implementation**
```python
# Event Types
class EventType(Enum):
    TIMER_STARTED = "timer_started"
    TIMER_STOPPED = "timer_stopped"
    TIMER_PAUSED = "timer_paused"
    PROJECT_CHANGED = "project_changed"
    DATA_SAVED = "data_saved"
    ERROR_OCCURRED = "error_occurred"

# Event Manager
class EventManager:
    def __init__(self):
        self._listeners = defaultdict(list)
    
    def subscribe(self, event_type: EventType, callback: callable):
        self._listeners[event_type].append(callback)
    
    def publish(self, event_type: EventType, data: dict):
        for callback in self._listeners[event_type]:
            callback(data)
```

---

## 💾 Data Persistence Architecture

### **Storage Strategy: JSON with Atomic Writes**

#### **File Structure**
```
user_data/
├── projects.json           # Project definitions
├── time_entries.json       # Time tracking data
├── config.json            # User configuration
├── backup/                 # Automatic backups
│   ├── projects_backup.json
│   └── time_entries_backup.json
└── .lock                   # File locking
```

#### **Atomic Write Implementation**
```python
class AtomicFileWriter:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.temp_filepath = filepath.with_suffix('.tmp')
        self.lock_filepath = filepath.with_suffix('.lock')
    
    def write(self, data: dict):
        with FileLock(self.lock_filepath):
            # Write to temporary file
            with open(self.temp_filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic move
            self.temp_filepath.replace(self.filepath)
```

### **Data Models Schema**

#### **Project Data Schema**
```json
{
  "projects": [
    {
      "id": "uuid4-string",
      "name": "Project Name",
      "description": "Optional description",
      "color": "#HEX_COLOR",
      "created_date": "2025-08-11T10:30:00Z",
      "is_active": true,
      "total_time_seconds": 0
    }
  ],
  "metadata": {
    "version": "1.0",
    "last_modified": "2025-08-11T10:30:00Z"
  }
}
```

#### **Time Entry Schema**
```json
{
  "time_entries": [
    {
      "id": "uuid4-string",
      "project_id": "uuid4-string",
      "start_time": "2025-08-11T10:30:00Z",
      "end_time": "2025-08-11T11:30:00Z",
      "duration_seconds": 3600,
      "description": "Optional task description",
      "tags": ["tag1", "tag2"]
    }
  ],
  "active_session": {
    "project_id": "uuid4-string",
    "start_time": "2025-08-11T12:00:00Z",
    "last_save": "2025-08-11T12:05:00Z"
  },
  "metadata": {
    "version": "1.0",
    "last_modified": "2025-08-11T12:05:00Z"
  }
}
```

---

## ⏱️ Timer Architecture

### **High-Precision Timer System**

#### **System Time-Based Approach**
```python
class TimerManager:
    def __init__(self):
        self.start_time = None
        self.elapsed_time = 0
        self.is_running = False
        self.last_update = None
    
    def start_timer(self):
        self.start_time = time.time()
        self.is_running = True
        self.last_update = self.start_time
    
    def get_current_duration(self) -> float:
        if not self.is_running:
            return self.elapsed_time
        
        current_time = time.time()
        return self.elapsed_time + (current_time - self.start_time)
    
    def update_display(self):
        # Called every second for UI updates
        current_duration = self.get_current_duration()
        self.event_manager.publish(
            EventType.TIMER_UPDATED, 
            {"duration": current_duration}
        )
```

#### **Sleep Detection System**
```python
class SleepDetector:
    def __init__(self, threshold_seconds=30):
        self.threshold = threshold_seconds
        self.last_check = time.time()
    
    def check_for_sleep(self) -> bool:
        current_time = time.time()
        time_gap = current_time - self.last_check
        
        if time_gap > self.threshold:
            return True  # System likely slept
        
        self.last_check = current_time
        return False
```

---

## 🎨 UI Architecture

### **Tkinter Widget Hierarchy**

#### **Main Window Structure**
```
MainWindow (tk.Tk)
├── HeaderFrame (ttk.Frame)
│   ├── ProjectCombobox (ttk.Combobox)
│   └── OptionsButton (ttk.Button)
├── TimerFrame (ttk.Frame)
│   ├── TimeDisplay (ttk.Label)
│   ├── StartButton (ttk.Button)
│   ├── PauseButton (ttk.Button)
│   └── StopButton (ttk.Button)
├── StatusFrame (ttk.Frame)
│   ├── StatusLabel (ttk.Label)
│   └── ProgressBar (ttk.Progressbar)
└── FooterFrame (ttk.Frame)
    ├── MinimizeButton (ttk.Button)
    └── CloseButton (ttk.Button)
```

#### **Theme System Architecture**
```python
class ThemeManager:
    def __init__(self):
        self.current_theme = "light"
        self.themes = {
            "light": LightTheme(),
            "dark": DarkTheme(),
            "high_contrast": HighContrastTheme()
        }
    
    def apply_theme(self, theme_name: str):
        theme = self.themes.get(theme_name)
        if theme:
            theme.apply_to_root(self.root)
            self.current_theme = theme_name
```

### **System Tray Integration**
```python
class SystemTrayManager:
    def __init__(self, timer_manager, project_manager):
        self.timer_manager = timer_manager
        self.project_manager = project_manager
        
        # Create tray icon
        self.icon = pystray.Icon(
            "tick-tock",
            image=self.create_icon(),
            menu=self.create_menu()
        )
    
    def create_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Start Timer", self.start_timer),
            pystray.MenuItem("Stop Timer", self.stop_timer),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Window", self.show_window),
            pystray.MenuItem("Exit", self.exit_app)
        )
```

---

## 🔌 Integration Architecture

### **Cross-Platform Compatibility Layer**

#### **Platform Detection**
```python
class PlatformManager:
    @staticmethod
    def get_platform() -> str:
        return platform.system().lower()
    
    @staticmethod
    def get_user_data_dir() -> Path:
        system = PlatformManager.get_platform()
        
        if system == "windows":
            return Path.home() / "AppData" / "Local" / "TickTockWidget"
        elif system == "darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "TickTockWidget"
        else:  # Linux and others
            return Path.home() / ".local" / "share" / "tick-tock-widget"
```

#### **System Integration Features**
```python
class SystemIntegration:
    def __init__(self):
        self.platform = PlatformManager.get_platform()
    
    def enable_always_on_top(self, window):
        if self.platform == "windows":
            window.wm_attributes("-topmost", True)
        elif self.platform == "darwin":
            window.lift()
            window.attributes("-topmost", True)
        else:  # Linux
            window.wm_attributes("-topmost", True)
    
    def set_window_transparency(self, window, alpha=0.9):
        if self.supports_transparency():
            window.wm_attributes("-alpha", alpha)
    
    def supports_transparency(self) -> bool:
        # Platform-specific transparency support check
        return self.platform in ["windows", "darwin"]
```

---

## 📊 Performance Architecture

### **Memory Management Strategy**

#### **Resource Cleanup**
```python
class ResourceManager:
    def __init__(self):
        self._resources = []
        self._cleanup_callbacks = []
    
    def register_resource(self, resource, cleanup_callback):
        self._resources.append(resource)
        self._cleanup_callbacks.append(cleanup_callback)
    
    def cleanup_all(self):
        for callback in reversed(self._cleanup_callbacks):
            try:
                callback()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
```

#### **Memory Monitoring**
```python
class MemoryMonitor:
    def __init__(self, threshold_mb=50):
        self.threshold_bytes = threshold_mb * 1024 * 1024
        self.process = psutil.Process()
    
    def check_memory_usage(self) -> dict:
        memory_info = self.process.memory_info()
        return {
            "rss": memory_info.rss,
            "vms": memory_info.vms,
            "percent": self.process.memory_percent(),
            "threshold_exceeded": memory_info.rss > self.threshold_bytes
        }
```

### **Auto-Save Optimization**

#### **Intelligent Save Strategy**
```python
class AutoSaveManager:
    def __init__(self, save_interval=300):  # 5 minutes default
        self.save_interval = save_interval
        self.last_save = time.time()
        self.has_unsaved_changes = False
        self.force_save_threshold = 600  # 10 minutes max
    
    def should_save(self) -> bool:
        current_time = time.time()
        time_since_save = current_time - self.last_save
        
        # Force save if too much time has passed
        if time_since_save >= self.force_save_threshold:
            return True
        
        # Save if interval passed and there are changes
        if time_since_save >= self.save_interval and self.has_unsaved_changes:
            return True
        
        return False
```

---

## 🧪 Testing Architecture

### **Testing Strategy Integration**

#### **Testable Architecture Principles**
- **Dependency Injection**: All external dependencies injected
- **Interface Segregation**: Small, focused interfaces
- **Mock-Friendly Design**: External systems easily mockable
- **Event-Driven**: Testable through event simulation

#### **Test Fixtures Architecture**
```python
@pytest.fixture
def timer_manager():
    return TimerManager(
        data_manager=MockDataManager(),
        event_manager=MockEventManager()
    )

@pytest.fixture
def test_data_dir(tmp_path):
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir
```

---

## 🔒 Security Architecture

### **Data Protection Strategy**

#### **File System Security**
```python
class SecureFileManager:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self._ensure_secure_permissions()
    
    def _ensure_secure_permissions(self):
        # Set directory permissions (owner read/write only)
        if platform.system() != "Windows":
            os.chmod(self.base_path, 0o700)
    
    def secure_write(self, filename: str, data: dict):
        filepath = self.base_path / filename
        
        # Validate path is within base directory
        if not self._is_safe_path(filepath):
            raise SecurityError("Path traversal attempt detected")
        
        # Write with secure permissions
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Set file permissions (owner read/write only)
        if platform.system() != "Windows":
            os.chmod(filepath, 0o600)
```

---

## 🚀 Build and Deployment Pipeline

### **Development Environment Setup**

#### **Requirements Management**
```
# requirements.txt (Production)
filelock>=3.12.0
pystray>=0.19.0
Pillow>=9.5.0

# requirements-dev.txt (Development)
pytest>=7.4.0
pytest-cov>=4.1.0
pylint>=2.17.0
black>=23.7.0
mypy>=1.5.0

# requirements-build.txt (Packaging)
PyInstaller>=5.13.0
setuptools>=68.0.0
wheel>=0.41.0
```

#### **PyInstaller Specification**
```python
# tick_tock_widget.spec
a = Analysis(
    ['src/tick_tock/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/tick_tock/assets', 'assets'),
        ('src/tick_tock/themes', 'themes')
    ],
    hiddenimports=['pystray._win32', 'PIL._tkinter_finder'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)
```

---

## 📈 Monitoring and Observability

### **Application Monitoring**

#### **Health Check System**
```python
class HealthChecker:
    def __init__(self):
        self.checks = {
            "timer_accuracy": self._check_timer_accuracy,
            "file_access": self._check_file_access,
            "memory_usage": self._check_memory_usage,
            "gui_responsiveness": self._check_gui_responsiveness
        }
    
    def run_health_check(self) -> dict:
        results = {}
        for check_name, check_func in self.checks.items():
            try:
                results[check_name] = check_func()
            except Exception as e:
                results[check_name] = {"status": "error", "error": str(e)}
        return results
```

#### **Error Tracking**
```python
class ErrorTracker:
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.error_counts = defaultdict(int)
    
    def log_error(self, error: Exception, context: dict = None):
        error_data = {
            "timestamp": time.time(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        
        # Log to file
        with open(self.log_file, 'a') as f:
            json.dump(error_data, f)
            f.write('\n')
        
        # Track error frequency
        self.error_counts[type(error).__name__] += 1
```

---

## 🎯 Implementation Priorities

### **Phase 1: Core Foundation (Week 1-2)**
1. **Basic module structure and entry point**
2. **Timer manager with system time accuracy**
3. **JSON data persistence with atomic writes**
4. **Basic Tkinter UI framework**

### **Phase 2: Core Features (Week 3-4)**
1. **Project management functionality**
2. **System tray integration**
3. **Auto-save system implementation**
4. **Error handling and logging**

### **Phase 3: Integration & Polish (Week 5-6)**
1. **Cross-platform compatibility testing**
2. **Performance optimization**
3. **Theme system implementation**
4. **Build pipeline and packaging**

---

*This technical architecture provides the detailed implementation blueprint for Tick-Tock Widget v0.1.0, ensuring a robust, maintainable, and scalable foundation for development.*
