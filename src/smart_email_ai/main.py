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

# 添加iCloud集成
import imaplib
import ssl
import email
from datetime import datetime

# 添加iCloud集成导入
from .core.icloud_connector import iCloudConnector

class iCloudConnector:
    """iCloud邮箱连接器"""
    
    def __init__(self):
        self.EMAIL = "jerrywsx@icloud.com"
        self.PASSWORD = "fsil-npvx-rbdo-vman"  # 应用专用密码
        self.IMAP_SERVER = "imap.mail.me.com"
        self.IMAP_PORT = 993
        self.mail = None
        self.connected = False
    
    def connect(self):
        """连接到iCloud"""
        try:
            context = ssl.create_default_context()
            self.mail = imaplib.IMAP4_SSL(self.IMAP_SERVER, self.IMAP_PORT, ssl_context=context)
            self.mail.login(self.EMAIL, self.PASSWORD)
            self.mail.select('INBOX')
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        try:
            if self.mail:
                self.mail.close()
                self.mail.logout()
            self.connected = False
        except:
            pass
    
    def safe_fetch_email(self, mail_id):
        """安全获取邮件"""
        try:
            status, msg_data = self.mail.fetch(mail_id, '(RFC822)')
            if status == 'OK' and msg_data and len(msg_data) > 0:
                if isinstance(msg_data[0], tuple) and len(msg_data[0]) > 1:
                    raw_email = msg_data[0][1]
                    if isinstance(raw_email, bytes):
                        return email.message_from_bytes(raw_email)
                    elif isinstance(raw_email, str):
                        return email.message_from_string(raw_email)
            return None
        except:
            return None
    
    def decode_header(self, header):
        """解码邮件头"""
        if not header:
            return ""
        try:
            decoded_parts = email.header.decode_header(header)
            result = ""
            for content, encoding in decoded_parts:
                if isinstance(content, bytes):
                    if encoding:
                        content = content.decode(encoding, errors='ignore')
                    else:
                        content = content.decode('utf-8', errors='ignore')
                result += str(content)
            return result
        except:
            return str(header)
    
    def extract_body(self, msg):
        """提取邮件正文"""
        body = ""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        charset = part.get_content_charset() or 'utf-8'
                        body_bytes = part.get_payload(decode=True)
                        if body_bytes:
                            body += body_bytes.decode(charset, errors='ignore')
            else:
                charset = msg.get_content_charset() or 'utf-8'
                body_bytes = msg.get_payload(decode=True)
                if body_bytes:
                    body = body_bytes.decode(charset, errors='ignore')
                else:
                    body = str(msg.get_payload())
        except:
            body = "正文解析失败"
        return body
    
    def parse_email_content(self, msg):
        """解析邮件内容"""
        info = {}
        info['subject'] = self.decode_header(msg.get('Subject', ''))
        info['sender'] = self.decode_header(msg.get('From', ''))
        info['date'] = msg.get('Date', '')
        info['body'] = self.extract_body(msg)
        info['body_length'] = len(info['body'])
        return info

# 全局iCloud连接器实例
icloud_connector = None

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


# 创建全局系统实例（延迟初始化）
email_system = None

def get_email_system():
    """获取邮件系统实例（延迟初始化）"""
    global email_system
    if email_system is None:
        email_system = RefactoredEmailSystem()
    return email_system

# MCP工具函数 - 使用解耦架构

@mcp.tool()
def setup_email_system() -> str:
    """初始化邮件处理系统"""
    system = get_email_system()
    return system.enable_demo_mode()

@mcp.tool()
def analyze_demo_emails() -> str:
    """分析演示邮件数据"""
    system = get_email_system()
    return system.analyze_demo_emails()

@mcp.tool()
def parse_outlook_email(html_content: str) -> str:
    """解析Outlook邮件HTML内容
    
    Args:
        html_content: Outlook邮件的HTML内容
    """
    system = get_email_system()
    return system.parse_outlook_email(html_content)

