# ATP: AI-driven Translation Platform

一个功能强大的AI驱动翻译平台，支持多模型、多语言、多场景的智能翻译服务。

## 📖 项目简介

ATP (AI-driven Translation Platform) 是一个基于现代AI技术的智能翻译平台，支持多种主流AI模型（DeepSeek、OpenAI、Anthropic、Google），提供文档翻译、交互式翻译等多种翻译模式。平台采用现代化的Web界面设计，支持实时翻译、批量处理、自定义提示词等高级功能。

## ✨ 核心功能

### 1. 交互式翻译
- **双模式切换**:
  - 单模型翻译：快速单次翻译
  - 多模型翻译：最多3个模型同时翻译，横向对比结果
- **多模型支持**: 支持 DeepSeek、OpenAI GPT-4、Anthropic Claude、Google Gemini 等主流模型
- **自定义参数**: 可调节温度参数、系统提示词等，满足不同翻译需求
- **结果对比**: 支持弹窗横向对比多个模型的翻译结果
- **统一界面**: 单一主界面，操作更直观

### 2. 文档翻译
- **多格式支持**: 支持 Word (.docx/.doc) 和文本 (.txt) 文档
- **智能分块**: 自动将长文档分块处理，确保翻译质量
- **批量处理**: 支持双工作区并行处理，提高翻译效率
- **进度显示**: 实时显示翻译进度和状态

### 3. AI 译审
- **单模型译审**: 使用单个AI模型对翻译质量进行全面评估
- **双模型对比**: 对比两个模型的评估质量，分析优劣
- **模型开会**: 多个AI专家角色扮演，民主表决形成最终评估
  - 术语专家：评估专业术语准确性
  - 流畅度专家：评估自然度和可读性
  - 文化适应性专家：评估文化差异和本地化
  - 准确性专家：评估意思传达完整性
  - 风格专家：评估写作和语言风格
  - 语法专家：评估语法正确性和规范性
- 自动评分和改进建议

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 包管理器

### 🎯 超快速启动（推荐）

#### Windows用户

**方法一：双击运行（最简单）**
```
双击 dev.bat 文件即可启动
```

**方法二：命令行运行**
```bash
python dev.py
```

#### Linux/Mac用户

```bash
# 方法一：使用启动脚本
chmod +x start.sh
./start.sh

# 方法二：使用开发脚本（推荐）
python3 dev.py
```

### ✨ 特色功能

- 🔥 **自动热重载**：修改代码后自动重启，无需手动重启！
- ⚡ **超快启动**：优化的开发服务器，启动速度更快
- 📝 **实时更新**：修改HTML/CSS/JS后刷新浏览器即可看到效果
- 🐛 **详细调试**：开发模式下显示详细的错误信息

### 传统安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ATP
```

2. **安装依赖**
```bash
pip install -r text_process/requirements.txt
```

或者手动安装：
```bash
pip install flask==3.0.2
pip install python-docx==1.1.0
pip install requests==2.31.0
pip install anthropic==0.18.1
pip install google-generativeai==0.3.2
pip install openai==1.12.0
pip install aiohttp==3.9.3
pip install hypercorn==0.16.0
pip install docx2txt
```

3. **运行应用**
```bash
# 开发模式（默认，支持热重载）
python main.py

# 或使用快速开发脚本
python dev.py

# 生产模式
python main.py --prod
```

4. **访问应用**
在浏览器中打开 `http://localhost:5000`

### 📖 开发指南

详细的开发说明请查看 [DEVELOPMENT.md](DEVELOPMENT.md)，包括：
- 热重载配置
- 调试技巧
- 性能优化
- 常见问题解决

## 📚 使用指南

### 交互式翻译

1. 点击"交互翻译"卡片进入交互翻译页面
2. 在左侧设置栏配置：
   - 选择API提供商（DeepSeek/OpenAI/Anthropic/Google）
   - 输入API密钥
   - 选择模型
   - 设置温度参数（0-2，控制输出随机性）
   - 选择源语言和目标语言
   - 可选：添加系统提示词以自定义翻译风格
3. 在右侧输入框输入要翻译的内容
4. 点击"发送"或按 Enter 键发送
5. 查看翻译结果，支持多轮对话

### 文档翻译

