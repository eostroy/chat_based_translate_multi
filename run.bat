@echo off
chcp 65001 > nul
cls

echo ==========================================
echo   ATP 翻译平台启动中...
echo ==========================================
echo.

REM 检查Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [X] 错误: 未找到Python
    echo.
    echo 请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [√] Python已安装
python --version
echo.

REM 检查main.py
if not exist "main.py" (
    color 0C
    echo [X] 错误: 找不到main.py
    echo 请确保在ATP项目目录下运行此脚本
    echo.
    pause
    exit /b 1
)

echo [√] 找到主程序
echo.

REM 检查依赖
echo [*] 检查依赖包...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [!] Flask未安装，正在安装...
    pip install flask -q
)
echo [√] 依赖检查完成
echo.

echo ==========================================
echo   启动成功！
echo.
echo   访问地址: http://localhost:5000
echo   按 Ctrl+C 停止服务器
echo ==========================================
echo.

REM 启动应用
python main.py

pause
