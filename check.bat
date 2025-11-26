@echo off
chcp 65001 > nul
cls
color 0B

echo ==========================================
echo   ATP 环境诊断工具
echo ==========================================
echo.

echo [1/5] 检查Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo    [X] 未找到Python
    echo    请从 https://www.python.org/downloads/ 安装Python
    set "has_error=1"
) else (
    echo    [√] Python已安装
    python --version
)
echo.

echo [2/5] 检查pip...
where pip >nul 2>&1
if %errorlevel% neq 0 (
    echo    [X] 未找到pip
    set "has_error=1"
) else (
    echo    [√] pip已安装
    pip --version
)
echo.

echo [3/5] 检查项目文件...
if not exist "main.py" (
    echo    [X] 找不到main.py
    echo    当前目录: %CD%
    set "has_error=1"
) else (
    echo    [√] main.py存在
)

if not exist "templates\index.html" (
    echo    [X] 找不到templates/index.html
    set "has_error=1"
) else (
    echo    [√] templates/index.html存在
)
echo.

echo [4/5] 检查关键依赖...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo    [X] Flask未安装
    echo    运行: pip install flask
    set "has_error=1"
) else (
    echo    [√] Flask已安装
)

python -c "import docx" 2>nul
if %errorlevel% neq 0 (
    echo    [!] python-docx未安装 (文档翻译需要)
) else (
    echo    [√] python-docx已安装
)
echo.

echo [5/5] 检查端口占用...
netstat -ano | findstr ":5000" >nul 2>&1
if %errorlevel% equ 0 (
    echo    [!] 端口5000已被占用
    echo    请关闭占用该端口的程序或更改配置
) else (
    echo    [√] 端口5000可用
)
echo.

echo ==========================================
if defined has_error (
    color 0C
    echo   诊断结果: 发现问题
    echo   请根据上述提示解决问题后再次运行
) else (
    color 0A
    echo   诊断结果: 一切正常
    echo   可以运行 run.bat 启动应用
)
echo ==========================================
echo.

pause