1. 点击"文档翻译"卡片进入文档翻译页面
2. 上传要翻译的文档（支持 .txt, .doc, .docx 格式）
3. 配置翻译参数：
   - 选择API和模型
   - 输入API密钥
   - 设置温度参数
   - 选择源语言和目标语言
   - 可选：添加系统提示词和用户提示词
4. 点击"开始翻译"
5. 等待翻译完成，点击下载链接获取结果

### 温度参数说明

- **0.0-0.5**: 更确定、一致的翻译，适合技术文档
- **0.5-1.0**: 平衡创造性和准确性，适合一般文本
- **1.0-2.0**: 更灵活、有创造性的翻译，适合文学文本

## 🔧 项目结构

```
ATP/
├── main.py                 # Flask主应用程序
├── translators.py          # 多模型翻译器实现
├── text_processor.py       # 文本处理和分块模块
├── deepseek_translator.py  # DeepSeek翻译器（已整合到translators.py）
├── terminology_extract.py  # 术语提取模块
├── 2vec_and_rag.py        # 向量化和RAG相关功能
├── templates/
│   └── index.html         # Web界面模板
├── uploads/               # 上传文件临时存储
├── outputs/               # 翻译结果存储
├── text_process/
│   └── requirements.txt   # 依赖包列表
└── README.md             # 项目说明文档
```

## 🔑 API密钥获取

### DeepSeek
1. 访问 [DeepSeek官网](https://www.deepseek.com/)
2. 注册账号并登录
3. 在控制台创建API密钥

### OpenAI
1. 访问 [OpenAI官网](https://platform.openai.com/)
2. 注册账号并登录
3. 在API Keys页面创建密钥

### Anthropic
1. 访问 [Anthropic官网](https://www.anthropic.com/)
2. 注册账号并登录
3. 在控制台创建API密钥

### Google
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 使用Google账号登录
3. 创建API密钥

## 🎨 技术栈

### 后端
- **Python 3.8+**: 主要编程语言
- **Flask**: Web框架
- **Hypercorn**: ASGI服务器，支持异步处理
- **python-docx**: Word文档处理
- **docx2txt**: 文档文本提取

### AI模型集成
- **DeepSeek API**: DeepSeek Chat / DeepSeek Reasoner
- **OpenAI API**: GPT-4 / GPT-4.5 Preview
- **Anthropic API**: Claude 3.7 Sonnet
- **Google API**: Gemini Pro

### 前端
- **HTML5/CSS3**: 现代化响应式设计
- **JavaScript (ES6+)**: 交互逻辑
- **Font Awesome**: 图标库
- **Google Fonts (Inter)**: 字体

## ⚙️ 配置说明

### 文本处理参数

在 `text_processor.py` 中可以调整：
- `max_tokens`: 每个文本块的最大token数（默认2000）

### 翻译参数

在 `translators.py` 中可以调整：
- `temperature`: 温度参数（0-2）
- `top_p`: 核采样参数
- `max_tokens`: 最大输出token数

## 📝 注意事项

1. **API密钥安全**: 请妥善保管您的API密钥，不要将其提交到公共代码仓库
2. **文件大小限制**: 默认最大上传文件大小为50MB
3. **翻译时间**: 大型文档可能需要较长的处理时间，请耐心等待
4. **API配额**: 请注意各API提供商的调用限制和费用
5. **网络连接**: 确保网络连接稳定，以便正常调用API

## 🐛 常见问题

### Q: 翻译失败怎么办？
A: 请检查：
- API密钥是否正确
- 网络连接是否正常
- API配额是否充足
- 文件格式是否支持

### Q: 如何提高翻译质量？
A: 
- 使用更高级的模型（如GPT-4、Claude 3.7）
- 添加详细的系统提示词
- 调整温度参数
- 对长文档进行分段处理

### Q: 支持哪些语言？
A: 目前支持：中文、英文、日文、韩文、德文、法文、西班牙文、俄文等。具体支持的语言取决于所选模型的能力。

### Q: 可以离线使用吗？
A: 不可以，本平台需要调用在线API服务，需要网络连接。

## 🔄 更新日志

### v1.0.0
- 初始版本发布
- 支持交互式翻译和文档翻译
- 集成多种AI模型
- 现代化Web界面

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 Issue 反馈。

---

**ATP** - 让AI翻译更简单、更智能、更高效 🚀 