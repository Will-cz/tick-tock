#!/usr/bin/env python3
"""
Build Script for Tick-Tock Widget Legacy Prototype Executable
This script creates a standalone .exe file for legacy prototype distribution
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_directories():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous build artifacts...")
    
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"   Removed {build_dir}")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"   Removed {dist_dir}")


def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable with PyInstaller...")
    
    # Set prototype environment for the build
    build_env = os.environ.copy()
    build_env["TICK_TOCK_ENV"] = "prototype"
    build_env["TICK_TOCK_ENVIRONMENT"] = "prototype"
    
    try:
        # Run PyInstaller with the virtual environment
        # First try using virtual environment python
        venv_python = Path("venv/Scripts/python.exe")
        
        if venv_python.exists():
            # Use virtual environment
            cmd = [str(venv_python), "-m", "PyInstaller", "--clean", "tick_tock_widget.spec"]
        else:
            # Fallback to system pyinstaller if venv not available
            cmd = ["pyinstaller", "--clean", "tick_tock_widget.spec"]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True, env=build_env)
        
        print("✅ Build completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Build failed with error:")
        print(f"   Return code: {e.returncode}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller not found. Please install it with: pip install pyinstaller")
        return False


def create_distribution_folder():
    """Create a clean distribution folder"""
    print("📦 Creating distribution folder...")
    
    dist_source = Path("dist/TickTockWidget.exe")
    prototype_dir = Path("prototype")
    
    if not dist_source.exists():
        print(f"❌ Executable not found at {dist_source}")
        return False
    
    # Create prototype directory (remove existing if present)
    if prototype_dir.exists():
        shutil.rmtree(prototype_dir)
        print(f"   Removed existing {prototype_dir}")
    prototype_dir.mkdir()
    print(f"   Created {prototype_dir}")
    
    # Copy executable
    shutil.copy2(dist_source, prototype_dir / "TickTockWidget.exe")
    print(f"   ✅ Copied TickTockWidget.exe")
    
    # Copy LICENSE file (required)
    license_path = Path("LICENSE")
    if license_path.exists():
        shutil.copy2(license_path, prototype_dir / "LICENSE")
        print(f"   ✅ Copied LICENSE")
    else:
        print(f"   ⚠️  LICENSE file not found")
    
    # Copy README.md file (optional)
    readme_path = Path("README.md")
    if readme_path.exists():
        shutil.copy2(readme_path, prototype_dir / "README.md")
        print(f"   ✅ Copied README.md")
    else:
        print(f"   ⚠️  README.md file not found (optional)")
    
    print(f"✅ Distribution created in {prototype_dir}/")
    return True


def main():
    """Main build process"""
    print()
    print("=" * 60)
    print("   TICK-TOCK WIDGET - LEGACY PROTOTYPE BUILD")
    print("=" * 60)
    print()
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent if script_dir.name == "scripts" else script_dir
    os.chdir(project_root)
    
    print(f"📂 Working directory: {Path.cwd()}")
    print()
    
    # Step 1: Clean previous builds
    clean_build_directories()
    print()
    
    # Step 2: Build executable
    if not build_executable():
        sys.exit(1)
    print()
    
    # Step 3: Create distribution
    if not create_distribution_folder():
        sys.exit(1)
    print()
    
    # Final information
    exe_path = Path("prototype/TickTockWidget.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("🎉 BUILD SUCCESSFUL!")
        print(f"📍 Executable location: {exe_path.absolute()}")
        print(f"📏 File size: {size_mb:.1f} MB")
        print()
        print("🚀 You can now distribute the legacy prototype executable!")
        print("   The 'prototype' folder contains everything needed.")
    else:
        print("❌ Build completed but executable not found in expected location")
        sys.exit(1)


if __name__ == "__main__":
    main()
