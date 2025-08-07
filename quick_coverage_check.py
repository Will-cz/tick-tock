#!/usr/bin/env python3
"""
Quick coverage improvement script to identify immediate wins
"""

import subprocess
import sys
from pathlib import Path

def run_coverage():
    """Run coverage on working test files"""
    
    working_tests = [
        "tests/test_tick_tock_widget_core.py",
        "tests/test_monthly_report.py", 
        "tests/test_project_data_extended.py",
        "tests/test_config.py"
    ]
    
    print("🧪 Running coverage on working test files...")
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest"
    ] + working_tests + [
        "-v",
        "--cov=src/tick_tock_widget",
        "--cov-report=term-missing",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Coverage test timed out")
        return False
    except Exception as e:
        print(f"❌ Error running coverage: {e}")
        return False

if __name__ == "__main__":
    success = run_coverage()
    if success:
        print("✅ Coverage test completed")
    else:
        print("❌ Coverage test failed")
    sys.exit(0 if success else 1)
