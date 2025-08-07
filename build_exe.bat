@echo off
echo.
echo =======================================
echo   TICK-TOCK WIDGET - BUILD EXECUTABLE
echo =======================================
echo.

cd /d "%~dp0"
C:/Users/MWina/anaconda3/Scripts/conda.exe run -p C:\Users\MWina\anaconda3 --no-capture-output pyinstaller --clean tick_tock_widget.spec

echo.
echo Creating release folder...
if not exist release mkdir release
copy dist\TickTockWidget.exe release\ /Y
copy README.md release\ /Y
copy LICENSE release\ /Y

echo.
echo =========================================
echo   BUILD COMPLETE! 
echo   Executable: release\TickTockWidget.exe
echo   Size: ~12.5 MB
echo =========================================
echo.
pause
