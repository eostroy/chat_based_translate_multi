@echo off
chcp 65001 > nul
title ATP 开发服务器
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║     ATP: AI Translation Platform - 开发服务器           ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM 检查Python是否存在
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请确保Python已安装并添加到PATH
    echo.
    echo 请访问 https://www.python.org/downloads/ 下载安装Python
    echo.
    pause
    exit /b 1
)

REM 显示Python版本
echo [信息] 检测到Python版本:
python --version
echo.

REM 检查dev.py是否存在
if not exist "dev.py" (
    echo [错误] 未找到dev.py文件
    echo 请确保在ATP项目根目录下运行此脚本
    echo.
    pause
    exit /b 1
)

REM 运行开发服务器
python dev.py

REM 如果Python脚本异常退出，显示错误
if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败，错误代码: %errorlevel%
    echo.
)

pause
