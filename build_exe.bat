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
echo Creating prototype folder...
if not exist prototype mkdir prototype

REM Copy executable
echo Copying TickTockWidget.exe...
copy dist\TickTockWidget.exe prototype\ /Y

REM Copy LICENSE file (required)
echo Copying LICENSE...
if exist LICENSE (
    copy LICENSE prototype\ /Y
    echo   ✅ LICENSE copied
) else (
    echo   ⚠️  LICENSE file not found
)

REM Copy README.md file (optional)
echo Copying README.md...
if exist README.md (
    copy README.md prototype\ /Y
    echo   ✅ README.md copied
) else (
    echo   ⚠️  README.md file not found (optional)
)

echo.
echo =========================================
echo   BUILD COMPLETE! 
echo   Executable: prototype\TickTockWidget.exe
echo   Size: ~12.5 MB
echo =========================================
echo.
pause