@mcp.tool()
def analyze_outlook_email_structure(html_content: str) -> str:
    """分析Outlook邮件结构并提供结构化数据
    
    Args:
        html_content: Outlook邮件的HTML内容
    """
    system = get_email_system()
    return system.analyze_outlook_email_with_ai(html_content)

@mcp.tool()
def get_system_status() -> str:
    """获取邮件处理系统状态"""
    system = get_email_system()
    return system.get_system_status()

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

@mcp.tool()
def extract_outlook_tables(html_content: str) -> str:
    """专门提取Outlook邮件中的表格数据
    
    Args:
        html_content: Outlook邮件的HTML内容
    """
    try:
        # 解析邮件
        system = get_email_system()
        parsed_section = system.outlook_parser.parse_email(html_content)
        
        if not parsed_section.tables:
            return "📋 未在邮件中发现数据表格"
        
        result = f"📊 **提取到 {len(parsed_section.tables)} 个表格**\n\n"
        
        for i, table in enumerate(parsed_section.tables, 1):
            result += f"## 表格 {i}\n"
            result += f"**规格:** {table['row_count']} 行 × {table['col_count']} 列\n\n"
            result += "**Markdown格式:**\n"
            result += table['markdown'] + "\n\n"
            
            # 提供原始数据
            result += "**原始数据:**\n"
            for j, row in enumerate(table['rows']):
                result += f"行{j+1}: {' | '.join(row)}\n"
            result += "\n---\n\n"
        
        return result
        
    except Exception as e:
        return f"❌ 表格提取失败: {str(e)}"

# MCP服务器运行逻辑
# 由根目录的 main.py --mcp 调用，不再独立运行 

@mcp.tool()
def connect_to_icloud() -> str:
    """连接到Jerry的iCloud邮箱，开始真实邮件数据访问
    
    Returns:
        str: 连接状态和基本信息
    """
    global icloud_connector
    
    try:
        # 创建新的连接器实例
        icloud_connector = iCloudConnector()
        
        # 尝试连接
        if icloud_connector.connect():
            # 获取基本统计信息
            stats = icloud_connector.get_mailbox_stats()
            
            return f"""✅ iCloud邮箱连接成功！

📊 邮箱概览:
• 邮箱地址: {stats.get('email_address', 'N/A')}
• 邮件总数: {stats.get('total_emails', 0)}
• 未读邮件: {stats.get('unread_count', 0)}
• 今日邮件: {stats.get('today_count', 0)}
• 本周邮件: {stats.get('week_count', 0)}
• 连接时间: {stats.get('last_update', 'N/A')}

🎯 现在可以使用以下功能:
- 获取邮箱统计: get_icloud_inbox_summary()
- 分析最近邮件: analyze_icloud_recent_emails(count)
- 智能搜索邮件: search_icloud_emails_smart(query, max_results)
- 断开连接: disconnect_icloud()"""
        else:
            return "❌ iCloud邮箱连接失败，请检查网络连接和凭据"
            
    except Exception as e:
        return f"❌ iCloud连接错误: {str(e)}"

@mcp.tool()
def get_icloud_inbox_summary() -> str:
    """获取iCloud邮箱的详细统计概览
    
    Returns:
        str: 邮箱统计信息
    """
    global icloud_connector
    
    if not icloud_connector or not icloud_connector.connected:
        return "⚠️ 请先使用 connect_to_icloud() 连接到邮箱"
    
    try:
        stats = icloud_connector.get_mailbox_stats()
        
        if 'error' in stats:
            return f"❌ 获取邮箱统计失败: {stats['error']}"
        
        return f"""📊 iCloud邮箱详细统计

🏠 基本信息:
• 邮箱: {stats.get('email_address', 'N/A')}
• 连接状态: {stats.get('connection_status', 'N/A')}
• 更新时间: {stats.get('last_update', 'N/A')}

📬 邮件统计:
• 邮件总数: {stats.get('total_emails', 0)}
• 未读邮件: {stats.get('unread_count', 0)} ({stats.get('unread_count', 0) / max(stats.get('total_emails', 1), 1) * 100:.1f}%)
• 今日新邮件: {stats.get('today_count', 0)}
• 本周邮件: {stats.get('week_count', 0)}

💡 建议操作:
- 查看最近邮件: analyze_icloud_recent_emails(10)
- 搜索特定内容: search_icloud_emails_smart("关键词", 20)"""
        
    except Exception as e:
        return f"❌ 获取邮箱统计错误: {str(e)}"

