#!/usr/bin/env python3
"""
Build Script for Tick-Tock Widget Production Executable
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
    
    try:
        # Run PyInstaller with the spec file
        # Use conda environment if available, otherwise try system Python
        conda_cmd = [
            "C:/Users/MWina/anaconda3/Scripts/conda.exe", 
            "run", "-p", "C:\\Users\\MWina\\anaconda3", 
            "--no-capture-output", 
            "pyinstaller", "--clean", "tick_tock_widget.spec"
        ]
        
        try:
            subprocess.run(conda_cmd, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to system pyinstaller if conda fails
            subprocess.run(
                ["pyinstaller", "--clean", "tick_tock_widget.spec"],
                check=True,
                capture_output=True,
                text=True
            )
        
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
    release_dir = Path("release")
    
    if not dist_source.exists():
        print(f"❌ Executable not found at {dist_source}")
        return False
    
    # Create release directory
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # Copy executable
    shutil.copy2(dist_source, release_dir / "TickTockWidget.exe")
    
    # Copy essential files
    essential_files = ["README.md", "LICENSE"]
    for file_name in essential_files:
        file_path = Path(file_name)
        if file_path.exists():
            shutil.copy2(file_path, release_dir / file_name)
    
    print(f"✅ Distribution created in {release_dir}/")
    return True


def main():
    """Main build process"""
    print()
    print("=" * 60)
    print("   TICK-TOCK WIDGET - PRODUCTION BUILD")
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
    exe_path = Path("release/TickTockWidget.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("🎉 BUILD SUCCESSFUL!")
        print(f"📍 Executable location: {exe_path.absolute()}")
        print(f"📏 File size: {size_mb:.1f} MB")
        print()
        print("🚀 You can now distribute the executable!")
        print("   The 'release' folder contains everything needed.")
    else:
        print("❌ Build completed but executable not found in expected location")
        sys.exit(1)


if __name__ == "__main__":
    main()
