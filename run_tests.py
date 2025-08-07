#!/usr/bin/env python3
"""Quick test runner to check coverage progress."""

import subprocess
import sys
import os

# Change to project directory
project_dir = r"d:\SynologyDrive\mark_home\070 - Home Coding\playground\python\tick-tock"
os.chdir(project_dir)

print("🔍 Running TickTockWidget Core Tests...")

try:
    # Run our working tests
    result = subprocess.run([
        "C:\\Users\\MWina\\anaconda3\\Scripts\\activate.bat", "base", "&&",
        "python", "tests/test_tick_tock_widget_core.py"
    ], shell=True, capture_output=True, text=True, timeout=30)
    
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")  
    print(result.stderr)
    print("Return code:", result.returncode)
    
except subprocess.TimeoutExpired:
    print("⏰ Test execution timed out")
except Exception as e:
    print(f"❌ Error running tests: {e}")

print("\n✅ Test runner completed")
