#!/usr/bin/env python3
"""
Script to convert PNG image to ICO format for Windows executable icon.
Creates multiple sizes optimized for Windows 10/11 with perfect quality.
"""

import os
from PIL import Image, ImageOps, ImageEnhance

def create_icon_from_png(png_path, ico_path):
    """
    Convert PNG image to ICO format with multiple sizes using optimal quality approach.
    
    Args:
        png_path (str): Path to the source PNG file
        ico_path (str): Path where the ICO file should be saved
    """
    # Open and ensure RGBA to preserve transparency
    with Image.open(png_path) as img:
        print(f"📏 Original image size: {img.width}x{img.height}")
        print(f"🎨 Original image mode: {img.mode}")
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            print("🔄 Converted to RGBA mode")
        
        # Make it perfectly square without distortion
        # Use the smaller dimension to ensure we don't lose any content
        min_dimension = min(img.width, img.height)
        
        # Use ImageOps.fit for high-quality center cropping to square
        img_square = ImageOps.fit(img, (min_dimension, min_dimension), method=Image.Resampling.LANCZOS)
        print(f"✂️  Cropped to square: {img_square.width}x{img_square.height}")
        
        # If the image is small, upscale it first for better quality downscaling
        # Following guidance: start from 1024x1024 for maximum quality
        target_size = max(1024, min_dimension)  # At least 1024px for optimal quality
        if img_square.width < target_size:
            img_square = img_square.resize((target_size, target_size), Image.Resampling.LANCZOS)
            print(f"⬆️  Upscaled to: {target_size}x{target_size} for optimal downscaling quality")
        
        # Enhance the source image slightly for better small-size results
        enhancer = ImageEnhance.Contrast(img_square)
        img_square = enhancer.enhance(1.1)  # Slight contrast boost
        
        enhancer = ImageEnhance.Sharpness(img_square)
        img_square = enhancer.enhance(1.1)  # Slight sharpening
        
        print("🎯 Applied contrast and sharpness enhancement")
        
        # Define optimal sizes for Windows 10/11 - these work perfectly across all zoom levels and DPI settings
        # This follows Microsoft's best practices for EXE embedding:
        # - 16×16: Classic small icons, file lists
        # - 24×24: Menus, some ribbon icons  
        # - 32×32: Default icons in Explorer list view
        # - 48×48: Default desktop shortcut size
        # - 64×64: Medium/large icons in Explorer
        # - 128×128: Very large icon view
        # - 256×256: High DPI scaling and future-proofing (CRITICAL for sharpness!)
        sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        print("📦 Creating ICO with Windows 10/11 optimal sizes:")
        print(f"   {', '.join(f'{w}x{h}' for w, h in sizes)}")
        print("💡 Note: Windows will use the 256×256 layer and downscale for crisp results!")
        
        # Use Pillow's built-in multi-size ICO creation - it handles quality automatically
        # The 256×256 layer is crucial - Windows 11 uses it for all downscaling
        img_square.save(ico_path, format="ICO", sizes=sizes)
        
        print(f"✅ High-quality icon created: {ico_path}")
        print(f"📋 Available sizes: {', '.join(f'{w}x{h}' for w, h in sizes)}")
        
        # Show final file info
        file_size = os.path.getsize(ico_path)
        print(f"📁 Icon file size: {file_size:,} bytes")
        
        return True

def main():
    print("🎨 High-Quality Icon Creator for Windows 10/11")
    print("=" * 55)
    
    # Define paths
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
    png_file = os.path.join(assets_dir, 'tick_tock_icon_source.png')
    ico_file = os.path.join(assets_dir, 'tick_tock_icon.ico')
    
    print(f"📂 Source PNG: {png_file}")
    print(f"📁 Target ICO: {ico_file}")
    print()
    
    # Check if PNG file exists
    if not os.path.exists(png_file):
        print(f"❌ Error: PNG file not found at {png_file}")
        return
    
    # Create the icon with optimal quality
    try:
        success = create_icon_from_png(png_file, ico_file)
        
        if success:
            print()
            print("🎉 SUCCESS!")
            print(f"📍 High-quality icon created at: {ico_file}")
            print("🚀 This icon is optimized for Windows 10/11 and will look crisp at all DPI settings!")
            print()
            print("🔍 How this ensures crisp quality:")
            print("  • 256×256 layer: Windows uses this for ALL downscaling (prevents blur)")
            print("  • Multiple sizes: Perfect rendering at every zoom level")
            print("  • High source res: Started from 1024×1024 for maximum detail")
            print("  • LANCZOS resampling: Preserves edge sharpness during downscaling")
            print()
            print("📱 Display contexts where this will look sharp:")
            print("  • Desktop shortcuts (48×48 logical, scaled from 256×256)")
            print("  • Windows Explorer at any view size")
            print("  • Taskbar icons (all DPI settings)")
            print("  • Alt+Tab thumbnails")
            print("  • Start menu tiles")
            print()
            print("Next steps:")
            print("1. ✅ Icon is already configured in tick_tock_widget.spec")
            print("2. 🔨 Run PyInstaller to build exe with embedded icon")
            print("3. 🖼️  Check Windows Explorer - icon should display clearly at all zoom levels")
        
    except Exception as e:
        print(f"❌ Error creating icon: {e}")
        print("💡 Try using a larger source PNG (512x512 or bigger) for best results")

if __name__ == "__main__":
    main()
