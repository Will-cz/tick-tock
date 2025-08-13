#!/usr/bin/env python3
"""
Build Script for Tick-Tock Widget Legacy Prototype Executable
This script creates a standalone .exe file for distribution
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
    
    print("🔒 Building with secure prototype configuration...")
    print("   - Environment locked to 'prototype'")
    print("   - Critical settings hardcoded")
    print("   - User config file creation disabled")
    
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


def prepare_distribution():
    """Prepare distribution files in the dist folder"""
    print("📦 Preparing distribution in dist folder...")
    
    dist_exe = Path("dist/TickTockWidget.exe")
    dist_dir = Path("dist")
    
    if not dist_exe.exists():
        print(f"❌ Executable not found at {dist_exe}")
        return False
    
    # Verify executable and show info
    exe_size = dist_exe.stat().st_size
    exe_size_mb = exe_size / (1024*1024)
    print(f"   ✅ TickTockWidget.exe built successfully")
    print(f"   📏 Executable size: {exe_size_mb:.1f} MB ({exe_size:,} bytes)")
    
    # Copy LICENSE file (required)
    license_path = Path("LICENSE")
    if license_path.exists():
        shutil.copy2(license_path, dist_dir / "LICENSE")
        print(f"   ✅ Copied LICENSE to dist")
    else:
        print(f"   ⚠️  LICENSE file not found")
    
    # Copy README.md file (optional)
    readme_path = Path("README.md")
    if readme_path.exists():
        shutil.copy2(readme_path, dist_dir / "README.md")
        print(f"   ✅ Copied README.md to dist")
    else:
        print(f"   ⚠️  README.md file not found (optional)")
    
    # Create antivirus notice
    av_notice_path = dist_dir / "ANTIVIRUS_README.txt"
    av_content = """ANTIVIRUS NOTICE
================

If your antivirus software flags this executable as suspicious, this is a 
common false positive with PyInstaller-built applications.

SAFE ACTIONS:
1. Add the 'dist' folder to your antivirus exclusions
2. Verify the executable with VirusTotal.com if concerned
3. Build from source code yourself using the provided scripts

This executable is built from the open-source Tick-Tock Widget project.
Source code is available at: https://github.com/Will-cz/tick-tock

The executable contains:
- Python runtime
- Tkinter GUI framework  
- Application code
- Application icon and resources

Built with PyInstaller - a legitimate Python packaging tool.
For questions, please refer to the project documentation.
"""
    
    with open(av_notice_path, 'w', encoding='utf-8') as f:
        f.write(av_content)
    print(f"   ✅ Created antivirus notice: {av_notice_path.name}")
    
    print(f"✅ Distribution ready in {dist_dir}/")
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
    
    # Step 3: Prepare distribution
    if not prepare_distribution():
        sys.exit(1)
    print()
    
    # Final information
    exe_path = Path("dist/TickTockWidget.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("🎉 BUILD SUCCESSFUL!")
        print(f"📍 Executable location: {exe_path.absolute()}")
        print(f"📏 File size: {size_mb:.1f} MB")
        print()
        print("🚀 Ready for distribution!")
        print("   All files are in the 'dist' folder:")
        print("   - TickTockWidget.exe (main executable)")
        print("   - LICENSE (required license file)")
        print("   - README.md (documentation)")
        print("   - ANTIVIRUS_README.txt (antivirus guidance)")
    else:
        print("❌ Build completed but executable not found in expected location")
        sys.exit(1)


if __name__ == "__main__":
    main()
