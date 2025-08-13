# Clear Windows Icon Cache - Run as Administrator
# This script clears the Windows icon cache to force refresh of executable icons

Write-Host "🔄 Windows Icon Cache Cleaner" -ForegroundColor Yellow
Write-Host "============================" -ForegroundColor Yellow
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "❌ This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Running as Administrator" -ForegroundColor Green
Write-Host ""

try {
    # Method 1: Stop Windows Explorer
    Write-Host "🛑 Stopping Windows Explorer..." -ForegroundColor Cyan
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    # Method 2: Clear icon cache using IE4UINIT
    Write-Host "🧹 Clearing icon cache..." -ForegroundColor Cyan
    Start-Process -FilePath "ie4uinit.exe" -ArgumentList "-show" -Wait -WindowStyle Hidden
    Start-Sleep -Seconds 2
    
    # Method 3: Clear thumbnail cache
    Write-Host "🗑️  Clearing thumbnail cache..." -ForegroundColor Cyan
    $cachePaths = @(
        "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\*.db",
        "$env:LOCALAPPDATA\IconCache.db",
        "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\thumbcache_*.db"
    )
    
    foreach ($path in $cachePaths) {
        Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    }
    
    # Method 4: Restart Windows Explorer
    Write-Host "🔄 Restarting Windows Explorer..." -ForegroundColor Cyan
    Start-Process -FilePath "explorer.exe"
    Start-Sleep -Seconds 3
    
    Write-Host ""
    Write-Host "✅ Icon cache cleared successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next steps:" -ForegroundColor Yellow
    Write-Host "1. Delete your existing desktop shortcut" -ForegroundColor White
    Write-Host "2. Create a new shortcut from dist\TickTockWidget.exe" -ForegroundColor White
    Write-Host "3. The new shortcut should show the high-quality icon" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 If still blurry, try:" -ForegroundColor Yellow
    Write-Host "- Sign out and sign back in to Windows" -ForegroundColor White
    Write-Host "- Restart your computer" -ForegroundColor White
    
} catch {
    Write-Host "❌ Error clearing cache: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
