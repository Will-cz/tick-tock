Add-Type -AssemblyName System.Drawing

function Test-ExecutableIcon {
    param([string]$ExePath)
    
    if (-not (Test-Path $ExePath)) {
        Write-Host "File not found: $ExePath" -ForegroundColor Red
        return
    }
    
    try {
        $icon = [System.Drawing.Icon]::ExtractAssociatedIcon($ExePath)
        
        if ($icon) {
            Write-Host "Icon extracted successfully!" -ForegroundColor Green
            Write-Host "Icon size: $($icon.Width)x$($icon.Height) pixels" -ForegroundColor Cyan
            Write-Host "Icon appears to be properly embedded!" -ForegroundColor Green
        } else {
            Write-Host "No icon found in executable" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "Error extracting icon: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "Testing Icon Embedding" -ForegroundColor White
Write-Host "======================" -ForegroundColor White

Write-Host ""
Write-Host "Testing dist executable:" -ForegroundColor Yellow
Test-ExecutableIcon "dist\TickTockWidget.exe"

Write-Host ""
Write-Host "If icons are properly embedded, they should display in Windows Explorer!" -ForegroundColor Cyan
