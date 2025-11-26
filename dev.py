#!/usr/bin/env python3
"""
ATP 开发服务器 - 超快速启动，支持热重载
使用方法：python dev.py
"""

import os
import sys
import subprocess

def print_banner():
    """打印启动横幅"""
    print("=" * 70)
    print("  🚀 ATP: AI Translation Platform - 开发服务器")
    print("=" * 70)
    print()

def check_dependencies():
    """检查并安装依赖"""
    required_packages = {
        'flask': 'Flask',
        'werkzeug': 'Werkzeug',
    }

    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"📦 检测到缺少依赖: {', '.join(missing)}")
        print("📝 正在安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q'] + missing)
        print("✅ 依赖安装完成\n")

def clean_cache():
    """清理Python缓存"""
    print("🧹 清理缓存文件...")
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dirs.append(os.path.join(root, '__pycache__'))
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                except:
                    pass

    for cache_dir in cache_dirs:
        try:
            import shutil
            shutil.rmtree(cache_dir)
        except:
            pass
    print("✅ 缓存清理完成\n")

def start_server():
    """启动开发服务器"""
    print("=" * 70)
    print("  ✨ 开发模式特性:")
    print("  - 🔥 代码修改后自动重载（无需重启）")
    print("  - 🐛 详细的错误信息和调试输出")
    print("  - ⚡ 快速启动和响应")
    print("=" * 70)
    print()
    print("  🌐 访问地址: http://localhost:5000")
    print("  📱 移动端访问: http://你的IP:5000")
    print("  ⛔ 按 Ctrl+C 停止服务器")
    print("=" * 70)
    print()

    # 设置环境变量
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'

    # 启动Flask应用
    from main import app

    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            threaded=True,
            extra_files=[  # 监控额外文件
                'templates/index.html',
                'translators/__init__.py',
                'translators/base.py',
                'translators/deepseek.py',
                'translators/openai.py',
                'translators/anthropic.py',
                'translators/google.py',
            ]
        )
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print_banner()
    check_dependencies()
    clean_cache()
    start_server()
