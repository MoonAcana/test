@echo off
cd /d "%~dp0"

echo.
echo ================================
echo        SignX-Demo Launcher
echo ================================
echo Current folder: %cd%
echo.

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found.
    echo Please make sure run.bat is in the project root folder.
    pause
    exit /b 1
)

if not exist "backend\main.py" (
    echo [ERROR] backend\main.py not found.
    echo Please check the project structure.
    pause
    exit /b 1
)

set "PYTHON_CMD=python"

echo [1/5] Checking Python...
python --version >nul 2>nul
if errorlevel 1 (
    set "PYTHON_CMD=py -3"
    py -3 --version >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python not found.
        echo Please install Python and add it to PATH.
        pause
        exit /b 1
    )
)

echo.
echo [2/5] Checking virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo venv not found. Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo venv found.
)

echo.
echo [3/5] Activating virtual environment...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo.
echo [4/5] Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    echo Please check requirements.txt or your network connection.
    pause
    exit /b 1
)

echo.
echo [5/5] Starting SignX-Demo...
echo Browser will open automatically:
echo http://127.0.0.1:8000
echo.
echo Do not close this window while using SignX-Demo.
echo.

start "" powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8000'"

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

echo.
echo SignX-Demo stopped.
pause