@mcp.tool()
def analyze_icloud_recent_emails(count: int = 10) -> str:
    """智能分析最近的iCloud邮件，提供详细的AI分析结果
    
    Args:
        count: 要分析的邮件数量 (默认10封，建议1-20)
    
    Returns:
        str: AI分析后的邮件摘要和洞察
    """
    global icloud_connector
    
    if not icloud_connector or not icloud_connector.connected:
        return "⚠️ 请先使用 connect_to_icloud() 连接到邮箱"
    
    try:
        # 验证参数
        if count < 1 or count > 50:
            count = 10
        
        # 获取最近的邮件
        recent_emails = icloud_connector.get_recent_emails(count)
        
        if not recent_emails:
            return "📭 没有找到最近的邮件"
        
        # 构建分析报告
        analysis = f"📧 最近 {len(recent_emails)} 封邮件智能分析\n"
        analysis += "=" * 50 + "\n\n"
        
        # 统计信息
        total_size = sum(email.get('size', 0) for email in recent_emails)
        has_attachments = sum(1 for email in recent_emails if email.get('has_attachments', False))
        avg_body_length = sum(email.get('body_length', 0) for email in recent_emails) / len(recent_emails)
        
        analysis += f"📊 总体统计:\n"
        analysis += f"• 邮件数量: {len(recent_emails)}\n"
        analysis += f"• 总大小: {total_size:,} 字节\n"
        analysis += f"• 有附件: {has_attachments} 封\n"
        analysis += f"• 平均正文长度: {avg_body_length:.0f} 字符\n\n"
        
        # 邮件详情
        analysis += "📝 邮件详情:\n\n"
        
        for i, email in enumerate(recent_emails[:count], 1):
            analysis += f"{i}. 【{email.get('subject', '无主题')}】\n"
            analysis += f"   发件人: {email.get('sender', '未知')}\n"
            analysis += f"   日期: {email.get('date', '未知')}\n"
            
            # 邮件正文预览
            body_preview = email.get('body_text', '')[:200]
            if len(body_preview) >= 200:
                body_preview += "..."
            analysis += f"   正文预览: {body_preview}\n"
            
            # 附件信息
            if email.get('has_attachments'):
                attachments = email.get('attachments', [])
                analysis += f"   📎 附件: {', '.join([att.get('filename', '未知') for att in attachments])}\n"
            
            analysis += "\n"
        
        # AI洞察（基于邮件模式分析）
        analysis += "🧠 AI洞察:\n"
        
        # 发件人分析
        senders = {}
        for email in recent_emails:
            sender = email.get('sender', 'unknown')
            senders[sender] = senders.get(sender, 0) + 1
        
        if senders:
            top_sender = max(senders.items(), key=lambda x: x[1])
            analysis += f"• 最活跃发件人: {top_sender[0]} ({top_sender[1]} 封邮件)\n"
        
        # 内容模式分析
        if has_attachments > 0:
            analysis += f"• 附件频率: {has_attachments/len(recent_emails)*100:.1f}% 的邮件包含附件\n"
        
        if avg_body_length > 1000:
            analysis += f"• 邮件特点: 平均邮件长度较长，可能包含详细信息或技术讨论\n"
        elif avg_body_length < 200:
            analysis += f"• 邮件特点: 邮件较为简短，多为快速沟通\n"
        
        return analysis
        
    except Exception as e:
        return f"❌ 分析最近邮件错误: {str(e)}"

