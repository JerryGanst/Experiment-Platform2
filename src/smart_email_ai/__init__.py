"""
Smart Email AI - MCP邮件处理工具集

一个专为MCP（Model Context Protocol）设计的邮件处理工具集，提供：
- Outlook邮件解析（包括转发链和表格提取）
- iCloud邮箱实时连接和分析
- 邮件数据结构化处理
- 配置管理和数据持久化
- 邮件内容格式转换

核心理念：
- 工具专注于数据处理，AI分析由外部模型完成
- 提供结构化的邮件数据供AI模型分析
- 遵循MCP最佳实践，保持工具单一职责

主要组件：
- EmailParser: 邮件内容解析和清理
- iCloudConnector: iCloud邮箱实时连接（NEW!）
- DataManager: 邮件数据管理和持久化
- ConfigManager: 配置文件管理
- MCPTools: MCP协议工具集
"""

__version__ = "2.1.0"
__author__ = "Smart Email AI Team"

from .main import RefactoredEmailSystem
from .interfaces.email_interface import EmailData, email_data_manager
from .interfaces.config_interface import config_manager
from .core.parser import OutlookEmailParser

# 添加iCloud连接器导出
try:
    from .core.icloud_connector import iCloudConnector
    icloud_available = True
except ImportError:
    # 如果iCloud依赖不可用，提供占位符
    class iCloudConnector:
        def __init__(self):
            raise ImportError("iCloud连接器需要额外的依赖包")
    icloud_available = False

__all__ = [
    'RefactoredEmailSystem',
    'EmailData', 
    'email_data_manager',
    'config_manager',
    'OutlookEmailParser',
    'iCloudConnector',
    'icloud_available'
] 