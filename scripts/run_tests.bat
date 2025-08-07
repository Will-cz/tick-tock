@echo off
REM Batch script to run Tick-Tock Widget tests on Windows
REM Usage: run_tests.bat [command] [options]

setlocal EnableDelayedExpansion

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Default to showing help if no arguments
if "%1"=="" (
    echo Tick-Tock Widget Test Runner for Windows
    echo.
    echo Usage: run_tests.bat [command] [options]
    echo.
    echo Commands:
    echo   unit         Run unit tests
    echo   integration  Run integration tests
    echo   e2e          Run end-to-end tests
    echo   gui          Run GUI tests
    echo   all          Run all tests
    echo   fast         Run fast tests only
    echo   install      Install test dependencies
    echo   lint         Run code linting
    echo   format       Format code with black
    echo.
    echo Options:
    echo   -v           Verbose output
    echo   -c           Generate coverage report
    echo.
    echo Examples:
    echo   run_tests.bat unit -v
    echo   run_tests.bat all -c
    echo   run_tests.bat install
    exit /b 0
)

REM Parse command and options
set COMMAND=%1
set VERBOSE=
set COVERAGE=

:parse_args
shift
if "%1"=="-v" (
    set VERBOSE=-v
    goto parse_args
)
if "%1"=="-c" (
    set COVERAGE=--cov=src/tick_tock_widget --cov-report=term-missing --cov-report=html:coverage_html
    goto parse_args
)
if not "%1"=="" goto parse_args

REM Execute commands
if "%COMMAND%"=="unit" (
    echo Running unit tests...
    python -m pytest tests/unit/ %VERBOSE% %COVERAGE%
    goto end
)

if "%COMMAND%"=="integration" (
    echo Running integration tests...
    python -m pytest tests/integration/ -m integration %VERBOSE%
    goto end
)

if "%COMMAND%"=="e2e" (
    echo Running end-to-end tests...
    python -m pytest tests/e2e/ -m e2e %VERBOSE%
    goto end
)

if "%COMMAND%"=="gui" (
    echo Running GUI tests...
    python -m pytest -m gui %VERBOSE%
    goto end
)

if "%COMMAND%"=="all" (
    echo Running all tests...
    python -m pytest tests/ %VERBOSE% %COVERAGE%
    goto end
)

if "%COMMAND%"=="fast" (
    echo Running fast tests only...
    python -m pytest tests/ -m "not slow" %VERBOSE%
    goto end
)

if "%COMMAND%"=="install" (
    echo Installing test dependencies...
    python -m pip install -r requirements.txt
    goto end
)

if "%COMMAND%"=="lint" (
    echo Running code linting...
    python -m flake8 src/ tests/
    if !errorlevel! neq 0 (
        echo Linting failed!
        exit /b 1
    )
    echo Linting passed!
    goto end
)

if "%COMMAND%"=="format" (
    echo Formatting code with black...
    python -m black src/ tests/
    goto end
)

echo Unknown command: %COMMAND%
echo Run "run_tests.bat" without arguments to see available commands.
exit /b 1

:end
if %errorlevel% equ 0 (
    echo.
    echo ✅ Command completed successfully!
) else (
    echo.
    echo ❌ Command failed!
    exit /b 1
)
