"""邮件解析器核心模块"""

import re
import html
from bs4 import BeautifulSoup
# HTML转文本处理（可选依赖）
try:
    import html2text
    HTML2TEXT_AVAILABLE = True
except ImportError:
    HTML2TEXT_AVAILABLE = False
    # 提供简单的HTML清理备用方案
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


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
    """Outlook邮件解析器 - 解耦版本"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化解析器
        
        Args:
            config: 解析器配置，包含forward_patterns, header_patterns等
        """
        self.config: Dict[str, Any] = config or {}
        self._init_patterns()

    def _init_patterns(self) -> None:
        """初始化匹配模式"""
        # 从配置获取转发邮件的常见分界标识
        forward_patterns_raw = self.config.get('forward_patterns', [
            r'-----\s*原始邮件\s*-----',
            r'-----\s*Forwarded message\s*-----',
            r'发件人:',
            r'From:',
            r'<div style=["\']border:none;border-top:solid #E1E1E1 1\.0pt',
            r'<div[^>]*border-top[^>]*>',
        ])
        
        # 确保类型安全
        if isinstance(forward_patterns_raw, list):
            self.forward_patterns: List[str] = [str(pattern) for pattern in forward_patterns_raw]
        else:
            self.forward_patterns = [
                r'-----\s*原始邮件\s*-----',
                r'-----\s*Forwarded message\s*-----',
                r'发件人:',
                r'From:',
            ]

        # 从配置获取邮件头字段模式
        default_header_patterns = {
            'from': [r'发件人[:\s]*(.+?)(?:<br|$)', r'From[:\s]*(.+?)(?:<br|$)'],
            'to': [r'收件人[:\s]*(.+?)(?:<br|$)', r'To[:\s]*(.+?)(?:<br|$)'],
            'cc': [r'抄送[:\s]*(.+?)(?:<br|$)', r'CC[:\s]*(.+?)(?:<br|$)'],
            'subject': [r'主题[:\s]*(.+?)(?:<br|$)', r'Subject[:\s]*(.+?)(?:<br|$)'],
            'date': [r'发送时间[:\s]*(.+?)(?:<br|$)', r'Sent[:\s]*(.+?)(?:<br|$)'],
        }
        
        header_patterns_raw = self.config.get('header_patterns', default_header_patterns)
        if isinstance(header_patterns_raw, dict):
            self.header_patterns: Dict[str, List[str]] = {}
            for key, patterns in header_patterns_raw.items():
                if isinstance(patterns, list):
                    self.header_patterns[str(key)] = [str(p) for p in patterns]
                else:
                    self.header_patterns[str(key)] = default_header_patterns.get(str(key), [])
        else:
            self.header_patterns = default_header_patterns

        # 表格检测配置
        table_config_raw = self.config.get('table_detection', {})
        if isinstance(table_config_raw, dict):
            self.min_table_rows: int = int(table_config_raw.get('min_rows', 2))
            self.skip_layout_tables: bool = bool(table_config_raw.get('skip_layout_tables', True))
        else:
            self.min_table_rows = 2
            self.skip_layout_tables = True

    def parse_email(self, email_content: str) -> EmailSection:
        """
        统一解析邮件（包括转发链）
        
        Args:
            email_content: 邮件HTML内容
            
        Returns:
            EmailSection: 解析后的邮件结构
        """
        # 类型安全检查
        if email_content is None:
            raise ValueError("email_content 不能为 None")
        
        if not isinstance(email_content, str):
            # 尝试转换为字符串
            try:
                email_content = str(email_content)
            except Exception as e:
                raise TypeError(f"无法将 email_content 转换为字符串: {e}")
        
        # 检查是否为空字符串
        if not email_content.strip():
            return EmailSection(
                header={},
                body="",
                tables=[],
                attachments=[],
                forwarded_emails=[],
                level=0
            )
        
        # 清理HTML并创建BeautifulSoup对象
        soup = self._clean_outlook_html(email_content)

        # 分割邮件段落（原始+转发）
        email_sections = self._split_email_sections(soup)

        # 递归解析每个段落
        return self._parse_section(email_sections[0], email_sections[1:], level=0)

    def _clean_outlook_html(self, html_content: str) -> BeautifulSoup:
        """清理Outlook特有的HTML标记"""
        # 确保输入不为空
        if not html_content:
            return BeautifulSoup("", 'html.parser')
        
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
            if self.skip_layout_tables and self._is_layout_table(table):
                continue

            table_data = self._parse_table_to_markdown(table)
            if table_data:
                tables.append(table_data)

        return tables

    def _is_layout_table(self, table) -> bool:
        """判断是否为布局表格"""
        # 检查是否有明确的数据表格特征
        has_th = table.find('th') is not None
        has_multiple_rows = len(table.find_all('tr')) >= self.min_table_rows
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
            if not (self.skip_layout_tables and self._is_layout_table(table)):
                table.decompose()

        # 移除邮件头部分（通常在特定div中）
        for div in soup.find_all('div'):
            if 'border-top:solid #E1E1E1' in str(div):
                div.decompose()

        # 转换为纯文本
        if HTML2TEXT_AVAILABLE:
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0  # 不限制行宽

            text = h.handle(str(soup))
        else:
            # 提供简单的HTML清理备用方案
            text = re.sub(r'<[^>]*>', '', str(soup)) # 移除所有HTML标签
            text = re.sub(r'\s+', ' ', text) # 清理多余空白
            text = re.sub(r'\n\s*\n\s*\n', '\n\n', text) # 清理多余的空行

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