#!/usr/bin/env python3
"""
Tick-Tock Widget Launcher
Simple launcher for the project time tracking widget
"""

import sys
import os
from pathlib import Path

# Handle both development and executable scenarios
if getattr(sys, 'frozen', False):
    # Running as executable - PyInstaller sets up the path
    application_path = Path(sys.executable).parent
else:
    # Running in development - launcher is in src/, project root is parent
    application_path = Path(__file__).parent.parent
    src_dir = application_path / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))

# Ensure we're working from the project root directory
os.chdir(str(application_path))

# Debug: Print environment info
print(f"🔧 DEBUG: Current working directory: {os.getcwd()}")
print(f"🔧 DEBUG: Application path: {application_path}")
print(f"🔧 DEBUG: TICK_TOCK_ENV environment variable: {os.environ.get('TICK_TOCK_ENV', 'NOT SET')}")

try:
    from tick_tock_widget import main
except ImportError as e:
    print(f"Error importing tick_tock_widget: {e}")
    print(f"Python path: {sys.path}")
    print(f"Application path: {application_path}")
    print(f"Current working directory: {os.getcwd()}")
    # Try alternative import path
    try:
        sys.path.insert(0, str(application_path / "src"))
        from tick_tock_widget import main
        print("Successfully imported after path adjustment")
    except ImportError as e2:
        print(f"Failed alternative import: {e2}")
        print("Available modules in current directory:")
        try:
            for item in os.listdir('.'):
                print(f"  {item}")
        except OSError:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
