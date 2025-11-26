@echo off
REM Auto switch to script directory
cd /d "%~dp0"

cls
echo.
echo  ========================================
echo    ATP Translation Platform
echo  ========================================
echo.
echo  Checking environment...
echo.

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [X] Python not found
    echo  Please install Python from python.org
    echo.
    pause
    exit /b 1
)
echo  [OK] Python installed

REM Check main.py
if not exist "main.py" (
    echo  [X] main.py not found
    echo  Current dir: %CD%
    echo.
    pause
    exit /b 1
)
echo  [OK] main.py found

REM Check Flask
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo  [!] Installing Flask...
    pip install flask -q
)
echo  [OK] Flask ready

echo.
echo  ========================================
echo    Server starting...
echo.
echo    URL: http://localhost:5000
echo    Press Ctrl+C to stop
echo  ========================================
echo.

python main.py

pause
