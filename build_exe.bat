@echo off
echo.
echo ===============================================
echo   TICK-TOCK WIDGET - BUILD LEGACY PROTOTYPE
echo ===============================================
echo.

REM Set prototype environment for the build
set TICK_TOCK_ENV=prototype
set TICK_TOCK_ENVIRONMENT=prototype

cd /d "%~dp0"
venv\Scripts\python.exe -m PyInstaller --clean tick_tock_widget.spec

echo.
echo Verifying build in dist folder...
if exist dist\TickTockWidget.exe (
    echo   ✅ Executable built successfully
    for %%A in (dist\TickTockWidget.exe) do echo   📏 Size: %%~zA bytes
) else (
    echo   ❌ Build failed - executable not found
    goto :end
)

REM Copy LICENSE file to dist (required)
echo Copying LICENSE to dist...
if exist LICENSE (
    copy LICENSE dist\ /Y
    echo   ✅ LICENSE copied to dist
) else (
    echo   ⚠️  LICENSE file not found
)

REM Copy README.md file to dist (optional)
echo Copying README.md to dist...
if exist README.md (
    copy README.md dist\ /Y
    echo   ✅ README.md copied to dist
) else (
    echo   ⚠️  README.md file not found (optional)
)

REM Create antivirus notice in dist
echo Creating antivirus notice...
echo ANTIVIRUS NOTICE> dist\ANTIVIRUS_README.txt
echo ================>> dist\ANTIVIRUS_README.txt
echo.>> dist\ANTIVIRUS_README.txt
echo If your antivirus flags this executable, it's likely a false positive.>> dist\ANTIVIRUS_README.txt
echo PyInstaller-built applications are commonly flagged by antivirus software.>> dist\ANTIVIRUS_README.txt
echo.>> dist\ANTIVIRUS_README.txt
echo SAFE ACTIONS:>> dist\ANTIVIRUS_README.txt
echo 1. Add the 'dist' folder to antivirus exclusions>> dist\ANTIVIRUS_README.txt
echo 2. Verify with VirusTotal.com if concerned>> dist\ANTIVIRUS_README.txt
echo 3. Build from source code yourself>> dist\ANTIVIRUS_README.txt
echo.>> dist\ANTIVIRUS_README.txt
echo Source: https://github.com/Will-cz/tick-tock>> dist\ANTIVIRUS_README.txt
echo   ✅ Antivirus notice created

:end
echo.
echo =========================================
echo   BUILD COMPLETE! 
echo   Executable: dist\TickTockWidget.exe
echo   Ready for distribution from dist folder
echo =========================================
echo.
pause
