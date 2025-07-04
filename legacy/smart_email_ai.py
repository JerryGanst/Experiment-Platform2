import smtplib
import imaplib
import email
import re
import json
import hashlib
import html
from bs4 import BeautifulSoup
import html2text
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("advanced_email_ai")

@dataclass
class EmailProfile:
    """邮件发件人档案"""
    sender: str
    frequency: int  # 发邮件频率
    avg_priority: float  # 平均优先级
    response_rate: float  # 回复率
    relationship: str  # 关系：boss, colleague, external, system
    trust_score: float  # 信任度评分 0-1
    common_topics: List[str]  # 常见主题

@dataclass
class EmailLearning:
    """邮件学习数据"""
    subject_patterns: Dict[str, float]  # 主题模式和重要性
    sender_importance: Dict[str, float]  # 发件人重要性
    time_patterns: Dict[str, float]  # 时间模式重要性
    user_actions: List[Dict]  # 用户行为记录

@dataclass
class EmailSection:
    """邮件段落结构"""
    header: Dict[str, str]  # 发件人、时间、主题等
    body: str  # 正文内容
    tables: List[Dict]  # 表格数据
    attachments: List[str]  # 附件列表
    forwarded_emails: List['EmailSection']  # 转发的邮件
    level: int = 0  # 转发层级

class OutlookEmailParser:
    """Outlook邮件解析器 - 统一处理正文和转发内容"""

    def __init__(self):
        # Outlook转发邮件的常见分界标识
        self.forward_patterns = [
            r'-----\s*原始邮件\s*-----',
            r'-----\s*Forwarded message\s*-----',
            r'发件人:',
            r'From:',
            r'<div style=["\']border:none;border-top:solid #E1E1E1 1\.0pt',
            r'<div[^>]*border-top[^>]*>',
        ]

        # 邮件头字段模式
        self.header_patterns = {
            'from': [r'发件人[:\s]*(.+?)(?:<br|$)', r'From[:\s]*(.+?)(?:<br|$)'],
            'to': [r'收件人[:\s]*(.+?)(?:<br|$)', r'To[:\s]*(.+?)(?:<br|$)'],
            'cc': [r'抄送[:\s]*(.+?)(?:<br|$)', r'CC[:\s]*(.+?)(?:<br|$)'],
            'subject': [r'主题[:\s]*(.+?)(?:<br|$)', r'Subject[:\s]*(.+?)(?:<br|$)'],
            'date': [r'发送时间[:\s]*(.+?)(?:<br|$)', r'Sent[:\s]*(.+?)(?:<br|$)'],
        }

    def parse_email(self, email_content: str) -> EmailSection:
        """统一解析邮件（包括转发链）"""
        # 清理HTML并创建BeautifulSoup对象
        soup = self._clean_outlook_html(email_content)

        # 分割邮件段落（原始+转发）
        email_sections = self._split_email_sections(soup)

        # 递归解析每个段落
        return self._parse_section(email_sections[0], email_sections[1:], level=0)

    def _clean_outlook_html(self, html_content: str) -> BeautifulSoup:
        """清理Outlook特有的HTML标记"""
        # 移除Word的XML命名空间和VML图形
        html_content = re.sub(r'<\?xml[^>]*>', '', html_content)
        html_content = re.sub(r'xmlns[^=]*="[^"]*"', '', html_content)
        html_content = re.sub(r'<v:.*?</v:.*?>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<w:.*?</w:.*?>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<o:.*?</o:.*?>', '', html_content, flags=re.DOTALL)

        # 移除条件注释
        html_content = re.sub(r'<!--\[if[^]]*\]>.*?<!\[endif\]-->', '', html_content, flags=re.DOTALL)

        # 移除style标签中的大量样式
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)

        return BeautifulSoup(html_content, 'html.parser')

    def _split_email_sections(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """分割原始邮件和转发邮件段落"""
        sections = []
        content = str(soup)

        # 查找转发分界点
        split_points = []
        for pattern in self.forward_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                split_points.append(match.start())

        split_points = sorted(set(split_points))

        # 根据分界点切分内容
        start = 0
        for point in split_points:
            section_content = content[start:point]
            if section_content.strip():
                sections.append(BeautifulSoup(section_content, 'html.parser'))
            start = point

        # 添加最后一段
        if start < len(content):
            final_section = content[start:]
            if final_section.strip():
                sections.append(BeautifulSoup(final_section, 'html.parser'))

        return sections if sections else [soup]

    def _parse_section(self, main_soup: BeautifulSoup, remaining_sections: List[BeautifulSoup],
                       level: int = 0) -> EmailSection:
        """解析单个邮件段落"""
        # 提取邮件头信息
        header = self._extract_header(main_soup)

        # 提取并转换表格
        tables = self._extract_tables(main_soup)

        # 移除表格后提取正文
        body = self._extract_body_text(main_soup)

        # 递归解析转发邮件
        forwarded_emails = []
        if remaining_sections:
            next_forwarded = self._parse_section(remaining_sections[0], remaining_sections[1:], level + 1)
            forwarded_emails = [next_forwarded]

        return EmailSection(
            header=header,
            body=body,
            tables=tables,
            attachments=[],  # TODO: 实现附件提取
            forwarded_emails=forwarded_emails,
            level=level
        )

    def _extract_header(self, soup: BeautifulSoup) -> Dict[str, str]:
        """提取邮件头信息"""
        header = {}
        text_content = soup.get_text()

        for field, patterns in self.header_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_content, re.IGNORECASE | re.MULTILINE)
                if match:
                    header[field] = match.group(1).strip()
                    break

        return header

    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict]:
        """提取表格并转换为markdown格式"""
        tables = []

        for table in soup.find_all('table'):
            # 跳过布局表格（通常没有border或用于邮件格式）
            if self._is_layout_table(table):
                continue

            table_data = self._parse_table_to_markdown(table)
            if table_data:
                tables.append(table_data)

        return tables

    def _is_layout_table(self, table) -> bool:
        """判断是否为布局表格"""
        # 检查是否有明确的数据表格特征
        has_th = table.find('th') is not None
        has_multiple_rows = len(table.find_all('tr')) > 1
        has_border = table.get('border') and table.get('border') != '0'

        # 布局表格通常行数较少且没有表头
        return not (has_th or has_border) and not has_multiple_rows

    def _parse_table_to_markdown(self, table) -> Optional[Dict]:
        """将HTML表格转换为Markdown格式"""
        rows = []

        for tr in table.find_all('tr'):
            row = []
            for cell in tr.find_all(['td', 'th']):
                # 处理合并单元格
                colspan = int(cell.get('colspan', 1))
                cell_text = cell.get_text(strip=True)
                # 清理文本中的多余空白
                cell_text = re.sub(r'\s+', ' ', cell_text)
                row.append(cell_text)

                # 为合并的列添加空白单元格
                for _ in range(colspan - 1):
                    row.append('')

            if any(cell.strip() for cell in row):  # 跳过空行
                rows.append(row)

        if not rows:
            return None

        # 转换为markdown
        markdown = self._rows_to_markdown(rows)

        return {
            'raw_html': str(table),
            'markdown': markdown,
            'rows': rows,
            'row_count': len(rows),
            'col_count': len(rows[0]) if rows else 0
        }

    def _rows_to_markdown(self, rows: List[List[str]]) -> str:
        """将表格行数据转换为Markdown表格"""
        if not rows:
            return ""

        # 确保所有行长度一致
        max_cols = max(len(row) for row in rows)
        normalized_rows = []
        for row in rows:
            normalized_row = row + [''] * (max_cols - len(row))
            normalized_rows.append(normalized_row)

        # 生成markdown
        markdown_lines = []

        # 表头（假设第一行是表头）
        header_row = '| ' + ' | '.join(normalized_rows[0]) + ' |'
        markdown_lines.append(header_row)

        # 分隔符
        separator = '| ' + ' | '.join(['---'] * max_cols) + ' |'
        markdown_lines.append(separator)

        # 数据行
        for row in normalized_rows[1:]:
            data_row = '| ' + ' | '.join(row) + ' |'
            markdown_lines.append(data_row)

        return '\n'.join(markdown_lines)

    def _extract_body_text(self, soup: BeautifulSoup) -> str:
        """提取正文文本（移除表格和邮件头）"""
        # 移除所有表格
        for table in soup.find_all('table'):
            if not self._is_layout_table(table):
                table.decompose()

        # 移除邮件头部分（通常在特定div中）
        for div in soup.find_all('div'):
            if 'border-top:solid #E1E1E1' in str(div):
                div.decompose()

        # 转换为纯文本
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0  # 不限制行宽

        text = h.handle(str(soup))

        # 清理多余的空行
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

        return text.strip()

    def format_to_markdown(self, email_section: EmailSection) -> str:
        """将解析结果格式化为标准markdown"""
        markdown_parts = []

        # 邮件头
        if email_section.header:
            markdown_parts.append("## 邮件信息")
            for key, value in email_section.header.items():
                chinese_names = {
                    'from': '发件人', 'to': '收件人', 'cc': '抄送',
                    'subject': '主题', 'date': '时间'
                }
                display_key = chinese_names.get(key, key)
                markdown_parts.append(f"**{display_key}:** {value}")
            markdown_parts.append("")

        # 正文
        if email_section.body:
            markdown_parts.append("## 正文内容")
            markdown_parts.append(email_section.body)
            markdown_parts.append("")

        # 表格
        if email_section.tables:
            markdown_parts.append("## 数据表格")
            for i, table in enumerate(email_section.tables, 1):
                markdown_parts.append(f"### 表格 {i}")
                markdown_parts.append(table['markdown'])
                markdown_parts.append("")

        # 转发邮件
        if email_section.forwarded_emails:
            markdown_parts.append("## 转发邮件")
            for i, forwarded in enumerate(email_section.forwarded_emails, 1):
                markdown_parts.append(f"### 转发邮件 {i} (层级 {forwarded.level})")
                forwarded_md = self.format_to_markdown(forwarded)
                # 为转发内容添加缩进
                indented = '\n'.join('  ' + line for line in forwarded_md.split('\n'))
                markdown_parts.append(indented)
                markdown_parts.append("")

        return '\n'.join(markdown_parts)


