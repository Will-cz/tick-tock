#!/usr/bin/env python3
"""
Development Launcher for Tick-Tock Widget
This script ensures the application runs in development mode
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main launcher function"""
    print()
    print("=" * 42)
    print("   TICK-TOCK WIDGET - DEVELOPMENT MODE")
    print("=" * 42)
    print()
    
    # Set environment to development
    os.environ["TICK_TOCK_ENVIRONMENT"] = "development"
    
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
    
    print("Starting Tick-Tock Widget in DEVELOPMENT mode...")
    print("Data will be saved to: tick_tock_projects_dev.json")
    print()
    
    # Set development environment
    os.environ["TICK_TOCK_ENV"] = "development"
    
    try:
        # Run the application with conda
        conda_path = "C:/Users/MWina/anaconda3/Scripts/conda.exe"
        conda_env = "C:/Users/MWina/anaconda3"
        
        # Build the command
        cmd = [
            conda_path,
            "run",
            "-p", conda_env,
            "--no-capture-output",
            "python",
            "src/tick_tock.py"
        ]
        
        # Run the application
        result = subprocess.run(cmd, capture_output=False, check=False)
        
        print()
        print("Tick-Tock Widget has been closed.")
        
        # Return the exit code
        return result.returncode
        
    except FileNotFoundError:
        print("ERROR: Conda not found at expected path.")
        print("Please check the conda installation path.")
        return 1
    except (subprocess.SubprocessError, OSError) as e:
        print(f"ERROR: Failed to start application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
