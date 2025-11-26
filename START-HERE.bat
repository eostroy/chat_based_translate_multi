@echo off
cd /d "%~dp0"

echo ==========================================
echo   ATP Translation Platform
echo ==========================================
echo.

if not exist "main.py" (
    echo ERROR: main.py not found
    echo Please run this script in ATP directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Starting server...
echo.
echo Visit: http://localhost:5000
echo Press Ctrl+C to stop
echo.

python main.py

pause