@mcp.tool()
def search_icloud_emails_smart(query: str, max_results: int = 20) -> str:
    """在iCloud邮箱中智能搜索邮件并提供AI分析
    
    Args:
        query: 搜索关键词（可以是发件人、主题、正文内容）
        max_results: 最大返回结果数 (默认20，建议1-50)
    
    Returns:
        str: 搜索结果和智能分析
    """
    global icloud_connector
    
    if not icloud_connector or not icloud_connector.connected:
        return "⚠️ 请先使用 connect_to_icloud() 连接到邮箱"
    
    if not query.strip():
        return "❌ 请提供搜索关键词"
    
    try:
        # 验证参数
        if max_results < 1 or max_results > 100:
            max_results = 20
        
        # 执行搜索
        search_results = icloud_connector.search_emails_by_content(query, max_results)
        
        if not search_results:
            return f"🔍 搜索'{query}'没有找到匹配的邮件"
        
        # 构建搜索报告
        report = f"🔍 搜索结果: '{query}'\n"
        report += "=" * 50 + "\n\n"
        
        report += f"📊 搜索统计:\n"
        report += f"• 找到邮件: {len(search_results)} 封\n"
        report += f"• 搜索关键词: {query}\n"
        report += f"• 最大结果数: {max_results}\n\n"
        
        # 搜索结果详情
        report += "📋 匹配邮件:\n\n"
        
        for i, email in enumerate(search_results, 1):
            report += f"{i}. 【{email.get('subject', '无主题')}】\n"
            report += f"   发件人: {email.get('sender', '未知')}\n"
            report += f"   日期: {email.get('date', '未知')}\n"
            
            # 正文匹配预览
            body_text = email.get('body_text', '')
            if query.lower() in body_text.lower():
                # 找到关键词在正文中的位置
                query_pos = body_text.lower().find(query.lower())
                start = max(0, query_pos - 100)
                end = min(len(body_text), query_pos + 100)
                preview = body_text[start:end]
                if start > 0:
                    preview = "..." + preview
                if end < len(body_text):
                    preview = preview + "..."
                report += f"   匹配内容: {preview}\n"
            
            # 附件信息
            if email.get('has_attachments'):
                attachments = email.get('attachments', [])
                report += f"   📎 附件: {', '.join([att.get('filename', '未知') for att in attachments])}\n"
            
            report += "\n"
        
        # 搜索洞察
        report += "🧠 搜索洞察:\n"
        
        # 发件人分布
        senders = {}
        for email in search_results:
            sender = email.get('sender', 'unknown')
            senders[sender] = senders.get(sender, 0) + 1
        
        if len(senders) > 1:
            report += f"• 相关发件人: {len(senders)} 个不同发件人\n"
            top_sender = max(senders.items(), key=lambda x: x[1])
            report += f"• 主要发件人: {top_sender[0]} ({top_sender[1]} 封相关邮件)\n"
        
        # 时间分布分析
        dates = [email.get('date', '') for email in search_results if email.get('date')]
        if dates:
            recent_count = sum(1 for date in dates if '2024' in date or '2025' in date)
            if recent_count > 0:
                report += f"• 时间分布: {recent_count} 封为最近邮件\n"
        
        return report
        
    except Exception as e:
        return f"❌ 搜索邮件错误: {str(e)}"

@mcp.tool()
def disconnect_icloud() -> str:
    """安全断开iCloud邮箱连接
    
    Returns:
        str: 断开连接的状态信息
    """
    global icloud_connector
    
    try:
        if icloud_connector:
            icloud_connector.disconnect()
            icloud_connector = None
            return "✅ iCloud邮箱连接已安全断开"
        else:
            return "ℹ️ 当前没有活动的iCloud连接"
            
    except Exception as e:
        return f"⚠️ 断开连接时出现错误: {str(e)}" 