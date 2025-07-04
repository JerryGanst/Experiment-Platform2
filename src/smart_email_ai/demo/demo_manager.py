"""演示邮件管理器 - 独立的演示功能模块"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from ..interfaces.email_interface import EmailData


@dataclass
class DemoEmailData(EmailData):
    """扩展的演示邮件数据结构"""
    expected_analysis: Optional[Dict] = None
    demo_tags: List[str] = None


class DemoEmailManager:
    """演示邮件管理器 - 处理所有演示相关功能"""
    
    def __init__(self, demo_emails_path: str = "data/demo_emails.json"):
        self.demo_emails_path = demo_emails_path
        self._demo_emails = None
    
    def load_demo_emails(self) -> List[DemoEmailData]:
        """加载演示邮件数据"""
        if self._demo_emails is None:
            self._demo_emails = self._load_demo_emails_from_file()
        return self._demo_emails
    
    def _load_demo_emails_from_file(self) -> List[DemoEmailData]:
        """从文件加载演示邮件"""
        try:
            if not os.path.exists(self.demo_emails_path):
                return self._create_default_demo_emails()
            
            with open(self.demo_emails_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            emails = []
            for email_dict in data.get('emails', []):
                metadata = email_dict.get('metadata', {})
                content = email_dict.get('content', {})
                
                email_data = DemoEmailData(
                    id=email_dict.get('id', ''),
                    sender=metadata.get('sender', ''),
                    subject=metadata.get('subject', ''),
                    body=content.get('body', ''),
                    date=metadata.get('date', ''),
                    category=metadata.get('category'),
                    expected_priority=metadata.get('expected_priority'),
                    expected_analysis=content.get('expected_analysis'),
                    demo_tags=metadata.get('demo_tags', [])
                )
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"❌ 演示邮件加载失败: {e}")
            return self._create_default_demo_emails()
    
    def _create_default_demo_emails(self) -> List[DemoEmailData]:
        """创建默认演示邮件"""
        return [
            DemoEmailData(
                id="default_001",
                sender="demo@example.com",
                subject="演示邮件",
                body="这是一封演示邮件，用于测试系统功能。",
                date=datetime.now().isoformat(),
                category="demo",
                expected_priority=3,
                demo_tags=["default", "basic"]
            )
        ]
    
    def get_demo_email_by_id(self, email_id: str) -> Optional[DemoEmailData]:
        """根据ID获取演示邮件"""
        emails = self.load_demo_emails()
        for email in emails:
            if email.id == email_id:
                return email
        return None
    
    def get_demo_email_by_subject_pattern(self, pattern: str) -> Optional[DemoEmailData]:
        """根据主题模式匹配演示邮件"""
        emails = self.load_demo_emails()
        for email in emails:
            if pattern.lower() in email.subject.lower():
                return email
        return None
    
    def get_demo_emails_by_category(self, category: str) -> List[DemoEmailData]:
        """根据类别获取演示邮件"""
        emails = self.load_demo_emails()
        return [email for email in emails if email.category == category]
    
    def get_demo_emails_by_priority(self, min_priority: int = 3) -> List[DemoEmailData]:
        """根据优先级获取演示邮件"""
        emails = self.load_demo_emails()
        return [email for email in emails if (email.expected_priority or 0) >= min_priority]
    
    def convert_to_legacy_format(self, email_data: DemoEmailData) -> Dict:
        """转换为原有格式（向后兼容）"""
        return {
            "sender": email_data.sender,
            "subject": email_data.subject,
            "body": email_data.body,
            "date": email_data.date,
            "category": email_data.category,
            "expected_priority": email_data.expected_priority
        }
    
    def get_all_demo_emails_legacy_format(self) -> List[Dict]:
        """获取所有演示邮件（原有格式）"""
        emails = self.load_demo_emails()
        return [self.convert_to_legacy_format(email) for email in emails]


class DemoModeManager:
    """演示模式管理器 - 控制演示模式的启用和状态"""
    
    def __init__(self):
        self.demo_enabled = False
        self.demo_email_manager = DemoEmailManager()
    
    def enable_demo_mode(self) -> str:
        """启用演示模式"""
        self.demo_enabled = True
        demo_emails = self.demo_email_manager.load_demo_emails()
        return f"✅ 演示模式已启用！\n📧 加载了 {len(demo_emails)} 封演示邮件\n🎭 现在可以使用演示数据进行测试"
    
    def disable_demo_mode(self) -> str:
        """禁用演示模式"""
        self.demo_enabled = False
        return "❌ 演示模式已禁用，切换到生产模式"
    
    def is_demo_enabled(self) -> bool:
        """检查演示模式是否启用"""
        return self.demo_enabled
    
    def get_demo_status(self) -> Dict:
        """获取演示模式状态"""
        if not self.demo_enabled:
            return {
                'enabled': False,
                'message': '演示模式未启用'
            }
        
        emails = self.demo_email_manager.load_demo_emails()
        return {
            'enabled': True,
            'email_count': len(emails),
            'categories': list(set(email.category for email in emails if email.category)),
            'priority_range': [
                min(email.expected_priority or 0 for email in emails),
                max(email.expected_priority or 0 for email in emails)
            ]
        }


# 全局演示管理器实例
demo_mode_manager = DemoModeManager()
demo_email_manager = DemoEmailManager() 