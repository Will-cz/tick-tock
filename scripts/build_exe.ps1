param(
    [string]$PythonExe = "python",
    [switch]$InstallBuildDeps,
    [switch]$SkipClean
)

$ErrorActionPreference = "Stop"

function Invoke-PythonCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args,
        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )

    & $PythonExe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (exit code $LASTEXITCODE)"
    }
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if ($PythonExe -eq "python" -and (Test-Path $venvPython)) {
    $PythonExe = $venvPython
    Write-Host "Using virtual environment Python: $PythonExe"
}

$pyprojectPath = Join-Path $ProjectRoot "pyproject.toml"
$iconPath = Join-Path $ProjectRoot "assets\tick_tock_icon.ico"
$alphaRuntimeHookPath = Join-Path $ProjectRoot "scripts\pyi_runtime_default_env_alpha.py"
$exeName = "TickTock"

if (-not (Test-Path $pyprojectPath)) {
    throw "pyproject.toml not found at $pyprojectPath"
}

if (-not (Test-Path $iconPath)) {
    throw "Icon file not found at $iconPath"
}

if ($InstallBuildDeps) {
    Write-Host "Installing build dependencies from requirements-build.txt..."
    Invoke-PythonCommand -Args @("-m", "pip", "install", "-r", "requirements-build.txt") -FailureMessage "Failed to install build dependencies"
}

Write-Host "Checking PyInstaller availability..."
Invoke-PythonCommand -Args @("-m", "PyInstaller", "--version") -FailureMessage "PyInstaller is not available in the selected Python environment"

$version = "dev"
$versionMatch = Select-String -Path $pyprojectPath -Pattern '^\s*version\s*=\s*"([^"]+)"\s*$' | Select-Object -First 1
if ($versionMatch -and $versionMatch.Matches.Count -gt 0) {
    $version = $versionMatch.Matches[0].Groups[1].Value
}

if (-not (Test-Path $alphaRuntimeHookPath)) {
    throw "Runtime hook for alpha default env not found at $alphaRuntimeHookPath"
}

$pyInstallerArgs = @(
    "--noconfirm",
    "--windowed",
    "--onefile",
    "--specpath", "build",
    "--name", $exeName,
    "--icon", $iconPath,
    "--add-data", "$iconPath;assets",
    "--hidden-import", "pystray._win32",
    "run.py"
)

Write-Host "Packaging build with runtime env hook (manual override in scripts/pyi_runtime_default_env_alpha.py)."
$pyInstallerArgs = @("--runtime-hook", $alphaRuntimeHookPath) + $pyInstallerArgs

if (-not $SkipClean) {
    $pyInstallerArgs = @("--clean") + $pyInstallerArgs
}

$distExe = Join-Path $ProjectRoot "dist\$exeName.exe"
if (Test-Path $distExe) {
    Remove-Item -Path $distExe -Force
}
$buildStartedAt = Get-Date

Write-Host "Building $exeName.exe with PyInstaller..."
Invoke-PythonCommand -Args (@("-m", "PyInstaller") + $pyInstallerArgs) -FailureMessage "PyInstaller build failed"

if (-not (Test-Path $distExe)) {
    throw "Build finished but executable not found at $distExe"
}

$distExeInfo = Get-Item $distExe
if ($distExeInfo.LastWriteTime -lt $buildStartedAt) {
    throw "Build produced a stale executable at $distExe (LastWriteTime: $($distExeInfo.LastWriteTime))"
}

$releasesDir = Join-Path $ProjectRoot "dist\releases"
New-Item -ItemType Directory -Path $releasesDir -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$versionedName = "$exeName-$version-win64-$timestamp.exe"
$versionedPath = Join-Path $releasesDir $versionedName
$releaseName = "$exeName-v$version-win64.exe"
$releasePath = Join-Path $releasesDir $releaseName
$latestPath = Join-Path $releasesDir "$exeName-latest.exe"

Copy-Item -Path $distExe -Destination $versionedPath -Force
Copy-Item -Path $distExe -Destination $releasePath -Force
Copy-Item -Path $distExe -Destination $latestPath -Force

Write-Host ""
Write-Host "Build complete."
Write-Host "Versioned EXE: $versionedPath"
Write-Host "Release EXE:   $releasePath"
Write-Host "Latest EXE:    $latestPath"
