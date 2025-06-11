"""邮件数据管理接口"""

import json
import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmailData:
    """邮件数据结构"""
    id: str
    sender: str
    subject: str
    body: str
    date: str
    category: Optional[str] = None
    expected_priority: Optional[int] = None
    expected_analysis: Optional[Dict] = None


class EmailDataInterface(ABC):
    """邮件数据管理抽象接口"""
    
    @abstractmethod
    def load_demo_emails(self) -> List[EmailData]:
        """加载演示邮件数据"""
        pass
    
    @abstractmethod
    def load_email_from_file(self, file_path: str) -> str:
        """从文件加载邮件内容"""
        pass
    
    @abstractmethod
    def save_email_analysis(self, email_id: str, analysis: Dict) -> bool:
        """保存邮件分析结果"""
        pass


class JsonEmailDataManager(EmailDataInterface):
    """基于JSON的邮件数据管理器"""
    
    def __init__(self, demo_emails_path: str = "data/demo_emails.json"):
        self.demo_emails_path = demo_emails_path
        self._demo_emails = None
    
    def load_demo_emails(self) -> List[EmailData]:
        """加载演示邮件数据"""
        if self._demo_emails is None:
            self._demo_emails = self._load_demo_emails_from_file()
        return self._demo_emails
    
    def _load_demo_emails_from_file(self) -> List[EmailData]:
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
                
                email_data = EmailData(
                    id=email_dict.get('id', ''),
                    sender=metadata.get('sender', ''),
                    subject=metadata.get('subject', ''),
                    body=content.get('body', ''),
                    date=metadata.get('date', ''),
                    category=metadata.get('category'),
                    expected_priority=metadata.get('expected_priority'),
                    expected_analysis=content.get('expected_analysis')
                )
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"❌ 演示邮件加载失败: {e}")
            return self._create_default_demo_emails()
    
    def _create_default_demo_emails(self) -> List[EmailData]:
        """创建默认演示邮件"""
        return [
            EmailData(
                id="default_001",
                sender="demo@example.com",
                subject="演示邮件",
                body="这是一封演示邮件，用于测试系统功能。",
                date=datetime.now().isoformat(),
                category="demo",
                expected_priority=3
            )
        ]
    
    def load_email_from_file(self, file_path: str) -> str:
        """从文件加载邮件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ 邮件文件加载失败: {e}")
            return ""
    
    def save_email_analysis(self, email_id: str, analysis: Dict) -> bool:
        """保存邮件分析结果"""
        try:
            analysis_file = f"data/analysis_results/{email_id}_analysis.json"
            os.makedirs(os.path.dirname(analysis_file), exist_ok=True)
            
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 分析结果保存失败: {e}")
            return False
    
    def get_demo_email_by_id(self, email_id: str) -> Optional[EmailData]:
        """根据ID获取演示邮件"""
        emails = self.load_demo_emails()
        for email in emails:
            if email.id == email_id:
                return email
        return None
    
    def get_demo_email_by_subject_pattern(self, pattern: str) -> Optional[EmailData]:
        """根据主题模式匹配演示邮件"""
        emails = self.load_demo_emails()
        for email in emails:
            if pattern.lower() in email.subject.lower():
                return email
        return None
    
    def convert_to_legacy_format(self, email_data: EmailData) -> Dict:
        """转换为原有格式（向后兼容）"""
        return {
            "sender": email_data.sender,
            "subject": email_data.subject,
            "body": email_data.body,
            "date": email_data.date
        }
    
    def get_all_demo_emails_legacy_format(self) -> List[Dict]:
        """获取所有演示邮件（原有格式）"""
        emails = self.load_demo_emails()
        return [self.convert_to_legacy_format(email) for email in emails]


# 全局邮件数据管理器实例
email_data_manager = JsonEmailDataManager() 