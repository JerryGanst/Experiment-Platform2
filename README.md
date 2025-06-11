# Smart Email AI 🛠️📧

> MCP邮件处理工具集 - 专业的邮件解析和数据处理工具

## 🌟 项目简介

Smart Email AI 是一个专为MCP（Model Context Protocol）环境设计的邮件处理工具集。它专注于邮件的解析、清理、结构化处理，为AI模型提供高质量的邮件数据。遵循"工具做处理，AI做分析"的设计原则。

### 🎯 核心功能

- **🔍 专精邮件解析**: 支持Outlook HTML邮件的深度解析，包括转发链和嵌套结构
- **📊 表格数据提取**: 智能识别和提取邮件中的数据表格，转换为结构化格式
- **🧹 内容清理优化**: 移除HTML噪声，提取纯净的邮件内容
- **📝 格式标准化**: 将复杂邮件结构转换为标准化的数据格式
- **⚙️ 配置驱动**: 支持灵活的配置管理和数据持久化
- **🔌 MCP集成**: 完全遵循MCP协议，提供标准化的工具接口

### 💡 设计理念

**为什么不内置AI分析？**

在MCP环境中，AI分析应该由外部AI模型（如Claude）完成，而不是在工具内部重复实现：

- ✅ **职责分离**: 工具负责数据处理，AI负责智能分析
- ✅ **避免重复**: 不与外部AI模型功能重叠
- ✅ **性能优化**: 避免双重AI处理的资源浪费
- ✅ **更好维护**: 单一职责原则，代码更清晰

**工具的价值在于提供高质量的结构化数据，让AI模型能够进行更准确的分析。**

### 🏗️ 系统架构

本项目采用模块化、解耦的架构设计：

```
smart_email_ai/
├── src/smart_email_ai/          # 核心源代码
│   ├── __init__.py             # 包初始化
│   ├── main.py                 # 主系统入口
│   ├── interfaces/             # 接口层
│   │   ├── config_interface.py # 配置管理接口
│   │   └── email_interface.py  # 邮件数据接口
│   ├── core/                   # 核心业务逻辑
│   │   └── parser.py          # 邮件解析器
│   └── mcp/                    # MCP服务层
├── data/                       # 数据文件
│   ├── config.yaml            # 系统配置
│   └── demo_emails.json       # 演示邮件数据
├── examples/                   # 示例代码
├── tests/                      # 测试文件
├── docs/                       # 文档
├── legacy/                     # 遗留代码
└── main.py                     # 项目主入口
```

## 🚀 快速开始

### 📋 系统要求

- Python 3.8+
- 8GB+ RAM（用于AI分析）
- 支持的操作系统：Windows, macOS, Linux

### ⚡ 安装

1. **克隆项目**
```bash
git clone <repository-url>
cd smart_email_ai
```

2. **创建虚拟环境**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
# 或使用uv（推荐）
uv pip install -r requirements.txt
```

### 🎮 使用方法

#### 1. 快速演示
```bash
# 运行完整演示
python main.py --demo

# 或运行快速开始示例
python examples/quick_start.py
```

#### 2. 分析邮件文件
```bash
# 分析HTML邮件文件
python main.py --analyze path/to/your/email.html

# 分析EML邮件文件
python main.py --analyze path/to/your/email.eml
```

#### 3. 交互式模式
```bash
# 启动交互式界面
python main.py
```

#### 4. 运行测试
```bash
# 系统功能测试
python main.py --test
```

## 🔧 配置说明

系统配置文件位于 `data/config.yaml`，包含以下主要配置：

### AI分析器配置
```yaml
ai_settings:
  learning_rate: 0.1
  trust_threshold: 0.5
  priority_weights:
    urgency: 0.4      # 紧急性权重
    sender: 0.3       # 发件人权重
    content: 0.2      # 内容权重
    importance: 0.1   # 重要性权重
```

### 邮件解析器配置
```yaml
parser_settings:
  forward_patterns:
    - "-----\\s*原始邮件\\s*-----"
    - "-----\\s*Forwarded message\\s*-----"
  table_detection:
    skip_layout_tables: true
    min_data_rows: 2
