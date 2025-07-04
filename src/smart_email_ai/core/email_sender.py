"""
邮件发送核心模块 - Smart Email AI系统组件

提供安全、高效的邮件发送功能
支持HTML邮件、附件和多种邮件服务器
与现有缓存和iCloud系统集成
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from pathlib import Path


class EmailSender:
    """邮件发送器 - 支持多种邮件服务器和动态发件人配置"""
    
    def __init__(self, email_address: str = None, password: str = None, provider: str = None, use_default: bool = False):
        """
        初始化邮件发送器
        
        Args:
            email_address: 发件人邮箱地址
            password: 邮箱密码或应用专用密码  
            provider: 邮件服务提供商 ('icloud', 'gmail', 'outlook')
            use_default: 是否使用默认配置（已废弃，为兼容性保留）
        """
        # 验证必要参数
        if not email_address or not password:
            raise ValueError("必须提供邮箱地址和密码")
            
        self.email_address = email_address
        self.password = password
        
        # 自动检测邮件服务商
        if not provider:
            provider = self._detect_provider(email_address)
        
        self.provider = provider
        
        # iCloud SMTP 配置
        self.smtp_config = {
            'icloud': {
                'server': 'smtp.mail.me.com',
                'port': 587,
                'use_tls': True
            },
            'gmail': {
                'server': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True
            },
            'outlook': {
                'server': 'smtp.office365.com',
                'port': 587,
                'use_tls': True
            }
        }
        
        # 验证支持的服务商
        if provider not in self.smtp_config:
            raise ValueError(f"不支持的邮件服务商: {provider}")
        
        # 检测邮箱类型
        self.provider = self._detect_email_provider()
        self.server_config = self.smtp_config.get(self.provider, self.smtp_config['icloud'])
        self.connected = False
        
    def _detect_email_provider(self) -> str:
        """检测邮箱服务提供商"""
        domain = self.email_address.split('@')[1].lower()
        
        if 'icloud.com' in domain or 'me.com' in domain:
            return 'icloud'
        elif 'gmail.com' in domain:
            return 'gmail'
        elif 'outlook.com' in domain or 'hotmail.com' in domain or 'live.com' in domain:
            return 'outlook'
        else:
            return 'icloud'  # 默认使用iCloud配置
    
    def send_email(self, 
                   to_email: str, 
                   subject: str, 
                   content: str,
                   content_type: str = 'html',
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None,
                   attachments: Optional[List[str]] = None) -> Dict[str, Any]:
        """发送邮件
        
        Args:
            to_email: 收件人邮箱地址
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型 ('html' 或 'plain')
            cc: 抄送列表
            bcc: 密送列表
            attachments: 附件文件路径列表
            
        Returns:
            Dict: 发送结果
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加抄送和密送
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # 添加邮件内容
            msg.attach(MIMEText(content, content_type, 'utf-8'))
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(msg, file_path)
            
            # 发送邮件
            result = self._send_via_smtp(msg, to_email, cc, bcc)
            
            return {
                'success': True,
                'message': '邮件发送成功',
                'details': {
                    'to': to_email,
                    'subject': subject,
                    'provider': self.provider,
                    'timestamp': datetime.now().isoformat(),
                    'attachments_count': len(attachments) if attachments else 0
                },
                **result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'邮件发送失败: {str(e)}',
                'details': {
                    'to': to_email,
                    'subject': subject,
                    'provider': self.provider,
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    def _send_via_smtp(self, msg: MIMEMultipart, to_email: str, 
                       cc: Optional[List[str]] = None, 
                       bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """通过SMTP发送邮件"""
        config = self.smtp_config[self.provider]
        
        # 构建收件人列表
        recipients = [to_email]
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)
        
        # 创建SMTP连接
        server = smtplib.SMTP(config['server'], config['port'])
        
        if config['use_tls']:
            server.starttls()
        
        # 登录
        server.login(self.email_address, self.password)
        
        # 发送邮件
        server.send_message(msg, to_addrs=recipients)
        server.quit()
        
        return {
            'smtp_server': config['server'],
            'recipients_count': len(recipients),
            'sent_at': datetime.now().isoformat()
        }
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """添加附件到邮件"""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            raise Exception(f"添加附件失败 ({filename}): {str(e)}")
    
    def send_html_email(self, to_email: str, subject: str, html_content: str, 
                        plain_text: Optional[str] = None) -> Dict[str, Any]:
        """发送HTML邮件（带纯文本备用）"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加纯文本版本（如果提供）
            if plain_text:
                text_part = MIMEText(plain_text, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # 添加HTML版本
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送
            result = self._send_via_smtp(msg, to_email)
            
            return {
                'success': True,
                'message': 'HTML邮件发送成功',
                'details': {
                    'to': to_email,
                    'subject': subject,
                    'has_plain_text': bool(plain_text),
                    'timestamp': datetime.now().isoformat()
                },
                **result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'HTML邮件发送失败: {str(e)}'
            }
    
    def send_analysis_report(self, to_email: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送邮件分析报告"""
        try:
            # 生成HTML报告
            html_content = self._generate_analysis_html(analysis_data)
            
            # 生成纯文本版本
            plain_content = self._generate_analysis_text(analysis_data)
            
            subject = f"邮件分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            return self.send_html_email(to_email, subject, html_content, plain_content)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'分析报告发送失败: {str(e)}'
            }
    
    def _generate_analysis_html(self, data: Dict[str, Any]) -> str:
        """生成HTML格式的分析报告"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>邮件分析报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .stats {{ background-color: #e8f4fd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .email-item {{ border-left: 3px solid #007acc; padding-left: 15px; margin: 10px 0; }}
                .important {{ color: #d73527; font-weight: bold; }}
                .normal {{ color: #333; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📧 Smart Email AI 分析报告</h1>
                <p>生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
            </div>
            
            <div class="stats">
                <h2>📊 统计概览</h2>
                <ul>
                    <li>分析邮件数量: {data.get('total_emails', 0)} 封</li>
                    <li>重要邮件: {data.get('important_emails', 0)} 封</li>
                    <li>平均正文长度: {data.get('avg_length', 0)} 字符</li>
                    <li>有附件邮件: {data.get('with_attachments', 0)} 封</li>
                </ul>
            </div>
            
            <h2>📝 邮件详情</h2>
        """
        
        # 添加邮件列表
        emails = data.get('emails', [])
        for i, email in enumerate(emails, 1):
            importance_class = "important" if email.get('importance', 0) > 70 else "normal"
            html += f"""
            <div class="email-item">
                <h3 class="{importance_class}">{i}. {email.get('subject', '无主题')}</h3>
                <p><strong>发件人:</strong> {email.get('sender', '未知')}</p>
                <p><strong>时间:</strong> {email.get('date', '未知')}</p>
                <p><strong>正文预览:</strong> {email.get('preview', '')[:200]}...</p>
            </div>
            """
        
        html += """
            <div class="header">
                <p>📱 由 Smart Email AI 系统生成</p>
                <p>🚀 性能优化：缓存系统提供毫秒级响应</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_analysis_text(self, data: Dict[str, Any]) -> str:
        """生成纯文本格式的分析报告"""
        text = f"""
Smart Email AI 分析报告
生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

📊 统计概览:
• 分析邮件数量: {data.get('total_emails', 0)} 封
• 重要邮件: {data.get('important_emails', 0)} 封  
• 平均正文长度: {data.get('avg_length', 0)} 字符
• 有附件邮件: {data.get('with_attachments', 0)} 封

📝 邮件详情:
"""
        
        emails = data.get('emails', [])
        for i, email in enumerate(emails, 1):
            text += f"""
{i}. {email.get('subject', '无主题')}
   发件人: {email.get('sender', '未知')}
   时间: {email.get('date', '未知')}
   正文预览: {email.get('preview', '')[:200]}...

"""
        
        text += """
📱 由 Smart Email AI 系统生成
🚀 性能优化：缓存系统提供毫秒级响应
"""
        
        return text
    
    def test_connection(self) -> Dict[str, Any]:
        """测试邮件服务器连接"""
        try:
            config = self.smtp_config[self.provider]
            
            server = smtplib.SMTP(config['server'], config['port'])
            if config['use_tls']:
                server.starttls()
            
            server.login(self.email_address, self.password)
            server.quit()
            
            return {
                'success': True,
                'message': f'{self.provider} 邮件服务器连接成功',
                'details': {
                    'provider': self.provider,
                    'server': config['server'],
                    'port': config['port'],
                    'email': self.email_address
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'邮件服务器连接失败: {str(e)}',
                'details': {
                    'provider': self.provider,
                    'email': self.email_address
                }
            }

    @classmethod
    def create_custom_sender(cls, email_address: str, password: str) -> 'EmailSender':
        """创建自定义发件人实例
        
        Args:
            email_address: 发件人邮箱地址
            password: 邮箱密码或应用专用密码
            
        Returns:
            EmailSender: 配置好的邮件发送器实例
        """
        return cls(email_address=email_address, password=password, use_default=False)
    
    @classmethod
    def create_default_sender(cls) -> 'EmailSender':
        """创建默认发件人实例（User的iCloud）
        
        Returns:
            EmailSender: 使用默认配置的邮件发送器实例
        """
        return cls(use_default=True)


# 全局邮件发送器实例（需要配置邮箱凭证后才能使用）
# email_sender = EmailSender()  # 需要邮箱凭证
email_sender = None  # 延迟初始化，避免启动时需要凭证 