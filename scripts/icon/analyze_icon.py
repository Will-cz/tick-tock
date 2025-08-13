#!/usr/bin/env python3
"""
Comprehensive icon analysis tool to verify ICO file quality and Windows executable embedding.
"""

import os
import sys
from PIL import Image
import struct

def analyze_ico_file(ico_path):
    """Analyze an ICO file to show all contained sizes and quality"""
    if not os.path.exists(ico_path):
        print(f"❌ ICO file not found: {ico_path}")
        return False
    
    try:
        # Read ICO file header
        with open(ico_path, 'rb') as f:
            # ICO file format: 
            # Bytes 0-1: Reserved (must be 0)
            # Bytes 2-3: Image type (1 = ICO)
            # Bytes 4-5: Number of images
            header = f.read(6)
            reserved, img_type, num_images = struct.unpack('<HHH', header)
            
            print(f"📁 ICO File: {ico_path}")
            print(f"📊 File size: {os.path.getsize(ico_path):,} bytes")
            print(f"🔢 Number of images: {num_images}")
            print(f"🎯 Image type: {img_type} (1=ICO, 2=CUR)")
            print()
            
            # Read directory entries
            for i in range(num_images):
                entry = f.read(16)  # Each directory entry is 16 bytes
                width, height, colors, reserved, planes, bpp, size, offset = struct.unpack('<BBBBHHII', entry)
                
                # Width/height of 0 means 256
                actual_width = 256 if width == 0 else width
                actual_height = 256 if height == 0 else height
                
                print(f"  📐 Image {i+1}: {actual_width}x{actual_height}, {bpp} bpp, {size:,} bytes")
        
        # Also try to load with PIL to verify
        print()
        print("🔍 PIL Verification:")
        with Image.open(ico_path) as img:
            print(f"  📏 Primary size: {img.width}x{img.height}")
            print(f"  🎨 Mode: {img.mode}")
            print(f"  📄 Format: {img.format}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing ICO: {e}")
        return False

def check_exe_icon_detailed(exe_path):
    """Check executable icon with detailed analysis"""
    if not os.path.exists(exe_path):
        print(f"❌ Executable not found: {exe_path}")
        return False
    
    try:
        # Try to extract icon using PIL
        print(f"🔍 Analyzing executable: {exe_path}")
        
        # Check if we can extract an icon
        import tempfile
        import subprocess
        
        # Try using PowerShell to extract icon information
        ps_script = f"""
Add-Type -AssemblyName System.Drawing
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon('{exe_path}')
if ($icon) {{
    Write-Host "Icon found: $($icon.Width)x$($icon.Height)"
    $icon.ToBitmap().Save('temp_icon.png', [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Host "Icon extracted to temp_icon.png"
}} else {{
    Write-Host "No icon found"
}}
"""
        
        with open('temp_ps_script.ps1', 'w', encoding='utf-8') as f:
            f.write(ps_script)
        
        result = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'temp_ps_script.ps1'], 
                              capture_output=True, text=True, cwd=os.path.dirname(exe_path) or '.')
        
        print(f"  📤 PowerShell output: {result.stdout.strip()}")
        
        # Clean up
        if os.path.exists('temp_ps_script.ps1'):
            os.remove('temp_ps_script.ps1')
        if os.path.exists('temp_icon.png'):
            with Image.open('temp_icon.png') as extracted_icon:
                print(f"  📐 Extracted icon size: {extracted_icon.width}x{extracted_icon.height}")
                print(f"  🎨 Extracted icon mode: {extracted_icon.mode}")
            os.remove('temp_icon.png')
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking executable icon: {e}")
        return False

def clear_icon_cache():
    """Provide instructions to clear Windows icon cache"""
    print("🔄 Windows Icon Cache Clear Instructions:")
    print("=" * 50)
    print("1. Open Task Manager (Ctrl+Shift+Esc)")
    print("2. Find 'Windows Explorer' in processes")
    print("3. Right-click → Restart")
    print("4. Or run this PowerShell command as Admin:")
    print("   ie4uinit.exe -show")
    print()
    print("Alternative method:")
    print("1. Open Command Prompt as Administrator")
    print("2. Run: ie4uinit.exe -ClearIconCache")
    print("3. Restart Windows Explorer")

def main():
    print("🔍 Comprehensive Icon Analysis Tool")
    print("=" * 40)
    print()
    
    # Analyze the ICO file
    ico_path = os.path.join('assets', 'tick_tock_icon.ico')
    print("📋 Step 1: Analyzing ICO file")
    analyze_ico_file(ico_path)
    print()
    
    # Analyze the executables
    print("📋 Step 2: Analyzing executables")
    exe_paths = ['dist/TickTockWidget.exe']
    for exe_path in exe_paths:
        if os.path.exists(exe_path):
            print(f"\n🔍 Checking: {exe_path}")
            check_exe_icon_detailed(exe_path)
        else:
            print(f"⚠️  Not found: {exe_path}")
    
    print()
    print("📋 Step 3: Icon cache recommendations")
    clear_icon_cache()

if __name__ == "__main__":
    main()
