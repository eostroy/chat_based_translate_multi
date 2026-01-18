@echo off
chcp 65001 > nul
echo ========================================
echo   ATP: AI Translation Platform
echo   快速启动脚本 (开发模式)
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [1/3] 检查依赖包...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在安装依赖包...
    pip install -r requirements.txt
)

echo [2/3] 清理缓存...
if exist __pycache__ rmdir /s /q __pycache__
if exist atp\translators\__pycache__ rmdir /s /q atp\translators\__pycache__

echo [3/3] 启动应用程序...
echo.
echo ========================================
echo   🚀 应用启动中...
echo   📝 代码修改后会自动重载
echo   🌐 访问地址: http://localhost:5000
echo   ⛔ 按 Ctrl+C 停止服务器
echo ========================================
echo.

python main.py

pause
