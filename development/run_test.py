#!/usr/bin/env python3
"""
Test Launcher for Tick-Tock Widget
This script ensures the application runs in test mode for testing purposes
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main launcher function"""
    print()
    print("=" * 42)
    print("   TICK-TOCK WIDGET - TEST MODE")
    print("=" * 42)
    print()
    
    # Set environment to test
    os.environ["TICK_TOCK_ENVIRONMENT"] = "test"
    
    # Navigate to the application directory (parent of development folder)
    script_dir = Path(__file__).parent
    app_dir = script_dir.parent
    os.chdir(str(app_dir))
    
    # Check if we're in the right directory
    launcher_path = app_dir / "src" / "tick_tock.py"
    if not launcher_path.exists():
        print("ERROR: src/tick_tock.py launcher not found.")
        print("Make sure this script is in the Tick-Tock development directory.")
        print(f"Current directory: {os.getcwd()}")
        input("Press Enter to continue...")
        sys.exit(1)
    
    print("Starting Tick-Tock Widget in TEST mode...")
    print("Data will be saved to: tests/fixtures/test_data.json")
    print("Window title: Tick-Tock Widget [TEST]")
    print("Test environment with yellow title color and isolated data storage.")
    print("Note: Test data file will be auto-created if it doesn't exist.")
    print()
    
    # Set test environment
    os.environ["TICK_TOCK_ENV"] = "test"
    
    try:
        # Run the application with virtual environment
        venv_python = app_dir / "venv" / "Scripts" / "python.exe"
        
        # Check if virtual environment exists
        if not venv_python.exists():
            print("ERROR: Virtual environment not found.")
            print("Please run 'python -m venv venv' in the project root directory.")
            return 1
        
        # Build the command
        cmd = [
            str(venv_python),
            "src/tick_tock.py"
        ]
        
        # Run the application
        result = subprocess.run(cmd, capture_output=False, check=False)
        
        print()
        print("Tick-Tock Widget TEST mode has been closed.")
        
        # Return the exit code
        return result.returncode
        
    except FileNotFoundError:
        print("ERROR: Python virtual environment not found.")
        print("Please ensure the virtual environment is properly set up.")
        return 1
    except (subprocess.SubprocessError, OSError) as e:
        print(f"ERROR: Failed to start application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
