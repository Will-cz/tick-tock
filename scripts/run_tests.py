#!/usr/bin/env python3
"""
Test runner script for Tick-Tock Widget
Provides convenient commands to run different test suites
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result"""
    if description:
        print(f"\n🔧 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests"""
    cmd = ["python", "-m", "pytest", "tests/unit/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=src/tick_tock_widget",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_html"
        ])
    
    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run integration tests"""
    cmd = ["python", "-m", "pytest", "tests/integration/", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running integration tests")


def run_e2e_tests(verbose=False):
    """Run end-to-end tests"""
    cmd = ["python", "-m", "pytest", "tests/e2e/", "-m", "e2e"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running end-to-end tests")


def run_gui_tests(verbose=False):
    """Run GUI tests (with mocked components)"""
    cmd = ["python", "-m", "pytest", "-m", "gui"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running GUI tests")


def run_all_tests(verbose=False, coverage=False):
    """Run all test suites"""
    cmd = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=src/tick_tock_widget",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_html",
            "--cov-report=xml:coverage.xml"
        ])
    
    return run_command(cmd, "Running all tests")


def run_fast_tests(verbose=False):
    """Run fast tests only (exclude slow tests)"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "not slow"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running fast tests only")


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test function"""
    cmd = ["python", "-m", "pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Running specific test: {test_path}")


def install_test_dependencies():
    """Install test dependencies"""
    cmd = ["python", "-m", "pip", "install", "-r", "requirements.txt"]
    return run_command(cmd, "Installing test dependencies")


def lint_code():
    """Run code linting"""
    success = True
    
    # Run flake8
    flake8_cmd = ["python", "-m", "flake8", "src/", "tests/"]
    if not run_command(flake8_cmd, "Running flake8 linter"):
        success = False
    
    # Run mypy (if available)
    try:
        mypy_cmd = ["python", "-m", "mypy", "src/tick_tock_widget/"]
        if not run_command(mypy_cmd, "Running mypy type checker"):
            print("Note: mypy errors found, but continuing...")
    except FileNotFoundError:
        print("mypy not available, skipping type checking")
    
    return success


def format_code():
    """Format code with black"""
    cmd = ["python", "-m", "black", "src/", "tests/"]
    return run_command(cmd, "Formatting code with black")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Tick-Tock Widget Test Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Generate coverage report")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test commands
    subparsers.add_parser("unit", help="Run unit tests")
    subparsers.add_parser("integration", help="Run integration tests")
    subparsers.add_parser("e2e", help="Run end-to-end tests")
    subparsers.add_parser("gui", help="Run GUI tests")
    subparsers.add_parser("all", help="Run all tests")
    subparsers.add_parser("fast", help="Run fast tests only")
    
    # Specific test command
    specific_parser = subparsers.add_parser("run", help="Run specific test")
    specific_parser.add_argument("test_path", help="Path to test file or test function")
    
    # Utility commands
    subparsers.add_parser("install", help="Install test dependencies")
    subparsers.add_parser("lint", help="Run code linting")
    subparsers.add_parser("format", help="Format code")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Ensure we're in the right directory (script is in scripts/ subdirectory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Change to project root directory
    import os
    os.chdir(project_root)
    
    if project_root.name != "tick-tock":
        print("Error: Cannot find project root directory")
        sys.exit(1)
    
    success = True
    
    if args.command == "unit":
        success = run_unit_tests(args.verbose, args.coverage)
    elif args.command == "integration":
        success = run_integration_tests(args.verbose)
    elif args.command == "e2e":
        success = run_e2e_tests(args.verbose)
    elif args.command == "gui":
        success = run_gui_tests(args.verbose)
    elif args.command == "all":
        success = run_all_tests(args.verbose, args.coverage)
    elif args.command == "fast":
        success = run_fast_tests(args.verbose)
    elif args.command == "run":
        success = run_specific_test(args.test_path, args.verbose)
    elif args.command == "install":
        success = install_test_dependencies()
    elif args.command == "lint":
        success = lint_code()
    elif args.command == "format":
        success = format_code()
    
    if success:
        print("\n✅ Command completed successfully!")
    else:
        print("\n❌ Command failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
