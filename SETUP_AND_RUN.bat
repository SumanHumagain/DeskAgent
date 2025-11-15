@echo off
:: Desktop Automation Agent - Setup and Run Script
:: Automatically sets up environment and runs with admin privileges

echo ============================================
echo Desktop Automation Agent - Setup
echo ============================================
echo.

:: Check if Python venv exists
if not exist "venv\Scripts\python.exe" (
    echo Python virtual environment not found
    echo Please run: python -m venv venv
    echo Then install requirements: venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:: Check if node_modules exists
if not exist "ui\node_modules" (
    echo Installing Node.js dependencies...
    cd ui
    call npm install
    cd ..
    echo.
)

:: Check for .env file
if not exist ".env" (
    echo WARNING: .env file not found
    echo Please copy .env.example to .env and configure your OpenAI API key
    echo.
    pause
    exit /b 1
)

:: Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ============================================
    echo ADMINISTRATOR PRIVILEGES REQUIRED
    echo ============================================
    echo.
    echo This application requires Administrator privileges to:
    echo  - Modify Windows Firewall settings
    echo  - Control Windows Defender
    echo  - Manage Bluetooth settings
    echo  - Access system settings
    echo.
    echo Please RIGHT-CLICK this script and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo ✓ Running with Administrator privileges
echo ✓ Environment configured
echo.
echo Starting Desktop Automation Agent...
echo.

:: Launch the UI
cd ui
call npm start

if %errorLevel% neq 0 (
    echo.
    echo ERROR: Application failed to start
    pause
)
