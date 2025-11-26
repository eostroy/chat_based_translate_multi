#!/bin/bash

echo "========================================"
echo "  ATP: AI Translation Platform"
echo "  快速启动脚本 (开发模式)"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "[1/3] 检查依赖包..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[提示] 正在安装依赖包..."
    pip3 install -r requirements.txt
fi

echo "[2/3] 清理缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

echo "[3/3] 启动应用程序..."
echo ""
echo "========================================"
echo "  🚀 应用启动中..."
echo "  📝 代码修改后会自动重载"
echo "  🌐 访问地址: http://localhost:5000"
echo "  ⛔ 按 Ctrl+C 停止服务器"
echo "========================================"
echo ""

python3 main.py
