#!/usr/bin/env powershell
<#
.SYNOPSIS
Advanced Windows Icon Cache Cleaner for Tick-Tock Widget

.DESCRIPTION
This script performs a comprehensive icon cache clearing operation to ensure
that new or updated icons display correctly. Must be run as Administrator.

Based on Microsoft's recommended icon cache clearing procedures.
#>

# Require Administrator privileges
#Requires -RunAsAdministrator

function Clear-IconCacheComprehensive {
    Write-Host "Advanced Windows Icon Cache Cleaner" -ForegroundColor Cyan
    Write-Host "=" * 40 -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Step 1: Stopping Windows Explorer..." -ForegroundColor Yellow
    try {
        # Stop all explorer processes
        Get-Process -Name explorer -ErrorAction SilentlyContinue | Stop-Process -Force
        Start-Sleep -Seconds 3
        Write-Host "   SUCCESS: Windows Explorer stopped" -ForegroundColor Green
    }
    catch {
        Write-Host "   WARNING: Could not stop Explorer: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host "Step 2: Clearing icon cache with ie4uinit..." -ForegroundColor Yellow
    try {
        # Method 1: Clear icon cache with ie4uinit
        & ie4uinit.exe -ClearIconCache
        Write-Host "   SUCCESS: Icon cache cleared with ie4uinit" -ForegroundColor Green
    }
    catch {
        Write-Host "   WARNING: ie4uinit failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host "Step 3: Clearing thumbnail cache..." -ForegroundColor Yellow
    try {
        # Method 2: Clear thumbnail cache
        & ie4uinit.exe -show
        Write-Host "   SUCCESS: Thumbnail cache cleared" -ForegroundColor Green
    }
    catch {
        Write-Host "   WARNING: Thumbnail cache clearing failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host "Step 4: Deleting cache files manually..." -ForegroundColor Yellow
    try {
        # Method 3: Delete icon cache files from user profile
        $iconCachePath = "$env:LOCALAPPDATA\Microsoft\Windows\Explorer"
        if (Test-Path $iconCachePath) {
            Get-ChildItem $iconCachePath -Filter "iconcache*" -Force | Remove-Item -Force -ErrorAction SilentlyContinue
            Get-ChildItem $iconCachePath -Filter "thumbcache*" -Force | Remove-Item -Force -ErrorAction SilentlyContinue
            Write-Host "   SUCCESS: Cache files deleted" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "   WARNING: Manual cache deletion failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host "Step 5: Flushing system caches..." -ForegroundColor Yellow
    try {
        # Method 4: Flush system caches
        & rundll32.exe user32.dll,UpdatePerUserSystemParameters
        Write-Host "   SUCCESS: System caches flushed" -ForegroundColor Green
    }
    catch {
        Write-Host "   WARNING: System cache flush failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host "Step 6: Restarting Windows Explorer..." -ForegroundColor Yellow
    try {
        # Restart Windows Explorer
        Start-Sleep -Seconds 2
        Start-Process explorer.exe
        Start-Sleep -Seconds 3
        Write-Host "   SUCCESS: Windows Explorer restarted" -ForegroundColor Green
    }
    catch {
        Write-Host "   WARNING: Explorer restart failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Icon Cache Clearing Complete!" -ForegroundColor Green
    Write-Host "=" * 35 -ForegroundColor Green
    Write-Host ""
    Write-Host "What was done:" -ForegroundColor Cyan
    Write-Host "  - Stopped Windows Explorer" -ForegroundColor White
    Write-Host "  - Cleared icon cache with ie4uinit.exe" -ForegroundColor White
    Write-Host "  - Cleared thumbnail cache" -ForegroundColor White
    Write-Host "  - Deleted manual cache files" -ForegroundColor White
    Write-Host "  - Flushed system caches" -ForegroundColor White
    Write-Host "  - Restarted Windows Explorer" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Check your desktop shortcut icon quality" -ForegroundColor White
    Write-Host "  2. Try different desktop icon sizes (Right-click -> View)" -ForegroundColor White
    Write-Host "  3. If still blurry, log out and log back in" -ForegroundColor White
    Write-Host "  4. Verify your display scaling settings" -ForegroundColor White
}

# Check if running as Administrator
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "To run as Administrator:" -ForegroundColor Yellow
    Write-Host "1. Right-click on PowerShell" -ForegroundColor White
    Write-Host "2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "3. Navigate to the project folder" -ForegroundColor White
    Write-Host "4. Run: .\scripts\clear_icon_cache_admin.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use this command:" -ForegroundColor Cyan
    Write-Host "powershell -Command ""Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass -File scripts\clear_icon_cache_admin.ps1' -Verb RunAs""" -ForegroundColor Gray
    exit 1
}

# Main execution
Clear-IconCacheComprehensive
