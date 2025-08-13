# ⚠️ LEGACY PROTOTYPE BRANCH ⚠️

# Tick-Tock Widget - Legacy Prototype

> **IMPORTANT NOTICE**: This branch (`legacy-prototype`) contains **LEGACY PROTOTYPE CODE** only. The source code, builds, and all artifacts present in this branch are **outdated prototypes** and should **NOT** be used for production or current development.

[![Development Status](https://img.shields.io/badge/Status-Legacy%20Prototype-red?style=for-the-badge)](https://github.com/Will-cz/tick-tock)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-yellow?style=for-the-badge)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

## 🚨 Legacy Branch Warning

**This is a legacy prototype branch. All code and builds here are outdated.**

- ❌ **Do not use for production**
- ❌ **Do not use for current development**  
- ❌ **Builds may be unstable or contain bugs**
- ❌ **Code architecture may be incomplete**
- ⚠️ **Maintained for historical reference only**

For the current, maintained version of this project, please check the main development branches.

---

## About This Legacy Prototype

This legacy prototype was an early version of a comprehensive project time tracking widget application built with Python and Tkinter. It provided basic functionality for tracking work time across multiple projects and sub-activities.

### Legacy Features (Prototype Only)

- 🕐 **Basic Time Tracking**: Simple stopwatch functionality for projects
- 📊 **Primitive Project Management**: Basic project creation and editing
- 🎨 **Limited Theming**: Basic color theme cycling
- 📈 **Basic Reporting**: Simple monthly time reports
- 💾 **JSON Data Storage**: File-based project data persistence
- 🪟 **Windows Desktop Widget**: Minimizable desktop application
- 🔔 **System Tray Integration**: Windows system tray support with hide/show functionality

### Legacy Technical Stack

- **Language**: Python 3.8+
- **GUI Framework**: Tkinter (Python standard library)
- **Data Storage**: JSON files
- **Dependencies**: 
  - Core: None (uses only Python standard library)
  - System Tray: pystray, Pillow (optional, graceful degradation)
- **Platform**: Windows (primary), cross-platform compatible

## Repository Structure (Legacy)

```
├── 📁 src/                    # Legacy source code
│   ├── tick_tock.py          # Main entry point (legacy)
│   └── tick_tock_widget/     # Widget package (legacy)
├── 📁 prototype/             # Legacy prototype builds
│   └── TickTockWidget.exe    # Legacy executable (DO NOT USE)
├── 📁 development/           # Legacy development scripts
├── 📁 tests/                 # Legacy test suite
├── 📁 build/                 # Legacy build artifacts
├── 📁 user_data/             # Legacy user data files
└── 📁 scripts/               # Legacy build scripts
```

## Legacy Development Setup (Historical Reference)

> **Warning**: This setup is for historical reference only. Do not use for active development.

<details>
<summary>Legacy Setup Instructions (Click to expand)</summary>

### Prerequisites (Legacy)
- Python 3.8 or higher
- Windows OS (for full functionality)

### Installation (Legacy)
```bash
# Clone this legacy branch (NOT RECOMMENDED)
git clone -b legacy-prototype https://github.com/Will-cz/tick-tock.git
cd tick-tock

# Install legacy development dependencies
pip install -r requirements-dev.txt
```

### Running Legacy Prototype
```bash
# Development mode (legacy)
python development/run_development.py

# Direct execution (legacy)
python src/tick_tock.py
```

### Legacy Testing
```bash
# Run legacy test suite
python scripts/run_tests.py

# Or with pytest directly
pytest tests/
```

</details>

## Legacy Build Information

The legacy builds in this branch were created using:
- **PyInstaller**: For creating standalone executables
- **Custom build scripts**: Located in `scripts/` directory
- **Windows targeting**: Primary platform for legacy builds

> **⚠️ Security Warning**: Legacy builds may contain outdated dependencies or security vulnerabilities. Do not use in production environments.

## Migration Notice

If you're looking to continue development or use this application:

1. **Check main branches** for current, maintained code
2. **Do not base new work** on this legacy prototype
3. **Refer to current documentation** for up-to-date setup instructions
4. **Use current releases** for production use

## Legacy Architecture Overview

This prototype used a simple architecture:
- **Main Widget** (`TickTockWidget`): Core GUI application
- **Project Data Manager**: JSON-based data persistence
- **Minimized Widget**: System tray functionality
- **Theme System**: Basic color theme management
- **Reporting**: Simple time tracking reports

## Historical Context

This legacy prototype served as:
- ✅ **Proof of concept** for time tracking widget
- ✅ **Initial GUI design exploration**
- ✅ **Basic functionality validation**
- ✅ **Learning exercise** for Tkinter development

## License

This legacy prototype is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Final Reminder

**This is legacy prototype code. Do not use for production or current development.**

For current, maintained versions of this project, please visit the main repository branches or check for the latest releases.

---

*Legacy prototype preserved for historical reference - Will-cz © 2025*
