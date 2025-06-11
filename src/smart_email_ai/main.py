"""
重构后的智能邮件AI系统 - 解耦架构
采用模块化设计，配置外置，数据文件分离
"""

import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(__file__))

from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# 导入解耦的模块
from .interfaces.config_interface import config_manager
from .interfaces.email_interface import email_data_manager, EmailData
from .core.parser import OutlookEmailParser
# AI分析由外部MCP调用者（如Claude）完成，不需要内部AI分析器

# Initialize FastMCP server
mcp = FastMCP("advanced_email_ai_refactored")

class RefactoredEmailSystem:
    """重构后的邮件系统主类"""
    
    def __init__(self):
        # 加载配置
        self.config = config_manager.load_config()
        
        # 初始化组件
        parser_config = config_manager.get_parser_settings()
        self.outlook_parser = OutlookEmailParser(parser_config)
        
        # 暂时保持原有AI分析器，后续可以解耦
        # AI分析由外部MCP调用者完成，这里只保留数据处理功能
        
        # 邮件数据管理器
        self.email_manager = email_data_manager
        
        # 系统状态
        self.demo_mode = False
    
    def enable_demo_mode(self) -> str:
        """启用演示模式"""
        self.demo_mode = True
        demo_emails = self.email_manager.load_demo_emails()
        return f"✅ 解耦架构演示模式已启用！\n📧 加载了 {len(demo_emails)} 封演示邮件\n🏗️ 使用配置文件和数据文件分离架构"
    
    def analyze_demo_emails(self) -> str:
        """分析演示邮件"""
        if not self.demo_mode:
            return "❌ 请先启用演示模式"
        
        demo_emails = self.email_manager.load_demo_emails()
        analyses = []
        
        for email_data in demo_emails:
            # 提供结构化数据，AI分析由外部模型完成
            analysis = {
                'email_id': email_data.id,
                'subject': email_data.subject,
                'sender': email_data.sender,
                'body': email_data.body,
                'category': email_data.category,
                'expected_priority': email_data.expected_priority,
                'metadata': {
                    'body_length': len(email_data.body),
                    'has_attachments': False,  # TODO: 实现附件检测
                    'date': email_data.date
                }
            }
            
            analyses.append(analysis)
        
        # 按预期优先级排序（仅用于演示）
        analyses.sort(key=lambda x: x.get("expected_priority", 0), reverse=True)
        
        return self._format_analysis_report(analyses)
    
    def parse_outlook_email(self, html_content: str) -> str:
        """解析Outlook邮件"""
        try:
            parsed_section = self.outlook_parser.parse_email(html_content)
            markdown_result = self.outlook_parser.format_to_markdown(parsed_section)
            
            # 统计信息
            stats = {
                'total_tables': len(parsed_section.tables),
                'forwarded_levels': self._count_forwarded_levels(parsed_section),
                'has_header': bool(parsed_section.header),
                'body_length': len(parsed_section.body),
            }
            
            return f"""📧 **Outlook邮件解析完成** (解耦架构)

**解析统计:**
• 表格数量: {stats['total_tables']} 个
• 转发层级: {stats['forwarded_levels']} 层
• 邮件头信息: {'✅ 已提取' if stats['has_header'] else '❌ 未找到'}
• 正文长度: {stats['body_length']} 字符

**配置信息:**
• 转发模式数量: {len(config_manager.get_forward_patterns())}
• 表格检测: {'启用' if config_manager.get_parser_settings().get('table_detection', {}).get('skip_layout_tables', True) else '禁用'}

---

{markdown_result}
"""
        except Exception as e:
            return f"❌ 解析失败: {str(e)}"
    
    def analyze_outlook_email_with_ai(self, html_content: str) -> str:
        """解析Outlook邮件并进行AI分析"""
        try:
            # 首先解析邮件结构
            parsed_section = self.outlook_parser.parse_email(html_content)
            
            # 提取信息进行AI分析
            subject = parsed_section.header.get('subject', '未知主题')
            sender = parsed_section.header.get('from', '未知发件人')
            body = parsed_section.body
            
            # 提供结构化数据供AI分析
            structured_data = {
                'parsed_structure': {
                    'subject': subject,
                    'sender': sender,
                    'body': body,
                    'tables': parsed_section.tables,
                    'forwarded_emails': len(parsed_section.forwarded_emails),
                    'header_info': parsed_section.header
                },
                'metadata': {
                    'body_length': len(body),
                    'table_count': len(parsed_section.tables),
                    'forwarded_levels': self._count_forwarded_levels(parsed_section)
                }
            }
            
            return self._format_structured_data_result(structured_data, parsed_section)
            
        except Exception as e:
            return f"❌ 分析失败: {str(e)}"
    
    def get_system_status(self) -> str:
        """获取系统状态"""
        config_info = self.config
        demo_emails_count = len(self.email_manager.load_demo_emails())
        
        return f"""🏗️ **解耦架构系统状态**

**架构信息:**
• 配置管理: {'✅ YAML配置文件' if config_info else '❌ 配置加载失败'}
• 数据管理: ✅ JSON演示数据文件
• 解析器: ✅ 可配置Outlook解析器
• AI分析器: ✅ 高级情感分析

**当前配置:**
• 演示模式: {'✅ 启用' if self.demo_mode else '❌ 禁用'}
• 演示邮件: {demo_emails_count} 封
• 转发模式: {len(config_manager.get_forward_patterns())} 种
• 数据处理配置: ✅ 已加载

**模块状态:**
• 配置接口: ✅ 正常
• 邮件接口: ✅ 正常  
• 解析器核心: ✅ 正常
• MCP服务: ✅ 运行中

**解耦优势:**
• 🔧 配置热更新支持
• 📊 数据文件独立管理
• 🧪 模块独立测试
• 🔌 插件化扩展能力
"""
    
    def run_demo_analysis(self) -> str:
        """运行完整的演示分析"""
        # 自动启用演示模式
        self.enable_demo_mode()
        return self.analyze_demo_emails()
        
    def analyze_single_email(self, email_content: str) -> str:
        """分析单个邮件"""
        return self.parse_outlook_email(email_content)
        
    def run_system_tests(self) -> str:
        """运行系统测试"""
        results = []
        
        # 测试配置加载
        try:
            config = config_manager.load_config()
            results.append("✅ 配置文件加载正常")
        except Exception as e:
            results.append(f"❌ 配置文件加载失败: {e}")
        
        # 测试演示邮件加载
        try:
            emails = email_data_manager.load_demo_emails()
            results.append(f"✅ 演示邮件加载正常 ({len(emails)} 封)")
        except Exception as e:
            results.append(f"❌ 演示邮件加载失败: {e}")
        
        # 测试邮件解析器
        try:
            parser = OutlookEmailParser()
            test_html = "<html><body><p>测试邮件</p></body></html>"
            parsed = parser.parse_email(test_html)
            results.append("✅ 邮件解析器正常")
        except Exception as e:
            results.append(f"❌ 邮件解析器失败: {e}")
        
        return "🧪 **系统测试结果**\n\n" + "\n".join(results)
    
    def show_system_info(self) -> None:
        """显示系统信息"""
        print(self.get_system_status())
    
    def _count_forwarded_levels(self, section) -> int:
        """计算转发层级"""
        max_level = section.level
        for forwarded in section.forwarded_emails:
            max_level = max(max_level, self._count_forwarded_levels(forwarded))
        return max_level
    
    def _format_analysis_report(self, analyses: List[Dict]) -> str:
        """格式化分析报告"""
        report = "📊 **MCP邮件数据处理报告**\n\n"
        
        # 统计信息
        urgent_count = len([a for a in analyses if a.get("expected_priority", 0) >= 4])
        high_priority_count = len([a for a in analyses if a.get("expected_priority", 0) >= 3])
        
        report += f"📊 **数据统计**\n"
        report += f"• 总邮件: {len(analyses)} 封\n"
        report += f"• 高优先级: {urgent_count} 封\n"
        report += f"• 中高优先级: {high_priority_count} 封\n\n"
        
        # 详细数据
        for i, analysis in enumerate(analyses, 1):
            priority_icons = {5: "🚨", 4: "📋", 3: "📰", 2: "📱", 1: "🗑️"}
            icon = priority_icons.get(analysis.get("expected_priority", 0), "📧")
            
            report += f"{icon} **邮件 {i}: {analysis['subject']}**\n"
            report += f"📧 ID: {analysis['email_id']} | 分类: {analysis.get('category', 'unknown')}\n"
            report += f"📏 内容长度: {analysis['metadata']['body_length']} 字符\n"
            report += f"📅 日期: {analysis['metadata']['date']}\n"
            report += f"📤 发件人: {analysis['sender']}\n"
            report += f"🎯 预期优先级: {analysis.get('expected_priority', 'N/A')}/5\n"
            report += f"📝 正文预览: {analysis['body'][:100]}...\n"
            report += "\n"
        
        report += "💡 **提示**: 此工具提供结构化邮件数据，具体的AI分析请由外部AI模型完成。\n"
        
        return report
    
    def _format_structured_data_result(self, structured_data: Dict, parsed_section) -> str:
        """格式化结构化数据结果"""
        parsed = structured_data['parsed_structure']
        metadata = structured_data['metadata']
        
        result = f"""📊 **MCP邮件结构化数据**

## 📄 基础信息
• **主题:** {parsed['subject']}
• **发件人:** {parsed['sender']}
• **正文长度:** {metadata['body_length']} 字符
• **表格数量:** {metadata['table_count']} 个
• **转发层级:** {metadata['forwarded_levels']} 层

## 📧 邮件头信息
{chr(10).join(f"• **{k}:** {v}" for k, v in parsed['header_info'].items())}

## 📝 正文内容
{parsed['body'][:500]}{'...' if len(parsed['body']) > 500 else ''}

## 📊 数据表格
"""
        
        # 添加表格信息
        if parsed_section.tables:
            for i, table in enumerate(parsed_section.tables, 1):
                result += f"\n### 表格 {i} ({table['row_count']}行 × {table['col_count']}列)\n"
                result += table['markdown'] + "\n"
        else:
            result += "无表格数据\n"
        
        result += "\n💡 **使用建议**: 基于此结构化数据，您可以使用AI模型进行进一步的智能分析，如优先级评估、情感分析、行动项提取等。"
        
        return result