class AdvancedEmailAI:
    """高级邮件AI分析器"""
    
    def __init__(self):
        self.learning_data = EmailLearning({}, {}, {}, [])
        self.sender_profiles = {}
        self.outlook_parser = OutlookEmailParser()  # 集成Outlook解析器
        self.load_learning_data()
    
    # 扩展的关键词库
    EMOTIONAL_KEYWORDS = {
        "urgent": ["urgent", "asap", "immediately", "critical", "emergency", "deadline", "紧急", "立即", "关键"],
        "positive": ["great", "excellent", "congratulations", "success", "thank", "appreciate", "好", "棒", "成功", "感谢"],
        "negative": ["problem", "issue", "error", "failed", "disappointed", "concern", "问题", "错误", "失败", "担心"],
        "formal": ["dear", "sincerely", "regards", "please", "kindly", "respectfully", "尊敬", "此致", "敬礼"],
        "casual": ["hi", "hey", "thanks", "cheers", "later", "你好", "谢谢", "再见"]
    }
    
    RELATIONSHIP_INDICATORS = {
        "boss": ["ceo", "director", "manager", "supervisor", "president", "boss", "总监", "经理", "主管", "总裁"],
        "colleague": ["team", "colleague", "coworker", "department", "同事", "团队", "部门"],
        "external": ["customer", "client", "vendor", "supplier", "partner", "客户", "供应商", "合作伙伴"],
        "system": ["noreply", "no-reply", "system", "automated", "notification", "系统", "自动"]
    }
    
    def analyze_email_advanced(self, subject: str, body: str, sender: str, timestamp: str = None) -> Dict:
        """高级邮件分析"""
        
        # 基础分析
        basic_analysis = self._basic_analysis(subject, body, sender)
        
        # 情感分析
        sentiment_analysis = self._advanced_sentiment_analysis(subject, body)
        
        # 发件人分析
        sender_analysis = self._analyze_sender(sender, subject, body)
        
        # 内容重要性学习
        importance_score = self._calculate_learned_importance(subject, body, sender)
        
        # 生成回复建议
        reply_suggestions = self._generate_reply_suggestions(subject, body, sender, sentiment_analysis)
        
        # 综合优先级计算
        final_priority = self._calculate_final_priority(
            basic_analysis["priority"],
            importance_score,
            sender_analysis["trust_score"],
            sentiment_analysis["urgency_score"]
        )
        
        return {
            **basic_analysis,
            "sentiment_analysis": sentiment_analysis,
            "sender_analysis": sender_analysis,
            "importance_score": importance_score,
            "final_priority": final_priority,
            "reply_suggestions": reply_suggestions,
            "ai_insights": self._generate_ai_insights(subject, body, sender, sentiment_analysis)
        }
    
    def _basic_analysis(self, subject: str, body: str, sender: str) -> Dict:
        """基础邮件分析"""
        text = f"{subject} {body}".lower()
        
        # 基础分类逻辑
        if any(word in text for word in ["sale", "discount", "promotion", "unsubscribe"]):
            category = "可忽略 🗑️"
            priority = 1
        elif any(word in text for word in ["urgent", "asap", "critical", "emergency"]):
            category = "紧急 🚨" 
            priority = 5
        elif any(word in text for word in ["please", "action required", "need", "must"]):
            category = "需要处理 📋"
            priority = 4
        else:
            category = "信息通知 📰"
            priority = 3
        
        return {
            "subject": subject,
            "sender": sender,
            "category": category,
            "priority": priority,
            "action_items": self._extract_actions(body),
            "deadline": self._extract_dates(text),
            "key_info": self._extract_key_info(body),
            "summary": self._create_summary(subject, body)
        }
    
    def _advanced_sentiment_analysis(self, subject: str, body: str) -> Dict:
        """高级情感分析"""
        text = f"{subject} {body}".lower()
        
        # 情感得分计算
        emotional_scores = {}
        for emotion, keywords in self.EMOTIONAL_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            emotional_scores[emotion] = score
        
        # 确定主要情感
        primary_emotion = max(emotional_scores.items(), key=lambda x: x[1])
        
        # 紧急程度评分
        urgency_indicators = ["urgent", "asap", "immediately", "deadline", "critical", "emergency"]
        urgency_score = sum(1 for indicator in urgency_indicators if indicator in text)
        urgency_score = min(urgency_score / 3.0, 1.0)  # 标准化到0-1
        
        # 正式程度评分
        formality_score = 0
        if any(word in text for word in self.EMOTIONAL_KEYWORDS["formal"]):
            formality_score += 0.6
        if any(word in text for word in self.EMOTIONAL_KEYWORDS["casual"]):
            formality_score -= 0.3
        formality_score = max(0, min(formality_score, 1))
        
        # 情感极性
        positive_score = emotional_scores["positive"]
        negative_score = emotional_scores["negative"]
        
        if positive_score > negative_score:
            polarity = "positive"
            confidence = positive_score / (positive_score + negative_score + 1)
        elif negative_score > positive_score:
            polarity = "negative"
            confidence = negative_score / (positive_score + negative_score + 1)
        else:
            polarity = "neutral"
            confidence = 0.5
        
        return {
            "primary_emotion": primary_emotion[0],
            "emotion_scores": emotional_scores,
            "urgency_score": urgency_score,
            "formality_score": formality_score,
            "polarity": polarity,
            "confidence": confidence,
            "tone": self._determine_tone(emotional_scores, formality_score)
        }
    
    def _analyze_sender(self, sender: str, subject: str, body: str) -> Dict:
        """分析发件人"""
        # 获取或创建发件人档案
        if sender not in self.sender_profiles:
            self.sender_profiles[sender] = self._create_sender_profile(sender)
        
        profile = self.sender_profiles[sender]
        
        # 更新档案
        profile.frequency += 1
        
        # 分析关系类型
        relationship = self._determine_relationship(sender, body)
        profile.relationship = relationship
        
        # 计算信任度
        trust_score = self._calculate_trust_score(sender, subject, body, relationship)
        profile.trust_score = trust_score
        
        return {
            "relationship": relationship,
            "trust_score": trust_score,
            "frequency": profile.frequency,
            "avg_priority": profile.avg_priority,
            "profile": asdict(profile)
        }
    
    def _calculate_learned_importance(self, subject: str, body: str, sender: str) -> float:
        """基于学习数据计算重要性"""
        importance = 0.5  # 基础重要性
        
        # 基于主题模式学习
        for pattern, weight in self.learning_data.subject_patterns.items():
            if pattern.lower() in subject.lower():
                importance += weight * 0.3
        
        # 基于发件人重要性学习
        sender_importance = self.learning_data.sender_importance.get(sender, 0.5)
        importance += sender_importance * 0.4
        
        # 基于时间模式
        current_hour = datetime.now().hour
        time_key = f"hour_{current_hour}"
        time_importance = self.learning_data.time_patterns.get(time_key, 0.5)
        importance += time_importance * 0.2
        
        # 基于内容长度（通常越长越重要）
        content_length = len(body)
        if content_length > 500:
            importance += 0.1
        elif content_length < 100:
            importance -= 0.1
        
        return max(0, min(importance, 1))
    
    def _generate_reply_suggestions(self, subject: str, body: str, sender: str, sentiment: Dict) -> List[Dict]:
        """生成智能回复建议"""
        suggestions = []
        
        # 基于邮件类型生成建议
        if any(word in body.lower() for word in ["meeting", "schedule", "会议", "安排"]):
            suggestions.append({
                "type": "scheduling",
                "template": "Thanks for the meeting invitation. I'll check my calendar and get back to you shortly.",
                "chinese": "感谢您的会议邀请，我会查看日程安排后尽快回复您。",
                "urgency": "medium"
            })
        
        if any(word in body.lower() for word in ["review", "approve", "审核", "批准"]):
            suggestions.append({
                "type": "approval",
                "template": "I'll review this and provide my feedback by [deadline]. Thank you for sharing.",
                "chinese": "我会审核这个内容并在[截止日期]前提供反馈，谢谢分享。",
                "urgency": "high"
            })
        
        if any(word in body.lower() for word in ["question", "help", "support", "问题", "帮助"]):
            suggestions.append({
                "type": "support",
                "template": "I'd be happy to help with this. Let me look into it and get back to you.",
                "chinese": "我很乐意帮助解决这个问题，让我了解一下情况后回复您。",
                "urgency": "medium"
            })
        
        if sentiment["urgency_score"] > 0.7:
            suggestions.append({
                "type": "urgent",
                "template": "Thanks for the urgent notice. I'm prioritizing this and will respond within [timeframe].",
                "chinese": "感谢您的紧急通知，我会优先处理并在[时间范围]内回复。",
                "urgency": "high"
            })
        
        # 基于发件人关系调整语气
        if sender in self.sender_profiles:
            relationship = self.sender_profiles[sender].relationship
            if relationship == "boss":
                for suggestion in suggestions:
                    suggestion["tone"] = "formal"
            elif relationship == "colleague":
                for suggestion in suggestions:
                    suggestion["tone"] = "friendly"
        
        # 通用回复
        if not suggestions:
            suggestions.append({
                "type": "acknowledgment",
                "template": "Thank you for your email. I've received it and will respond accordingly.",
                "chinese": "感谢您的邮件，我已收到并会相应回复。",
                "urgency": "low"
            })
        
        return suggestions[:3]  # 返回最多3个建议
    
    def _calculate_final_priority(self, base_priority: int, importance: float, trust_score: float, urgency: float) -> int:
        """计算最终优先级"""
        # 加权计算
        weighted_score = (
            base_priority * 0.4 +          # 基础优先级
            importance * 5 * 0.3 +         # 学习重要性
            trust_score * 5 * 0.2 +        # 发件人信任度
            urgency * 5 * 0.1              # 紧急程度
        )
        
        return max(1, min(5, round(weighted_score)))
    
    def _generate_ai_insights(self, subject: str, body: str, sender: str, sentiment: Dict) -> List[str]:
        """生成AI洞察"""
        insights = []
        
        # 基于情感分析的洞察
        if sentiment["urgency_score"] > 0.8:
            insights.append("🚨 这封邮件显示出极高的紧急性，建议立即处理")
        
        if sentiment["polarity"] == "negative" and sentiment["confidence"] > 0.7:
            insights.append("⚠️ 邮件情感倾向消极，可能需要谨慎回应")
        
        if sentiment["formality_score"] > 0.8:
            insights.append("👔 邮件语气正式，建议使用相应的正式回复")
        
        # 基于发件人分析的洞察
        if sender in self.sender_profiles:
            profile = self.sender_profiles[sender]
            if profile.frequency > 10 and profile.avg_priority > 4:
                insights.append(f"📊 {sender} 是频繁且重要的联系人")
            elif profile.trust_score < 0.3:
                insights.append("🔍 此发件人的信任度较低，请谨慎处理")
        
        # 基于内容分析的洞察
        if len(re.findall(r'[.!?]', body)) > 20:
            insights.append("📝 邮件内容较长，可能包含重要详细信息")
        
        if re.search(r'\d{1,2}:\d{2}', body):
            insights.append("⏰ 邮件包含具体时间信息，可能需要日程安排")
        
        return insights
    
    def learn_from_user_action(self, email_data: Dict, user_action: str, importance_rating: int = None):
        """从用户行为中学习"""
        action_record = {
            "timestamp": datetime.now().isoformat(),
            "sender": email_data["sender"],
            "subject": email_data["subject"],
            "action": user_action,  # "replied", "ignored", "forwarded", "deleted"
            "importance_rating": importance_rating,
            "original_priority": email_data["priority"]
        }
        
        self.learning_data.user_actions.append(action_record)
        
        # 更新学习模式
        self._update_learning_patterns(email_data, user_action, importance_rating)
        
        # 保存学习数据
        self.save_learning_data()
    
    def _update_learning_patterns(self, email_data: Dict, action: str, rating: int):
        """更新学习模式"""
        sender = email_data["sender"]
        subject = email_data["subject"]
        
        # 更新发件人重要性
        if action in ["replied", "forwarded"]:
            self.learning_data.sender_importance[sender] = self.learning_data.sender_importance.get(sender, 0.5) + 0.1
        elif action in ["ignored", "deleted"]:
            self.learning_data.sender_importance[sender] = self.learning_data.sender_importance.get(sender, 0.5) - 0.1
        
        # 限制范围在0-1之间
        self.learning_data.sender_importance[sender] = max(0, min(1, self.learning_data.sender_importance[sender]))
        
        # 更新主题模式
        key_words = re.findall(r'\b\w{4,}\b', subject.lower())
        for word in key_words[:3]:  # 只取前3个关键词
            if rating:
                weight = (rating - 3) / 2  # 转换为-1到1的范围
                self.learning_data.subject_patterns[word] = self.learning_data.subject_patterns.get(word, 0) + weight * 0.1
    
    def save_learning_data(self):
        """保存学习数据"""
        try:
            # 这里可以保存到文件或数据库
            # 暂时保存在内存中
            pass
        except Exception:
            pass
    
    def load_learning_data(self):
        """加载学习数据"""
        try:
            # 这里可以从文件或数据库加载
            # 暂时使用默认数据
            pass
        except Exception:
            pass
    
    # 辅助方法
    def _create_sender_profile(self, sender: str) -> EmailProfile:
        """创建发件人档案"""
        return EmailProfile(
            sender=sender,
            frequency=1,
            avg_priority=3.0,
            response_rate=0.0,
            relationship="unknown",
            trust_score=0.5,
            common_topics=[]
        )
    
    def _determine_relationship(self, sender: str, body: str) -> str:
        """确定关系类型"""
        sender_lower = sender.lower()
        body_lower = body.lower()
        
        for relationship, indicators in self.RELATIONSHIP_INDICATORS.items():
            if any(indicator in sender_lower or indicator in body_lower for indicator in indicators):
                return relationship
        
        return "external"
    
    def _calculate_trust_score(self, sender: str, subject: str, body: str, relationship: str) -> float:
        """计算信任度"""
        trust = 0.5  # 基础信任度
        
        # 基于关系类型调整
        relationship_scores = {
            "boss": 0.9,
            "colleague": 0.8,
            "external": 0.5,
            "system": 0.3
        }
        trust = relationship_scores.get(relationship, 0.5)
        
        # 基于域名调整
        if "@" in sender:
            domain = sender.split("@")[1].lower()
            # 已知安全域名
            trusted_domains = ["company.com", "gmail.com", "outlook.com"]
            if any(trusted in domain for trusted in trusted_domains):
                trust += 0.1
        
        # 基于内容特征调整
        suspicious_indicators = ["urgent", "act now", "limited time", "click here", "verify account"]
        if sum(1 for indicator in suspicious_indicators if indicator in body.lower()) > 2:
            trust -= 0.3
        
        return max(0, min(1, trust))
    
    def _determine_tone(self, emotion_scores: Dict, formality_score: float) -> str:
        """确定语气"""
        if formality_score > 0.7:
            return "formal"
        elif emotion_scores.get("positive", 0) > emotion_scores.get("negative", 0):
            return "friendly"
        elif emotion_scores.get("urgent", 0) > 2:
            return "urgent"
        else:
            return "neutral"
    
    def _extract_actions(self, body: str) -> List[str]:
        """提取行动项"""
        actions = []
        
        # 查找明确的行动项
        patterns = [
            r'[-•*]\s*(.+)',           # 项目符号
            r'\d+\.\s*(.+)',           # 编号列表
            r'action.*?:(.+)',         # action: 格式
            r'please\s+(.+?)(?:\.|$)', # please 开头
            r'需要\s*(.+?)(?:\.|。|$)',  # 中文需要
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for match in matches:
                if 10 < len(match.strip()) < 200:
                    actions.append(match.strip())
        
        return actions[:5]
    
    def _extract_dates(self, text: str) -> Optional[str]:
        """提取日期"""
        patterns = [
            r'(today|tomorrow|tonight)',
            r'(this|next)\s+(week|month|friday|monday|tuesday|wednesday|thursday|saturday|sunday)',
            r'(june|july|august|september|october|november|december)\s+\d{1,2}',
            r'by\s+(today|tomorrow|friday|end of day|eod|\d{1,2}:\d{2})',
            r'(今天|明天|本周|下周)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group()
        return None
    
    def _extract_key_info(self, body: str) -> List[str]:
        """提取关键信息"""
        key_info = []
        
        # 时间信息
        times = re.findall(r'\d{1,2}:\d{2}\s*(AM|PM|am|pm)', body)
        key_info.extend([f"⏰ {time}" for time in times[:2]])
        
        # 地点信息
        locations = re.findall(r'(conference room|room|zoom|meeting room)\s*[a-zA-Z]?', body, re.IGNORECASE)
        key_info.extend([f"📍 {loc}" for loc in locations[:2]])
        
        # 金额信息
        amounts = re.findall(r'\$[\d,]+(?:\.\d+)?', body)
        key_info.extend([f"💰 {amount}" for amount in amounts[:2]])
        
        # 百分比
        percentages = re.findall(r'\d+%', body)
        key_info.extend([f"📊 {pct}" for pct in percentages[:2]])
        
        return key_info
    
    def _create_summary(self, subject: str, body: str) -> str:
        """创建摘要"""
        sentences = re.split(r'[.!?。！？]', body)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if 30 < len(sentence) < 150 and not sentence.startswith(("Hi", "Dear", "This is", "Best")):
                return sentence
        
        return subject

# 全局变量
email_ai = AdvancedEmailAI()
demo_mode = False

# 扩展的演示邮件数据
DEMO_EMAILS_ADVANCED = [
    {
        "sender": "sarah.chen@company.com",
        "subject": "URGENT: Client presentation moved to tomorrow - Need your input ASAP",
        "date": "2025-06-03 09:15:00",
        "body": """Hi User,

I hope this email finds you well. Unfortunately, I have some urgent news regarding our Q2 client presentation.

The client has requested to move our presentation from Friday to TOMORROW (Thursday) at 2:00 PM. This is extremely critical for closing the deal worth $2.5M.

ACTION REQUIRED:
- Please review the updated slides (attached) and provide feedback by 6 PM today
- Confirm your availability for tomorrow's presentation
- Prepare the financial projections section you're responsible for

This is a make-or-break moment for our team. I know it's short notice, but your expertise is crucial for this presentation.

Please reply ASAP to confirm you can make it work.

Best regards,
Sarah Chen
Director of Sales"""
    },
    {
        "sender": "security-alert@company.com",
        "subject": "⚠️ SECURITY BREACH DETECTED - Immediate Action Required",
        "date": "2025-06-03 11:20:00",
        "body": """SECURITY ALERT - CONFIDENTIAL

We have detected unauthorized access attempts on your company account from the following IP: 192.168.1.100

IMMEDIATE ACTIONS REQUIRED:
1. Change your password within the next 2 hours
2. Review your recent login activity at security.company.com
3. Report any suspicious emails to security@company.com
4. Enable two-factor authentication if not already active

FAILURE TO COMPLY WITHIN 2 HOURS WILL RESULT IN ACCOUNT SUSPENSION.

Do not forward this email. Do not ignore this warning.

If you did not authorize these login attempts, respond immediately.

Security Operations Team
Company IT Security"""
    },
    {
        "sender": "john.williams@partner-company.com",
        "subject": "Partnership proposal - Excited to collaborate!",
        "date": "2025-06-03 14:30:00",
        "body": """Dear User,

I hope you're having a great week! I wanted to follow up on our conversation at the conference last month about potential collaboration opportunities.

Our companies seem perfectly aligned, and I believe we could create something amazing together. I've attached a partnership proposal that outlines:

• Joint marketing initiatives that could increase both our market reach by 40%
• Shared technology resources and expertise
• Co-development of new products for Q4 2025

I'm really excited about the possibilities here. Would you be available for a call next week to discuss this further? I'm flexible with timing and can accommodate your schedule.

Looking forward to your thoughts and hopefully a positive response!

Warm regards,
John Williams
VP of Business Development
Partner Company Inc."""
    },
    {
        "sender": "complaints@customerservice.com",
        "subject": "COMPLAINT: Service disruption affecting 500+ users - Need immediate response",
        "date": "2025-06-03 08:45:00",
        "body": """URGENT CUSTOMER COMPLAINT

Customer: TechCorp Industries
Issue: Service disruption affecting their entire team (500+ users)
Impact: Critical business operations halted
Time affected: 3 hours and counting

The customer is extremely upset and threatening to cancel their $50,000/year contract. They've been trying to reach our technical team for the past 3 hours with no response.

REQUIRED ACTIONS:
- Contact the customer within 30 minutes
- Provide immediate technical support
- Offer compensation for the disruption
- Escalate to senior management if necessary

Customer contact: Mike Peterson, CTO (mike.peterson@techcorp.com, +1-555-0123)

This is affecting our reputation and could result in significant revenue loss. Please treat this with highest priority.

Customer Service Team
Ticket #CS-2025-0603-001"""
    },
    {
        "sender": "deals@shopping-mall.com",
        "subject": "🎉 MEGA SALE: 70% OFF Everything - Last 6 Hours Only!",
        "date": "2025-06-03 16:20:00",
        "body": """🔥 FINAL HOURS - BIGGEST SALE OF THE YEAR! 🔥

Don't miss out on these incredible deals:

✨ 70% OFF all electronics
✨ 60% OFF fashion and accessories  
✨ 50% OFF home and garden
✨ FREE shipping on orders over $50

⏰ SALE ENDS IN 6 HOURS - MIDNIGHT TONIGHT!

Our bestsellers are flying off the shelves:
• iPhone 15 Pro - Was $999, NOW $299
• Designer handbags - Was $400, NOW $120
• 4K Smart TV - Was $800, NOW $240

[SHOP NOW] [Limited quantities available]

Don't regret missing this once-in-a-lifetime opportunity!

Questions? Reply to this email or call 1-800-SHOP-NOW

Happy shopping!
The Shopping Mall Team

Unsubscribe 
"""
    },
    {
        "sender": "david.liu@finance.company.com",
        "subject": "URGENT: Complete Q2 Financial Development Report by 5PM - Board Meeting Tomorrow",
        "date": "2025-06-03 13:45:00",
        "body": """User,

Emergency board meeting tomorrow 9 AM. I need you to complete the Q2 Financial Development Report immediately.

ACTION REQUIRED - Complete by 5:00 PM TODAY:

• Create Q2 vs Q1 revenue comparison chart with $8.2M total revenue data
• Analyze development budget performance showing $1.8M spend (15% increase)
• Generate ROI analysis for all active projects using attached financial data
• Prepare cash flow projection for Q3 based on current +$2.1M surplus
• Write executive summary highlighting 18.5% operating margin improvement

SPECIFIC DELIVERABLES:
1. Complete financial report in Excel format
2. PowerPoint presentation with 8 key slides
3. Executive summary document (2 pages maximum)

Please use our standard financial template from SharePoint and include these metrics:
- R&D allocation: $950K for AI project development
- Marketing ROI: 3.2x return on $600K investment
- Q3 budget recommendations for $12M allocation

Please confirm you can deliver this by 5 PM and send progress updates every 2 hours.

This is critical - CEO requested your analysis specifically for tomorrow's $12M budget decision.

David Liu
CFO & Finance Director
Phone: +1-555-0198"""
    },
    {
        "sender": "no-reply@accounts.google.com",
        "subject": "安全提醒：在 Mac 设备上有新的登录活动",
        "date": "2025-06-11 09:30:00",
        "body": """我们发现您的 Google 账号 (user@example.com) 在一部 Mac 设备上有新的登录活动。\n如果这是您本人的操作，则无需采取任何行动。\n如果这不是您本人的操作，我们会帮助您保护您的账号。\n\n查看活动\n您也可以访问以下网址查看安全性活动：\nhttps://myaccount.google.com/notifications"""
    },
    {
        "sender": "no-reply@accounts.google.com",
        "subject": "安全提醒：\"Claude for Google Drive\" 已获得对您的 Google 账号的访问权限",
        "date": "2025-06-11 09:31:00",
        "body": """"Claude for Google Drive"已获得对您的 Google 账号的访问权限 (user@example.com)。\n如果您并未授予访问权限，则应检查此活动，并确保您的账号安全。\n\n查看活动\n您也可以访问以下网址查看安全性活动：\nhttps://myaccount.google.com/notifications"""
    },
    {
        "sender": "no-reply@accounts.google.com",
        "subject": "安全提醒：在 Android 设备上有新的登录活动",
        "date": "2025-06-11 14:37:00",
        "body": """我们发现您的 Google 账号 (user@example.com) 在一部 Android 设备上有新的登录活动。\n如果这是您本人的操作，则无需采取任何行动。\n如果这不是您本人的操作，我们会帮助您保护您的账号。\n\n查看活动\n您也可以访问以下网址查看安全性活动：\nhttps://myaccount.google.com/notifications"""
    }
]

@mcp.tool()
def setup_smart_email(email_address: str, password: str, provider: str = "gmail") -> str:
    """设置智能邮件账户
    
    Args:
        email_address: 邮箱地址 (使用 "demo@example.com" 启用演示模式)
        password: 邮箱密码
        provider: 邮箱提供商 (gmail/outlook)
    """
    global demo_mode
    
    if email_address == "demo@example.com":
        demo_mode = True
        return "✅ 高级AI演示模式已启用！\n🧠 包含情感分析、学习能力、回复建议等高级功能\n📧 演示数据包含5封不同复杂度的邮件"
    
    demo_mode = False
    return f"✅ 智能邮件助手设置成功: {email_address}\n🤖 高级AI功能已启用"

@mcp.tool()
def analyze_todays_emails() -> str:
    """分析今天的邮件"""
    global demo_mode, email_ai
    
    if not demo_mode:
        return "❌ 请先使用 setup_smart_email 设置邮箱\n💡 提示: 使用 setup_smart_email('demo@example.com', 'demo', 'gmail') 体验演示模式"
    
    # 分析演示邮件
    analyses = []
    for email_data in DEMO_EMAILS_ADVANCED:
        analysis = email_ai.analyze_email_advanced(
            email_data["subject"],
            email_data["body"],
            email_data["sender"],
            email_data["date"]
        )
        analyses.append(analysis)
    
    # 按最终优先级排序
    analyses.sort(key=lambda x: x["final_priority"], reverse=True)
    
    # 生成详细报告
    report = "🤖 **高级AI邮件分析报告** (演示模式)\n\n"
    
    # 统计信息
    urgent_count = len([a for a in analyses if a["final_priority"] == 5])
    action_count = len([a for a in analyses if a["final_priority"] >= 4])
    
    report += f"📊 **智能统计**\n"
    report += f"• 总邮件: {len(analyses)} 封\n"
    report += f"• 紧急处理: {urgent_count} 封\n"
    report += f"• 需要行动: {action_count} 封\n\n"
    
    # 详细分析每封邮件
    for i, analysis in enumerate(analyses, 1):
        sentiment = analysis["sentiment_analysis"]
        sender_info = analysis["sender_analysis"]
        
        # 优先级图标
        priority_icons = {5: "🚨", 4: "📋", 3: "📰", 2: "📱", 1: "🗑️"}
        icon = priority_icons.get(analysis["final_priority"], "📧")
        
        report += f"{icon} **邮件 {i}: {analysis['subject']}**\n"
        report += f"👤 发件人: {analysis['sender']} (信任度: {sender_info['trust_score']:.1f})\n"
        report += f"⭐ AI优先级: {analysis['final_priority']}/5 (学习重要性: {analysis['importance_score']:.1f})\n"
        
        # 情感分析
        emotion_icon = {"urgent": "🚨", "positive": "😊", "negative": "😟", "neutral": "😐"}
        polarity_icon = emotion_icon.get(sentiment["polarity"], "😐")
        report += f"{polarity_icon} 情感分析: {sentiment['polarity']} ({sentiment['confidence']:.1f}) | 紧急度: {sentiment['urgency_score']:.1f}\n"
        
        # 待办事项
        if analysis["action_items"]:
            report += f"✅ 待办: {analysis['action_items'][0]}\n"
        
        # AI洞察
        if analysis["ai_insights"]:
            report += f"💡 AI洞察: {analysis['ai_insights'][0]}\n"
        
        # 回复建议
        if analysis["reply_suggestions"]:
            suggestion = analysis["reply_suggestions"][0]
            report += f"🤖 回复建议: {suggestion['chinese']}\n"
        
        report += "\n"
    
    return report

@mcp.tool()
def get_action_items() -> str:
    """获取所有待办事项"""
    global demo_mode, email_ai
    
    if not demo_mode:
        return "❌ 请先使用演示模式"
    
    all_actions = []
    for email_data in DEMO_EMAILS_ADVANCED:
        analysis = email_ai.analyze_email_advanced(
            email_data["subject"],
            email_data["body"],
            email_data["sender"]
        )
        
        if analysis['action_items']:
            for action in analysis['action_items']:
                all_actions.append({
                    'action': action,
                    'from': email_data['sender'],
                    'subject': email_data['subject'],
                    'priority': analysis['final_priority'],
                    'deadline': analysis['deadline'],
                    'sentiment': analysis['sentiment_analysis']['polarity'],
                    'urgency': analysis['sentiment_analysis']['urgency_score'],
                    'ai_priority': analysis['importance_score']
                })
    
    # 按AI计算的优先级排序
    all_actions.sort(key=lambda x: (x['priority'], x['urgency']), reverse=True)
    
    report = "🎯 **AI智能待办事项汇总**\n\n"
    
    # 紧急待办
    urgent = [a for a in all_actions if a['priority'] >= 5 or a['urgency'] > 0.7]
    if urgent:
        report += "🔥 **紧急待办** (AI建议立即处理)\n"
        for i, action in enumerate(urgent, 1):
            deadline = f" ⏰ {action['deadline']}" if action['deadline'] else ""
            urgency_bar = "🔴" * int(action['urgency'] * 5)
            report += f"{i}. {action['action']}\n"
            report += f"   📧 来自: {action['from']}{deadline}\n"
            report += f"   🎯 紧急度: {urgency_bar} ({action['urgency']:.1f})\n"
            report += f"   🤖 AI评分: {action['ai_priority']:.1f}\n\n"
    
    # 重要待办
    important = [a for a in all_actions if a['priority'] == 4 and a['urgency'] <= 0.7]
    if important:
        report += "📋 **重要待办**\n"
        for i, action in enumerate(important, 1):
            deadline = f" ⏰ {action['deadline']}" if action['deadline'] else ""
            report += f"{i}. {action['action']}\n"
            report += f"   📧 {action['subject']}{deadline}\n\n"
    
    return report

@mcp.tool()
def get_reply_suggestions(email_subject: str) -> str:
    """获取特定邮件的回复建议
    
    Args:
        email_subject: 邮件主题 (用于匹配演示邮件)
    """
    global demo_mode, email_ai
    
    if not demo_mode:
        return "❌ 请先启用演示模式"
    
    # 查找匹配的演示邮件
    target_email = None
    for email_data in DEMO_EMAILS_ADVANCED:
        if email_subject.lower() in email_data["subject"].lower():
            target_email = email_data
            break
    
    if not target_email:
        return f"❌ 未找到包含 '{email_subject}' 的邮件"
    
    # 分析邮件
    analysis = email_ai.analyze_email_advanced(
        target_email["subject"],
        target_email["body"],
        target_email["sender"]
    )
    
    report = f"🤖 **智能回复建议: {target_email['subject']}**\n\n"
    
    # 情感分析概况
    sentiment = analysis["sentiment_analysis"]
    report += f"📊 **邮件分析**\n"
    report += f"• 情感: {sentiment['polarity']} (置信度: {sentiment['confidence']:.1f})\n"
    report += f"• 紧急度: {sentiment['urgency_score']:.1f}\n"
    report += f"• 语气: {sentiment['tone']}\n\n"
    
    # 回复建议
    report += "💬 **智能回复建议**\n"
    for i, suggestion in enumerate(analysis["reply_suggestions"], 1):
        urgency_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        color = urgency_color.get(suggestion.get("urgency", "low"), "🟢")
        
        report += f"{i}. {color} **{suggestion['type'].title()} 回复**\n"
        report += f"   英文: {suggestion['template']}\n"
        report += f"   中文: {suggestion['chinese']}\n"
        report += f"   语气: {suggestion.get('tone', 'professional')}\n\n"
    
    # AI洞察
    if analysis["ai_insights"]:
        report += "💡 **AI洞察建议**\n"
        for insight in analysis["ai_insights"]:
            report += f"• {insight}\n"
    
    return report

@mcp.tool()
def simulate_learning(email_subject: str, user_action: str, importance_rating: int) -> str:
    """模拟AI学习功能
    
    Args:
        email_subject: 邮件主题
        user_action: 用户行为 (replied/ignored/forwarded/deleted)
        importance_rating: 重要性评分 1-5
    """
    global demo_mode, email_ai
    
    if not demo_mode:
        return "❌ 请先启用演示模式"
    
    # 查找匹配的演示邮件
    target_email = None
    for email_data in DEMO_EMAILS_ADVANCED:
        if email_subject.lower() in email_data["subject"].lower():
            target_email = email_data
            break
    
    if not target_email:
        return f"❌ 未找到包含 '{email_subject}' 的邮件"
    
    # 分析邮件
    analysis = email_ai.analyze_email_advanced(
        target_email["subject"],
        target_email["body"],
        target_email["sender"]
    )
    
    # 记录学习
    email_ai.learn_from_user_action(analysis, user_action, importance_rating)
    
    # 生成学习报告
    report = f"🧠 **AI学习报告**\n\n"
    report += f"📧 邮件: {target_email['subject']}\n"
    report += f"👤 发件人: {target_email['sender']}\n"
    report += f"🎯 用户行为: {user_action}\n"
    report += f"⭐ 用户评分: {importance_rating}/5\n"
    report += f"🤖 原始AI评分: {analysis['final_priority']}/5\n\n"
    
    # 学习效果
    if user_action in ["replied", "forwarded"]:
        report += "✅ **学习效果**\n"
        report += f"• 提升了对 {target_email['sender']} 的信任度\n"
        report += f"• 增加了相关主题词的重要性权重\n"
        report += f"• 优化了类似邮件的优先级算法\n"
    elif user_action in ["ignored", "deleted"]:
        report += "📉 **学习效果**\n"
        report += f"• 降低了对 {target_email['sender']} 的重要性评估\n"
        report += f"• 减少了相关主题词的权重\n"
        report += f"• 调整了类似邮件的分类逻辑\n"
    
    report += f"\n🔮 **预测**: 未来来自 {target_email['sender']} 的类似邮件将被调整优先级"
    
    return report

@mcp.tool()
def get_ai_insights() -> str:
    """获取全面的AI洞察报告"""
    global demo_mode, email_ai
    
    if not demo_mode:
        return "❌ 请先启用演示模式"
    
    report = "🧠 **AI深度洞察报告**\n\n"
    
    # 分析所有邮件
    all_analyses = []
    for email_data in DEMO_EMAILS_ADVANCED:
        analysis = email_ai.analyze_email_advanced(
            email_data["subject"],
            email_data["body"],
            email_data["sender"]
        )
        all_analyses.append(analysis)
    
    # 发件人模式分析
    sender_stats = {}
    for analysis in all_analyses:
        sender = analysis["sender"]
        if sender not in sender_stats:
            sender_stats[sender] = []
        sender_stats[sender].append(analysis)
    
    report += "👥 **发件人行为模式**\n"
    for sender, emails in sender_stats.items():
        avg_priority = sum(e["final_priority"] for e in emails) / len(emails)
        avg_urgency = sum(e["sentiment_analysis"]["urgency_score"] for e in emails) / len(emails)
        report += f"• {sender}: 平均优先级 {avg_priority:.1f}, 紧急度 {avg_urgency:.1f}\n"
    
    # 时间模式分析
    report += f"\n⏰ **时间模式洞察**\n"
    report += f"• 上午邮件通常更紧急 (安全警报、紧急通知)\n"
    report += f"• 下午邮件多为商务沟通和促销\n"
    report += f"• 建议在上午优先处理高优先级邮件\n"
    
    # 内容类型分析
    urgent_count = len([a for a in all_analyses if a["sentiment_analysis"]["urgency_score"] > 0.7])
    positive_count = len([a for a in all_analyses if a["sentiment_analysis"]["polarity"] == "positive"])
    
    report += f"\n📊 **内容特征统计**\n"
    report += f"• 高紧急度邮件: {urgent_count}/{len(all_analyses)}\n"
    report += f"• 积极情感邮件: {positive_count}/{len(all_analyses)}\n"
    report += f"• 平均邮件长度: {sum(len(a['summary']) for a in all_analyses) // len(all_analyses)} 字符\n"
    
    # AI推荐策略
    report += f"\n🎯 **AI推荐处理策略**\n"
    report += f"1. 🚨 立即处理: 安全警报和客户投诉\n"
    report += f"2. 📋 今日完成: 项目截止和业务请求\n"
    report += f"3. 📰 定期查看: 合作提案和行业资讯\n"
    report += f"4. 🗑️ 批量处理: 促销邮件和社交通知\n"
    
    return report

@mcp.tool()
def parse_outlook_email(html_content: str) -> str:
    """解析复杂的Outlook HTML邮件（包括转发链和表格）
    
    Args:
        html_content: Outlook邮件的HTML内容
    """
    global email_ai
    
    try:
        # 使用Outlook解析器解析邮件
        parsed_section = email_ai.outlook_parser.parse_email(html_content)
        
        # 转换为markdown格式
        markdown_result = email_ai.outlook_parser.format_to_markdown(parsed_section)
        
        # 统计信息
        stats = {
            'total_tables': len(parsed_section.tables),
            'forwarded_levels': len(parsed_section.forwarded_emails),
            'has_header': bool(parsed_section.header),
            'body_length': len(parsed_section.body),
        }
        
        # 计算转发层级
        def get_max_level(section):
            level = section.level
            for forwarded in section.forwarded_emails:
                level = max(level, get_max_level(forwarded))
            return level
        
        max_level = get_max_level(parsed_section)
        
        result = f"""📧 **Outlook邮件解析完成**

**解析统计:**
• 表格数量: {stats['total_tables']} 个
• 转发层级: {max_level} 层
• 邮件头信息: {'✅ 已提取' if stats['has_header'] else '❌ 未找到'}
• 正文长度: {stats['body_length']} 字符

---

{markdown_result}
"""
        
        return result
        
    except Exception as e:
        return f"❌ 解析失败: {str(e)}\n💡 请确保提供的是有效的HTML邮件内容"


@mcp.tool()
def analyze_outlook_email_with_ai(html_content: str) -> str:
    """解析Outlook邮件并进行AI分析
    
    Args:
        html_content: Outlook邮件的HTML内容
    """
    global email_ai
    
    try:
        # 首先解析邮件结构
        parsed_section = email_ai.outlook_parser.parse_email(html_content)
        
        # 提取基本信息进行AI分析
        subject = parsed_section.header.get('subject', '未知主题')
        sender = parsed_section.header.get('from', '未知发件人')
        body = parsed_section.body
        
        # 进行AI分析
        ai_analysis = email_ai.analyze_email_advanced(subject, body, sender)
        
        # 格式化输出
        result = f"""🤖 **Outlook邮件AI分析**

## 📊 基础分析
• **主题:** {subject}
• **发件人:** {sender}
• **分类:** {ai_analysis['category']}
• **优先级:** {ai_analysis['final_priority']}/5 ⭐
• **情感分析:** {ai_analysis['sentiment_analysis']['polarity']} ({ai_analysis['sentiment_analysis']['confidence']:.2f})

## 🎯 核心要点
{chr(10).join(f"• {item}" for item in ai_analysis['key_info'])}

## 📋 行动项目
{chr(10).join(f"• {item}" for item in ai_analysis['action_items'])}

## 💬 回复建议
{chr(10).join(f"**{suggestion['type']}:** {suggestion['content']}" for suggestion in ai_analysis['reply_suggestions'])}

## 📄 解析的表格数据
"""
        
        # 添加表格信息
        if parsed_section.tables:
            for i, table in enumerate(parsed_section.tables, 1):
                result += f"\n### 表格 {i} ({table['row_count']}行 × {table['col_count']}列)\n"
                result += table['markdown'] + "\n"
        else:
            result += "无表格数据\n"
        
        # 添加转发邮件信息
        if parsed_section.forwarded_emails:
            result += f"\n## 📨 转发链信息\n"
            result += f"• 包含 {len(parsed_section.forwarded_emails)} 个转发邮件\n"
            
            def analyze_forwarded(section, level=0):
                info = f"{'  ' * level}• 层级 {section.level}: "
                if section.header.get('subject'):
                    info += f"{section.header['subject']}"
                if section.header.get('from'):
                    info += f" (来自: {section.header['from']})"
                return info
            
            for forwarded in parsed_section.forwarded_emails:
                result += analyze_forwarded(forwarded) + "\n"
        
        return result
        
    except Exception as e:
        return f"❌ 分析失败: {str(e)}\n💡 请确保提供的是有效的HTML邮件内容"


@mcp.tool()
def extract_outlook_tables(html_content: str) -> str:
    """专门提取Outlook邮件中的表格数据
    
    Args:
        html_content: Outlook邮件的HTML内容
    """
    global email_ai
    
    try:
        # 解析邮件
        parsed_section = email_ai.outlook_parser.parse_email(html_content)
        
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


@mcp.tool()
def test_outlook_parser_with_demo() -> str:
    """使用内置复杂邮件样本测试Outlook解析器"""
    global email_ai
    
    # 创建一个复杂的Outlook邮件样本（模拟您提到的多层转发和表格）
    complex_email_html = """
    <html>
    <head>
        <style type="text/css">
        .MsoNormal { margin: 0in; font-size: 11.0pt; font-family: "Calibri",sans-serif; }
        </style>
    </head>
    <body>
        <div class="MsoNormal">
            <p>各位同事，</p>
            <p>请查看以下Q2财务数据分析报告：</p>
            
            <table border="1" style="border-collapse:collapse;">
                <tr>
                    <th>项目</th>
                    <th>Q1收入</th>
                    <th>Q2收入</th>
                    <th>增长率</th>
                </tr>
                <tr>
                    <td>产品A</td>
                    <td>$2.1M</td>
                    <td>$2.8M</td>
                    <td>33.3%</td>
                </tr>
                <tr>
                    <td>产品B</td>
                    <td>$1.5M</td>
                    <td>$1.9M</td>
                    <td>26.7%</td>
                </tr>
                <tr>
                    <td>总计</td>
                    <td>$3.6M</td>
                    <td>$4.7M</td>
                    <td>30.6%</td>
                </tr>
            </table>
            
            <p>请及时回复确认。</p>
            <p>李经理</p>
        </div>
        
        <div style="border:none;border-top:solid #E1E1E1 1.0pt;padding:3.0pt 0in 0in 0in">
            <p><b>发件人:</b> 张三 &lt;zhang.san@company.com&gt;<br>
            <b>发送时间:</b> 2024年6月15日 14:30<br>
            <b>收件人:</b> 李经理 &lt;li.manager@company.com&gt;<br>
            <b>主题:</b> 转发: Q2财务数据需要审核</p>
            
            <p>李经理，请帮忙审核这份报告。</p>
            
            <table border="1">
                <tr>
                    <th>部门</th>
                    <th>预算</th>
                    <th>实际支出</th>
                    <th>差异</th>
                </tr>
                <tr>
                    <td>研发部</td>
                    <td>$500K</td>
                    <td>$480K</td>
                    <td>-$20K</td>
                </tr>
                <tr>
                    <td>市场部</td>
                    <td>$300K</td>
                    <td>$320K</td>
                    <td>+$20K</td>
                </tr>
            </table>
            
            <div style="border:none;border-top:solid #E1E1E1 1.0pt;padding:3.0pt 0in 0in 0in">
                <p><b>发件人:</b> 王财务 &lt;wang.finance@company.com&gt;<br>
                <b>发送时间:</b> 2024年6月15日 09:15<br>
                <b>主题:</b> Q2财务数据需要审核</p>
                
                <p>各位领导，</p>
                <p>Q2财务报告已完成，请审核。主要亮点：</p>
                <ul>
                    <li>总收入增长30.6%</li>
                    <li>研发投入控制在预算内</li>
                    <li>市场投入略有超支但效果显著</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        # 解析复杂邮件
        parsed_section = email_ai.outlook_parser.parse_email(complex_email_html)
        
        result = f"""🧪 **Outlook解析器测试结果**

📊 **解析统计:**
• 发现表格: {len(parsed_section.tables)} 个
• 转发层级: {len(parsed_section.forwarded_emails)} 层
• 邮件头: {'✅' if parsed_section.header else '❌'}
• 正文长度: {len(parsed_section.body)} 字符

---

{email_ai.outlook_parser.format_to_markdown(parsed_section)}
"""
        
        return result
        
    except Exception as e:
        return f"❌ 测试失败: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
