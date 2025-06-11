# Claude Desktop MCP 配置指南

## 📡 配置 Smart Email AI MCP 服务器

### 🎯 快速配置

将以下配置添加到 Claude Desktop 的 MCP 配置文件中：

#### macOS/Linux 配置：
```json
{
  "mcpServers": {
    "smart_email_ai": {
      "command": "python",
      "args": ["/path/to/smart_email_ai/main.py", "--mcp"],
      "env": {
        "PYTHONPATH": "/path/to/smart_email_ai"
      }
    }
  }
}
```

#### Windows 配置：
```json
{
  "mcpServers": {
    "smart_email_ai": {
      "command": "python",
      "args": ["C:\\path\\to\\smart_email_ai\\main.py", "--mcp"],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\smart_email_ai"
      }
    }
  }
}
```

### 📁 配置文件位置

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

### 🔧 详细设置步骤

1. **找到项目路径**
   ```bash
   cd /path/to/smart_email_ai
   pwd  # 复制输出的绝对路径
   ```

2. **测试MCP服务器**
   ```bash
   # 确保MCP服务器可以启动
   python main.py --mcp
   ```

3. **编辑Claude Desktop配置**
   - 打开配置文件
   - 添加上述JSON配置
   - 将 `/path/to/smart_email_ai` 替换为实际路径

4. **重启Claude Desktop**
   - 保存配置文件
   - 重启Claude Desktop应用

### 🛠️ 可用的MCP工具

配置成功后，Claude将可以使用以下工具：

#### 🏗️ 系统管理
- `setup_email_system()` - 初始化邮件处理系统
- `get_system_status()` - 获取系统状态信息

#### 📧 邮件处理
- `parse_outlook_email(html_content)` - 解析Outlook邮件HTML
- `analyze_outlook_email_structure(html_content)` - 分析邮件结构
- `extract_outlook_tables(html_content)` - 专门提取邮件表格数据
- `analyze_demo_emails()` - 分析演示邮件数据

#### 🧪 测试工具
- `test_config_loading()` - 测试配置加载
- `test_demo_emails_loading()` - 测试演示邮件加载

### 💡 使用示例

配置完成后，你可以在Claude Desktop中这样使用：

```
请帮我分析这封Outlook邮件的结构：
[粘贴邮件HTML内容]
```

或者专门提取表格：
```
请帮我提取这封邮件中的所有表格数据：
[粘贴邮件HTML内容]
```

Claude会自动选择合适的工具来处理邮件。

### 🐛 故障排除

#### 问题1：工具未显示
- 检查配置文件JSON语法是否正确
- 确认路径是否正确（使用绝对路径）
- 重启Claude Desktop

#### 问题2：Python模块未找到
```json
{
  "mcpServers": {
    "smart_email_ai": {
      "command": "python",
      "args": ["/path/to/smart_email_ai/main.py", "--mcp"],
      "env": {
        "PYTHONPATH": "/path/to/smart_email_ai",
        "PATH": "/path/to/your/python:$PATH"
      }
    }
  }
}
```

#### 问题3：权限错误
```bash
# 确保文件有执行权限
chmod +x /path/to/smart_email_ai/main.py
```

#### 问题4：虚拟环境
如果使用虚拟环境：
```json
{
  "mcpServers": {
    "smart_email_ai": {
      "command": "/path/to/smart_email_ai/.venv/bin/python",
      "args": ["/path/to/smart_email_ai/main.py", "--mcp"]
    }
  }
}
```

### 📝 配置验证

运行以下命令验证配置：

```bash
# 1. 测试MCP服务器启动
python main.py --mcp

# 2. 测试命令行功能（确保不冲突）
python main.py --demo

# 3. 检查依赖
python -c "import yaml, mcp; print('✅ 依赖正常')"
```

### 🚀 高级配置

#### 调试模式
```json
{
  "mcpServers": {
    "smart_email_ai": {
      "command": "python",
      "args": ["/path/to/smart_email_ai/main.py", "--mcp"],
      "env": {
        "MCP_DEBUG": "1",
        "PYTHONPATH": "/path/to/smart_email_ai"
      }
    }
  }
}
```

#### 自定义配置文件
```json
{
  "mcpServers": {
    "smart_email_ai": {
      "command": "python", 
      "args": [
        "/path/to/smart_email_ai/main.py", 
        "--mcp",
        "--config", "/path/to/custom/config.yaml"
      ]
    }
  }
}
```

---

📞 **需要帮助？** 
- 检查 [README.md](../README.md) 的完整文档
- 运行 `python main.py --help` 查看所有选项
- 提交 GitHub Issue 获取支持 