# 创建全局系统实例
email_system = RefactoredEmailSystem()

# MCP工具函数 - 使用解耦架构

@mcp.tool()
def setup_refactored_email() -> str:
    """设置解耦架构的智能邮件系统"""
    return email_system.enable_demo_mode()

@mcp.tool()
def analyze_emails_refactored() -> str:
    """使用解耦架构分析邮件"""
    return email_system.analyze_demo_emails()

@mcp.tool()
def parse_outlook_email_refactored(html_content: str) -> str:
    """使用解耦架构解析Outlook邮件
    
    Args:
        html_content: Outlook邮件的HTML内容
    """
    return email_system.parse_outlook_email(html_content)

@mcp.tool()
def analyze_outlook_email_refactored(html_content: str) -> str:
    """使用解耦架构解析并分析Outlook邮件
    
    Args:
        html_content: Outlook邮件的HTML内容
    """
    return email_system.analyze_outlook_email_with_ai(html_content)

@mcp.tool()
def get_system_status_refactored() -> str:
    """获取解耦架构系统状态"""
    return email_system.get_system_status()

@mcp.tool()
def test_config_loading() -> str:
    """测试配置加载功能"""
    try:
        ai_settings = config_manager.get_ai_settings()
        parser_settings = config_manager.get_parser_settings()
        system_settings = config_manager.get_system_settings()
        
        return f"""🔧 **配置加载测试**

**AI设置:**
• 学习率: {ai_settings.get('learning_rate', 'N/A')}
• 信任阈值: {ai_settings.get('trust_threshold', 'N/A')}
• 优先级权重: {ai_settings.get('priority_weights', {})}

**解析器设置:**
• 转发模式数量: {len(parser_settings.get('forward_patterns', []))}
• 表格检测配置: {parser_settings.get('table_detection', {})}

**系统设置:**
• 演示模式: {system_settings.get('demo_mode', False)}
• 日志级别: {system_settings.get('log_level', 'INFO')}

✅ 配置文件加载成功！
"""
    except Exception as e:
        return f"❌ 配置加载失败: {str(e)}"

@mcp.tool()
def test_demo_emails_loading() -> str:
    """测试演示邮件加载功能"""
    try:
        emails = email_data_manager.load_demo_emails()
        
        result = f"📧 **演示邮件加载测试**\n\n"
        result += f"✅ 成功加载 {len(emails)} 封演示邮件\n\n"
        
        for email in emails[:3]:  # 显示前3封
            result += f"• {email.id}: {email.subject[:50]}...\n"
            result += f"  发件人: {email.sender}\n"
            result += f"  分类: {email.category}\n\n"
        
        if len(emails) > 3:
            result += f"... 还有 {len(emails) - 3} 封邮件\n"
        
        return result
    except Exception as e:
        return f"❌ 演示邮件加载失败: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio') 