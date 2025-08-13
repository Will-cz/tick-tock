# Icon Management Scripts

This folder contains all scripts related to creating, managing, and troubleshooting the Tick-Tock Widget application icon.

## 📁 Scripts Overview

### Core Icon Creation
- **`create_icon.py`** - Converts PNG source to high-quality ICO with multiple sizes
- **`analyze_icon.py`** - Comprehensive analysis of ICO files and executable embedding

### Icon Testing & Verification  
- **`test_icon.ps1`** - Quick PowerShell test for icon embedding verification

### Desktop Shortcut Management
- **`create_desktop_shortcut.ps1`** - Creates desktop shortcuts with proper icon handling

### Windows Icon Cache Management
- **`clear_icon_cache.ps1`** - Basic icon cache clearing (no admin required)
- **`clear_icon_cache_admin.ps1`** - Advanced cache clearing (requires Administrator)

## 🚀 Quick Usage

### Create Icon from Source
```cmd
python scripts/icon/create_icon.py
```

### Analyze Icon Quality
```cmd
python scripts/icon/analyze_icon.py
```

### Create Desktop Shortcut
```powershell
powershell -ExecutionPolicy Bypass -File scripts/icon/create_desktop_shortcut.ps1
```

### Clear Icon Cache (if shortcut appears blurry)
```powershell
# Basic clearing
powershell -File scripts/icon/clear_icon_cache.ps1

# Advanced clearing (as Administrator)
powershell -ExecutionPolicy Bypass -File scripts/icon/clear_icon_cache_admin.ps1
```

## 📋 File Dependencies

### Input Files
- `../../assets/tick_tock_icon_source.png` - Source 1024x1024 PNG image
- `../../tick_tock_widget.spec` - PyInstaller spec with icon configuration

### Output Files
- `../../assets/tick_tock_icon.ico` - Generated multi-size ICO file
- `../../dist/TickTockWidget.exe` - Executable with embedded icon

## 🔧 Technical Details

### Icon Specifications
- **Source Resolution**: 1024x1024 pixels
- **ICO Sizes**: 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256
- **Critical Layer**: 256x256 (Windows uses this for all downscaling)
- **Format**: 32-bit RGBA with alpha transparency
- **Quality**: LANCZOS resampling for optimal downscaling

### Windows Icon Behavior
- Windows 10/11 uses the 256x256 layer as source for all icon sizes
- High DPI displays (150%+ scaling) benefit from the large source layer
- Icon cache can cause old icons to persist until cleared
- Desktop shortcuts reference the executable's embedded icon

## 🛠️ Troubleshooting

### If Icons Appear Blurry
1. Right-click desktop → View → Large icons or Extra large icons
2. Run icon cache clearing scripts
3. Restart Windows Explorer via Task Manager
4. Log out and log back in for complete refresh

### If Scripts Don't Work
- Ensure you're running from the project root directory
- Check that source PNG file exists in `assets/tick_tock_icon_source.png`
- Verify Python virtual environment is activated
- For PowerShell scripts, check execution policy: `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser`

## 📖 Related Documentation
- `../../docs/ICON_QUALITY_SOLUTION.md` - Complete technical documentation
- `../../assets/README.md` - Asset files information
- `../../README.md` - Project overview

---
*All scripts in this folder work together to ensure the Tick-Tock Widget has crisp, high-quality icons across all Windows 10/11 configurations.*