```

### 情感分析配置
```yaml
ai_settings:
  emotional_keywords:
    urgent: ["urgent", "紧急", "asap", "立即"]
    positive: ["great", "excellent", "perfect", "优秀"]
    negative: ["problem", "issue", "error", "问题"]
```

## 💻 编程接口

### 基本使用

```python
from smart_email_ai import RefactoredEmailSystem, OutlookEmailParser

# 初始化系统
system = RefactoredEmailSystem()

# 解析Outlook邮件
parser = OutlookEmailParser()
parsed_email = parser.parse_email(html_content)

# AI分析
analysis = system.analyze_email_priority(email_content)
print(f"优先级: {analysis['priority']}")
print(f"情感倾向: {analysis['sentiment']}")
```

### 高级功能

```python
# 加载演示数据
from smart_email_ai import email_data_manager, config_manager

demo_emails = email_data_manager.load_demo_emails()
config = config_manager.load_config()

# 批量分析
results = system.batch_analyze_emails(demo_emails)

# 自定义配置
custom_config = {
    'ai_settings': {
        'learning_rate': 0.2,
        'priority_weights': {'urgency': 0.5}
    }
}
system.update_config(custom_config)
```

## 📊 功能特性详解

### 🔍 邮件解析能力

- **Outlook HTML清理**: 移除Word XML标记、VML图形、条件注释
- **多层转发处理**: 递归解析转发邮件链，保持层级关系
- **表格智能识别**: 区分数据表格和布局表格，提取有意义的数据
- **附件信息提取**: 识别并记录邮件附件信息

### 🧠 AI分析引擎

- **优先级算法**: 基于多因子的优先级评分系统
- **情感分析**: NLP驱动的情感倾向识别
- **发件人画像**: 基于历史交互的发件人类型识别
- **学习机制**: 支持用户反馈驱动的模型改进

### 🎯 MCP工具集成

系统集成了完整的MCP（Model Context Protocol）工具集：

- `setup_refactored_email()`: 系统初始化
- `analyze_emails_refactored()`: 批量分析
- `parse_outlook_email_refactored()`: 邮件解析
- `test_configuration_loading()`: 配置测试

## 🔬 开发与测试

### 运行测试
```bash
# 完整测试套件
python main.py --test

# 单元测试
python -m pytest tests/

# 配置测试
python -c "from smart_email_ai import config_manager; print('✅ 配置加载成功')"
```

### 开发环境设置
```bash
# 开发模式安装
pip install -e .

# 代码格式化
black src/
flake8 src/

# 类型检查
mypy src/
```

## 📁 项目文件说明

### 核心文件
- `main.py`: 项目主入口，支持命令行参数
- `src/smart_email_ai/main.py`: 重构后的主系统类
- `src/smart_email_ai/core/parser.py`: Outlook邮件解析器
- `src/smart_email_ai/interfaces/`: 配置和数据接口层

### 数据文件
- `data/config.yaml`: 系统配置文件
- `data/demo_emails.json`: 演示邮件数据集
- `data/analysis_results/`: 分析结果存储目录

### 工具文件
- `examples/quick_start.py`: 快速开始示例
- `legacy/smart_email_ai.py`: 原始单体代码（保留参考）

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请参见 `LICENSE` 文件。

## 🆘 支持与帮助

### 常见问题

**Q: 为什么YAML配置加载失败？**
A: 确保已安装PyYAML: `pip install pyyaml`

**Q: 邮件解析失败怎么办？**
A: 检查邮件文件编码，确保为UTF-8格式

**Q: 如何添加自定义情感关键词？**
A: 编辑 `data/config.yaml` 中的 `emotional_keywords` 配置

### 联系方式

- 🐛 Bug报告: 创建GitHub Issue
- 💡 功能建议: 创建GitHub Discussion
- 📧 技术支持: 查看项目Wiki

## 🔄 版本历史

### v2.0.0 (当前版本)
- ✅ 完全重构为模块化架构
- ✅ 实现配置文件外部化
- ✅ 添加MCP工具集成
- ✅ 增强AI分析能力
- ✅ 改进邮件解析器

### v1.0.0 (Legacy)
- ✅ 基础邮件解析功能
- ✅ 简单优先级分析
- ✅ Outlook HTML处理

---

<div align="center">

**🚀 让AI为您的邮件管理添翼！**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/your-repo)

</div>
