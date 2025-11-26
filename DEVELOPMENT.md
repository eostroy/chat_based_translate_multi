# ATP 开发指南

## 🚀 快速启动

### 方法一：使用启动脚本（推荐）

**Windows:**
```bash
# 双击运行或在命令行执行
start.bat
```

**Linux/Mac:**
```bash
# 添加执行权限
chmod +x start.sh

# 运行
./start.sh
```

### 方法二：使用开发脚本（最快）

```bash
python dev.py
```

这是最推荐的开发方式，具有以下特性：
- ⚡ 超快启动速度
- 🔥 **代码热重载**：修改任何Python文件或HTML模板，保存后自动刷新
- 🐛 详细的调试信息
- 📝 自动检查和安装依赖

### 方法三：直接运行

```bash
python main.py
```

## 🔥 热重载说明

启动后，你可以：

1. **修改Python代码**：保存后服务器自动重启
2. **修改HTML模板**：保存后刷新浏览器即可看到变化
3. **修改CSS/JavaScript**：由于是内嵌在HTML中，修改后刷新浏览器

**不需要手动重启服务器！**

## 📁 目录结构

```
ATP/
├── main.py                 # 主应用程序
├── dev.py                  # 开发服务器启动脚本
├── start.bat               # Windows启动脚本
├── start.sh                # Linux/Mac启动脚本
├── templates/
│   └── index.html         # 前端页面
├── translators/           # 翻译器模块
│   ├── __init__.py
│   ├── base.py
│   ├── deepseek.py
│   ├── openai.py
│   ├── anthropic.py
│   └── google.py
├── uploads/               # 上传文件目录
└── outputs/               # 输出文件目录
```

## 🛠️ 开发模式 vs 生产模式

### 开发模式（默认）
- 自动重载
- 详细错误信息
- 调试工具栏
- 单进程

```bash
python main.py          # 开发模式
python dev.py          # 开发模式（推荐）
```

### 生产模式
- 多进程
- 性能优化
- 错误日志

```bash
python main.py --prod   # 生产模式
```

## 💡 开发技巧

### 1. 实时查看日志

启动后，所有日志会输出到控制台和 `translation.log` 文件。

### 2. 快速测试API

使用curl或Postman测试API：

```bash
# 测试翻译API
curl -X POST http://localhost:5000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Hello World",
    "api_type": "deepseek",
    "api_key": "your-key",
    "model": "deepseek-chat",
    "source_lang": "英文",
    "target_lang": "中文",
    "temperature": 1.0
  }'
```

### 3. 清理缓存

如果遇到奇怪的问题，清理Python缓存：

```bash
# Windows
del /s /q __pycache__
del /s /q *.pyc

# Linux/Mac
find . -type d -name "__pycache__" -delete
find . -type f -name "*.pyc" -delete
```

或者使用启动脚本，它们会自动清理。

## 🐛 调试技巧

### 1. 查看详细错误

开发模式下，Flask会显示详细的错误页面，包括：
- 完整的堆栈跟踪
- 变量值
- 交互式调试器（浏览器中）

### 2. 打印调试信息

在代码中添加：

```python
import logging
logger = logging.getLogger(__name__)

logger.info("这是信息")
logger.debug("这是调试信息")
logger.error("这是错误")
```

### 3. 断点调试

使用Python调试器：

```python
import pdb; pdb.set_trace()
```

或使用VSCode/PyCharm的断点功能。

## 📝 修改前端

前端代码在 `templates/index.html`，包含：
- HTML结构
- CSS样式（`<style>`标签内）
- JavaScript逻辑（`<script>`标签内）

修改后保存，刷新浏览器即可看到效果。

## 🔧 配置说明

### 端口配置

修改 `main.py` 或 `dev.py` 中的端口号：

```python
app.run(
    host='0.0.0.0',
    port=5000,  # 改成其他端口，如 8080
    ...
)
```

### 上传限制

修改 `main.py` 中的配置：

```python
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
```

## 🚀 性能优化建议

1. **开发时使用dev.py**：启动最快，体验最好
2. **代码改动小时**：保存即可，等待自动重载
3. **代码改动大时**：手动重启可能更快（Ctrl+C然后重新运行）
4. **清理日志文件**：定期清理 `translation.log`

## ❓ 常见问题

**Q: 修改代码后没有自动重载？**
A: 检查是否有语法错误。查看控制台输出。

**Q: 端口被占用？**
A: 修改端口号或关闭占用端口的程序。

**Q: 找不到模块？**
A: 运行 `pip install -r requirements.txt`

**Q: 启动很慢？**
A: 使用 `dev.py`，它启动最快。

## 📚 相关资源

- Flask文档: https://flask.palletsprojects.com/
- Python调试: https://docs.python.org/3/library/pdb.html
- 热重载原理: 使用Werkzeug的reloader监控文件变化

---

**开发愉快！🎉**
