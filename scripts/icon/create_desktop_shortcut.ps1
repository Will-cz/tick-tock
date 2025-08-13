#!/usr/bin/env powershell
<#
.SYNOPSIS
Creates a desktop shortcut for Tick-Tock Widget with high-quality icon handling.

.DESCRIPTION
This script creates a desktop shortcut that properly references the executable's
embedded icon, ensuring Windows uses the 256x256 layer for crisp display.
Also includes icon cache clearing to force refresh.

Based on best practices for Windows 10/11 icon handling.
#>

param(
    [string]$ExePath = ".\dist\TickTockWidget.exe",
    [string]$ShortcutName = "Tick-Tock Widget",
    [switch]$ClearIconCache,
    [switch]$ForceRefresh
)

function Test-AdminRights {
    return ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Clear-WindowsIconCache {
    Write-Host "Clearing Windows icon cache..." -ForegroundColor Cyan
    
    try {
        # Method 1: Use ie4uinit.exe (most reliable)
        if (Get-Command "ie4uinit.exe" -ErrorAction SilentlyContinue) {
            & ie4uinit.exe -ClearIconCache
            Write-Host "   SUCCESS: Cleared icon cache with ie4uinit.exe" -ForegroundColor Green
        }
        
        # Method 2: Restart Windows Explorer (forces icon refresh)
        Write-Host "Restarting Windows Explorer..." -ForegroundColor Cyan
        $explorerProcess = Get-Process -Name explorer -ErrorAction SilentlyContinue
        if ($explorerProcess) {
            Stop-Process -Name explorer -Force
            Start-Sleep -Seconds 2
            Start-Process explorer.exe
            Write-Host "   SUCCESS: Windows Explorer restarted" -ForegroundColor Green
        }
        
        return $true
    }
    catch {
        Write-Host "   WARNING: Cache clearing failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   TIP: Try running as Administrator for full cache clearing" -ForegroundColor Yellow
        return $false
    }
}

function New-DesktopShortcut {
    param(
        [string]$TargetPath,
        [string]$ShortcutName
    )
    
    try {
        # Get desktop path
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = Join-Path $desktopPath "$ShortcutName.lnk"
        
        # Create WScript.Shell COM object
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        
        # Set shortcut properties
        $shortcut.TargetPath = (Resolve-Path $TargetPath).Path
        $shortcut.WorkingDirectory = Split-Path -Parent (Resolve-Path $TargetPath)
        
        # CRITICAL: Point IconLocation to the EXE itself (uses embedded icon)
        # Windows will automatically use the 256x256 layer and downscale
        $shortcut.IconLocation = (Resolve-Path $TargetPath).Path + ",0"
        
        # Optional: Set description
        $shortcut.Description = "Tick-Tock Widget - Project Time Tracker"
        
        # Save the shortcut
        $shortcut.Save()
        
        # Release COM object
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($shortcut) | Out-Null
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($shell) | Out-Null
        
        Write-Host "SUCCESS: Shortcut created: $shortcutPath" -ForegroundColor Green
        return $shortcutPath
    }
    catch {
        Write-Host "ERROR: Failed to create shortcut: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Main execution
Write-Host "Tick-Tock Widget Desktop Shortcut Creator" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host ""

# Validate executable path
$fullExePath = Resolve-Path $ExePath -ErrorAction SilentlyContinue
if (-not $fullExePath -or -not (Test-Path $fullExePath)) {
    Write-Host "ERROR: Executable not found: $ExePath" -ForegroundColor Red
    Write-Host "TIP: Make sure to build the executable first with build_exe.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "Executable: $fullExePath" -ForegroundColor White
Write-Host "Shortcut name: $ShortcutName" -ForegroundColor White
Write-Host ""

# Check if we should clear icon cache first
if ($ClearIconCache -or $ForceRefresh) {
    if (Test-AdminRights) {
        Clear-WindowsIconCache
    } else {
        Write-Host "WARNING: Icon cache clearing requires Administrator rights" -ForegroundColor Yellow
        Write-Host "TIP: Run as Administrator for best results, or restart Windows Explorer manually" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Create the shortcut
Write-Host "Creating desktop shortcut..." -ForegroundColor Cyan
$shortcutPath = New-DesktopShortcut -TargetPath $fullExePath -ShortcutName $ShortcutName

if ($shortcutPath) {
    Write-Host ""
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "Shortcut location: $shortcutPath" -ForegroundColor White
    Write-Host ""
    Write-Host "Icon Quality Expectations:" -ForegroundColor Cyan
    Write-Host "  - Desktop icons: Should be crisp using 256x256 layer" -ForegroundColor White
    Write-Host "  - High DPI displays: Automatically scales from 256x256" -ForegroundColor White
    Write-Host "  - Different zoom levels: Uses appropriate embedded size" -ForegroundColor White
    Write-Host ""
    Write-Host "If icon appears blurry:" -ForegroundColor Yellow
    Write-Host "  1. Right-click desktop -> View -> Large icons or Extra large icons" -ForegroundColor White
    Write-Host "  2. Run this script with -ClearIconCache -ForceRefresh as Administrator" -ForegroundColor White
    Write-Host "  3. Log out and log back in" -ForegroundColor White
    Write-Host "  4. Check Windows display scaling (150%+ benefits from 256x256)" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "ERROR: Shortcut creation failed" -ForegroundColor Red
    exit 1
}
