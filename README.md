# ATP：AI Translation Platform

ATP 是一个面向多模型的翻译平台，提供交互式翻译、文档翻译与 AI 译审能力，支持多语言、多场景的翻译工作流。

## 核心功能

- **交互式翻译**：支持单模型与多模型对比翻译，适合实时对话与结果横向比较。
- **文档翻译**：支持文本与常见文档格式的翻译，具备分段处理与进度反馈。
- **AI 译审**：提供单模型评审、双模型对比、双阶段校验与多专家“模型开会”评审模式。

## 快速开始

### 环境要求

- Python 3.8+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动方式

**开发模式（推荐）**

```bash
python dev.py
```

**通用启动**

```bash
python main.py
```

**脚本启动（Windows / Linux / macOS）**

```bash
start.bat
# 或
./start.sh
```

启动后访问：`http://localhost:5000`

## 使用说明

1. 打开网页后选择功能卡片：交互翻译 / 文档翻译 / AI 译审。
2. 根据界面提示填写 API 类型、模型与密钥。
3. 输入文本或上传文件，点击执行即可获得翻译或评审结果。

## 项目结构

```
ATP/
├── atp/                  # 核心代码
│   ├── services/         # 文本处理与译审服务
│   ├── translators/      # 模型适配器
│   └── web/              # Web 应用与模板
├── tools/                # 独立脚本工具
├── main.py               # 应用入口
├── dev.py                # 开发启动脚本
├── requirements.txt      # 依赖列表
└── README.md
```

## 其他文档

- 开发细节请参考 [DEVELOPMENT.md](DEVELOPMENT.md)
- 启动指引可见 `HOW-TO-START.txt`
