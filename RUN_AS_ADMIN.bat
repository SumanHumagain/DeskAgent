@echo off
:: Desktop Automation Agent - Admin Launcher
:: This batch file launches the Electron UI with Administrator privileges

echo ============================================
echo Desktop Automation Agent
echo Starting with Administrator Privileges...
echo ============================================
echo.

:: Check if already running as admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Already running with Administrator privileges
    echo.
) else (
    echo Requesting Administrator elevation...
    echo.
)

:: Navigate to UI directory
cd /d "%~dp0ui"

:: Launch Electron with npm start (will inherit admin rights if this script is run as admin)
echo Launching Desktop Automation Agent UI...
echo.
call npm start

:: Keep window open if there's an error
if %errorLevel% neq 0 (
    echo.
    echo ERROR: Failed to start application
    echo Error code: %errorLevel%
    pause
)
