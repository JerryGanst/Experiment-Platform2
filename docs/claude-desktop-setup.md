# Claude Desktop 集成指南

## 🚀 概览

Smart Email AI 是一个专为Claude Desktop设计的MCP（Model Context Protocol）邮件处理工具集。**现在支持直接连接iCloud邮箱进行真实邮件分析**！告别演示模式，开始处理您的真实邮件数据。

## ✨ 核心特性

### 🍎 **iCloud真实邮件集成** (NEW!)
- **实时邮件访问**: 直接连接用户的iCloud邮箱 (user@example.com)
- **安全SSL连接**: 使用SSL/TLS加密和应用专用密码
- **智能邮件分析**: AI驱动的邮件内容理解和洞察
- **多维度搜索**: 支持主题、发件人、正文内容搜索
- **邮箱统计**: 实时邮箱概览和数据分析

### 🎛️ **Outlook邮件解析**
- **复杂HTML处理**: 清理Word格式、VML图形、条件注释
- **转发链解析**: 递归识别邮件转发历史
- **表格数据提取**: 智能识别并转换为Markdown格式
- **中英文支持**: 完美处理混合语言内容

### 📊 **数据管理**
- **模块化架构**: 解耦的配置管理和数据处理
- **配置热更新**: 实时配置调整，无需重启
- **缓存机制**: 优化性能，减少重复请求

## 🛠️ 快速设置

### 1. 安装依赖
```bash
cd smart_email_ai
pip install -r requirements.txt
```

### 2. 配置Claude Desktop

在您的 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "smart-email-ai": {
      "command": "python",
      "args": [
        "/Users/user/smart_email_ai/main.py",
        "--mcp"
      ],
      "cwd": "/Users/user/smart_email_ai"
    }
  }
}
```

### 3. 重启Claude Desktop

配置完成后，重启Claude Desktop以加载MCP服务器。

## 🍎 iCloud邮箱使用指南

### 🚀 **快速开始**
```
1. 连接到iCloud邮箱：connect_to_icloud()
2. 查看邮箱概览：get_icloud_inbox_summary()
3. 分析最近邮件：analyze_icloud_recent_emails(10)
4. 智能搜索邮件：search_icloud_emails_smart("关键词", 20)
5. 安全断开：disconnect_icloud()
```

### 📱 **典型使用场景**

#### **日常邮件监控**
```
"请连接我的iCloud邮箱，查看今天有什么重要的邮件"
```

#### **智能邮件搜索**
```
"搜索我所有关于'项目'的邮件，找出最重要的几封"
```

#### **邮件模式分析**
```
"分析我最近20封邮件，告诉我主要的沟通模式和趋势"
```

#### **特定内容查找**
```
"在我的邮箱中搜索包含'会议'的邮件，并总结相关安排"
```

### 🔒 **安全说明**
- 使用应用专用密码，不是Apple ID密码
- SSL/TLS加密连接，确保数据安全
- 支持安全断开连接，清理缓存数据

## 🛠️ 可用的MCP工具

### 🍎 **iCloud邮箱集成**
- `connect_to_icloud()` - 连接到Jerry的iCloud邮箱
- `get_icloud_inbox_summary()` - 获取iCloud邮箱概览统计
- `analyze_icloud_recent_emails(count)` - 智能分析最近的iCloud邮件
- `search_icloud_emails_smart(query, max_results)` - 智能搜索iCloud邮件
- `disconnect_icloud()` - 安全断开iCloud连接

### 📧 **邮件处理工具**
- `parse_outlook_email(html_content)` - 解析Outlook邮件HTML
- `analyze_outlook_email_structure(html_content)` - 分析邮件结构
- `extract_outlook_tables(html_content)` - 专门提取邮件表格数据

### 🧪 **系统工具**  
- `setup_email_system()` - 初始化邮件处理系统
- `get_system_status()` - 获取系统状态信息
- `test_config_loading()` - 测试配置加载
- `analyze_demo_emails()` - 分析演示邮件数据（备用）

## 🎯 **使用建议**

### 💡 **最佳实践**

1. **连接管理**: 使用完成后记得断开连接以节省资源
2. **批量分析**: 一次分析10-20封邮件获得最佳洞察
3. **精确搜索**: 使用具体关键词提高搜索准确性
4. **定期监控**: 通过邮箱概览了解邮件趋势

### ⚡ **性能优化**

- **缓存机制**: 系统自动缓存邮件数据，避免重复下载
- **智能限制**: 搜索和分析结果自动限制在合理范围内
- **错误恢复**: 网络问题时自动重试和优雅降级

## 🆚 **iCloud vs 演示模式对比**

| 特性 | iCloud模式 | 演示模式 |
|------|-----------|----------|
| 数据源 | 真实iCloud邮件 | 静态演示数据 |
| 实时性 | ✅ 实时数据 | ❌ 固定数据 |
| 数据量 | ✅ 完整邮箱 | ❌ 10封样本 |
| 搜索功能 | ✅ 全文搜索 | ❌ 有限搜索 |
| AI分析 | ✅ 基于真实模式 | ⚠️ 基于样本 |
| 个人相关性 | ✅ 100%相关 | ❌ 通用样本 |

## 🔧 **故障排除**

### 常见问题

#### **连接失败**
```
问题：connect_to_icloud() 返回连接失败
解决：检查网络连接和应用专用密码是否正确
```

#### **搜索无结果**
```
问题：search_icloud_emails_smart() 没有找到邮件
解决：尝试更通用的关键词或检查关键词拼写
```

#### **性能慢**  
```
问题：邮件分析耗时较长
解决：减少分析的邮件数量，使用5-10封进行测试
```

## 🎉 **开始使用**

现在您已经完成了配置，可以在Claude Desktop中开始使用Smart Email AI！

**推荐第一次使用流程**：
1. `connect_to_icloud()` - 建立连接
2. `get_icloud_inbox_summary()` - 了解邮箱状况  
3. `analyze_icloud_recent_emails(5)` - 快速分析测试
4. 根据需要进行搜索和深度分析
5. `disconnect_icloud()` - 使用完成后断开

祝您使用愉快！🚀 