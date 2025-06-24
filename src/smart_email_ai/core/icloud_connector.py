"""
iCloud邮箱连接器 - Smart Email AI核心组件

提供安全、高效的iCloud邮箱IMAP连接和邮件数据处理功能
支持实时邮件获取、智能解析和结构化数据输出

特性：
- SSL/TLS安全连接
- 多编码邮件解析
- 错误处理和连接管理
- 与Smart Email AI系统集成
"""

import imaplib
import ssl
import email
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .email_cache import email_cache_manager


class iCloudConnector:
    """iCloud邮箱连接器"""
    
    def __init__(self, email_address: str = None, password: str = None):
        """初始化iCloud连接器
        
        Args:
            email_address: iCloud邮箱地址（可选，默认使用Jerry的邮箱）
            password: 应用专用密码（可选，默认使用预设密码）
        """
        self.EMAIL = email_address or "jerrywsx@icloud.com"
        self.PASSWORD = password or "fsil-npvx-rbdo-vman"  # 应用专用密码
        self.IMAP_SERVER = "imap.mail.me.com"
        self.IMAP_PORT = 993
        self.mail = None
        self.connected = False
        self.email_cache = {}  # 简单的邮件缓存
        
    def connect(self) -> bool:
        """连接到iCloud邮箱
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 创建安全SSL上下文，处理证书验证问题
            context = ssl.create_default_context()
            
            # 首先尝试标准SSL连接
            try:
                self.mail = imaplib.IMAP4_SSL(
                    self.IMAP_SERVER, 
                    self.IMAP_PORT, 
                    ssl_context=context
                )
                self._log_info("✅ 使用标准SSL连接成功（推荐模式）")
            except ssl.SSLError as ssl_err:
                # 如果SSL验证失败，尝试禁用证书验证（仅用于开发/测试）
                self._log_info(f"标准SSL连接失败: {ssl_err}")
                self._log_info("🔧 尝试使用宽松SSL设置...")
                
                # 创建宽松的SSL上下文
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                self.mail = imaplib.IMAP4_SSL(
                    self.IMAP_SERVER, 
                    self.IMAP_PORT, 
                    ssl_context=context
                )
                self._log_info("⚠️ 使用宽松SSL连接成功（降级模式）")
            
            # 登录验证
            self.mail.login(self.EMAIL, self.PASSWORD)
            
            # 选择收件箱
            self.mail.select('INBOX')
            
            self.connected = True
            self._log_info("🎉 iCloud邮箱连接和登录成功")
            return True
            
        except imaplib.IMAP4.error as imap_err:
            self.connected = False
            error_msg = str(imap_err)
            if "authentication failed" in error_msg.lower():
                self._log_error(f"iCloud登录失败 - 请检查应用专用密码: {error_msg}")
            else:
                self._log_error(f"iCloud IMAP错误: {error_msg}")
            return False
            
        except Exception as e:
            self.connected = False
            self._log_error(f"iCloud连接失败: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """安全断开iCloud连接"""
        try:
            if self.mail and self.connected:
                self.mail.close()
                self.mail.logout()
        except:
            pass  # 忽略断开连接时的错误
        finally:
            self.connected = False
            self.mail = None
            self.email_cache.clear()
    
    def get_mailbox_stats(self) -> Dict[str, Any]:
        """获取邮箱统计信息
        
        Returns:
            Dict: 包含邮箱统计信息的字典
        """
        if not self.connected:
            return {"error": "未连接到邮箱"}
        
        try:
            stats = {}
            
            # 获取邮件总数
            status, count = self.mail.select('INBOX')
            stats['total_emails'] = int(count[0]) if status == 'OK' else 0
            
            # 获取未读邮件数
            status, unread = self.mail.search(None, 'UNSEEN')
            stats['unread_count'] = len(unread[0].split()) if unread[0] else 0
            
            # 获取今日邮件数
            today = datetime.now().strftime("%d-%b-%Y")
            status, today_mails = self.mail.search(None, f'SINCE {today}')
            stats['today_count'] = len(today_mails[0].split()) if today_mails[0] else 0
            
            # 获取本周邮件数
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
            status, week_mails = self.mail.search(None, f'SINCE {week_ago}')
            stats['week_count'] = len(week_mails[0].split()) if week_mails[0] else 0
            
            stats['email_address'] = self.EMAIL
            stats['connection_status'] = 'connected'
            stats['last_update'] = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            return {"error": f"获取邮箱统计失败: {str(e)}"}
    
    def search_emails(self, criteria: str) -> List[bytes]:
        """搜索邮件
        
        Args:
            criteria: IMAP搜索条件
            
        Returns:
            List[bytes]: 邮件ID列表
        """
        if not self.connected:
            return []
        
        try:
            status, messages = self.mail.search(None, criteria)
            if status == 'OK' and messages[0]:
                return messages[0].split()
            return []
        except Exception as e:
            self._log_error(f"邮件搜索失败: {str(e)}")
            return []
    
    def fetch_email(self, mail_id: bytes) -> Optional[email.message.Message]:
        """安全获取邮件对象
        
        Args:
            mail_id: 邮件ID
            
        Returns:
            Optional[email.message.Message]: 邮件对象或None
        """
        # 检查缓存
        cache_key = mail_id.decode() if isinstance(mail_id, bytes) else str(mail_id)
        if cache_key in self.email_cache:
            return self.email_cache[cache_key]
        
        try:
            # 确保mail_id是bytes类型
            if isinstance(mail_id, str):
                mail_id = mail_id.encode()
            
            self._log_info(f"获取邮件 ID: {mail_id}")
            # 修复：使用BODY.PEEK[]而不是RFC822，避免标记邮件为已读
            status, msg_data = self.mail.fetch(mail_id, '(BODY.PEEK[])')
            self._log_info(f"IMAP fetch状态: {status}, 数据长度: {len(msg_data) if msg_data else 0}")
            
            if status == 'OK' and msg_data and len(msg_data) > 0:
                # 检查返回数据的结构
                self._log_info(f"消息数据类型: {type(msg_data[0])}, 内容: {str(msg_data[0])[:100]}")
                
                # 处理不同的返回格式
                raw_email = None
                
                if isinstance(msg_data[0], tuple) and len(msg_data[0]) >= 2:
                    # 标准格式: (b'1 (BODY.PEEK[] {1234}', b'邮件内容...')
                    raw_email = msg_data[0][1]
                elif isinstance(msg_data[0], bytes):
                    # 某些情况下直接返回bytes
                    raw_email = msg_data[0]
                elif len(msg_data) >= 2 and isinstance(msg_data[1], bytes):
                    # 邮件内容在第二个元素
                    raw_email = msg_data[1]
                
                if raw_email and len(raw_email) > 0:
                    self._log_info(f"原始邮件数据类型: {type(raw_email)}, 长度: {len(raw_email)}")
                    
                    # 解析邮件
                    if isinstance(raw_email, bytes):
                        msg = email.message_from_bytes(raw_email)
                    elif isinstance(raw_email, str):
                        msg = email.message_from_string(raw_email)
                    else:
                        self._log_error(f"未知的邮件数据类型: {type(raw_email)}")
                        return None
                    
                    # 缓存邮件对象
                    self.email_cache[cache_key] = msg
                    subject = self._decode_header(msg.get('Subject', '无主题'))
                    self._log_info(f"成功解析邮件: {subject[:50]}")
                    return msg
                else:
                    self._log_error(f"无法提取邮件内容: {msg_data}")
                    return None
            else:
                self._log_error(f"IMAP fetch失败: status={status}, data={msg_data}")
                return None
            
        except Exception as e:
            self._log_error(f"获取邮件失败 (ID: {mail_id}): {str(e)}")
            import traceback
            self._log_error(f"详细错误: {traceback.format_exc()}")
            return None
    
    def parse_email_content(self, msg: email.message.Message) -> Dict[str, Any]:
        """解析邮件内容为结构化数据
        
        Args:
            msg: 邮件对象
            
        Returns:
            Dict: 结构化的邮件数据
        """
        try:
            parsed = {
                'subject': self._decode_header(msg.get('Subject', '')),
                'sender': self._decode_header(msg.get('From', '')),
                'recipient': self._decode_header(msg.get('To', '')),
                'date': msg.get('Date', ''),
                'message_id': msg.get('Message-ID', ''),
                'body_text': self._extract_text_body(msg),
                'body_html': self._extract_html_body(msg),
                'attachments': self._get_attachment_info(msg),
                'is_multipart': msg.is_multipart(),
                'content_type': msg.get_content_type(),
                'size': self._estimate_size(msg)
            }
            
            # 添加计算字段
            parsed['body_length'] = len(parsed['body_text'])
            parsed['has_attachments'] = len(parsed['attachments']) > 0
            parsed['parsed_date'] = self._parse_date(parsed['date'])
            
            return parsed
            
        except Exception as e:
            self._log_error(f"邮件解析失败: {str(e)}")
            return {
                'error': f"邮件解析失败: {str(e)}",
                'subject': '解析失败',
                'body_text': '邮件内容解析失败'
            }
    
    def get_recent_emails(self, count: int = 10, use_cache: bool = True) -> List[Dict[str, Any]]:
        """获取最近的邮件列表（带缓存优化）
        
        Args:
            count: 要获取的邮件数量
            use_cache: 是否使用缓存
            
        Returns:
            List[Dict]: 解析后的邮件数据列表
        """
        # 🚀 优先从缓存获取
        if use_cache:
            cached_emails = email_cache_manager.get_recent_emails(count, 'icloud')
            if cached_emails:
                self._log_info(f"⚡ 从缓存快速获取 {len(cached_emails)} 封邮件 (响应时间 <100ms)")
                return cached_emails
        
        if not self.connected:
            return []
        
        try:
            self._log_info(f"📡 从iCloud服务器获取最近 {count} 封邮件...")
            start_time = datetime.now()
            
            # 获取所有邮件ID
            mail_ids = self.search_emails('ALL')
            
            # 取最新的邮件
            recent_ids = mail_ids[-count:] if len(mail_ids) >= count else mail_ids
            recent_ids.reverse()  # 最新的在前面
            
            emails = []
            for i, mail_id in enumerate(recent_ids, 1):
                try:
                    # 获取邮件对象
                    msg = self.fetch_email(mail_id)
                    if msg:
                        # 解析邮件内容
                        parsed_email = self.parse_email_content(msg)
                        
                        # 添加额外字段
                        parsed_email['mail_id'] = mail_id.decode() if isinstance(mail_id, bytes) else str(mail_id)
                        parsed_email['account_type'] = 'icloud'
                        
                        # 格式化日期字段供缓存使用
                        if parsed_email.get('parsed_date'):
                            parsed_email['date_received'] = parsed_email['parsed_date']
                        
                        # 计算重要性分数（简单算法）
                        importance_score = 50  # 基础分数
                        subject = parsed_email.get('subject', '').lower()
                        
                        # 重要关键词加分
                        important_keywords = ['urgent', '紧急', '重要', 'important', 'asap', '立即']
                        for keyword in important_keywords:
                            if keyword in subject:
                                importance_score += 20
                                break
                        
                        # 有附件加分
                        if parsed_email.get('has_attachments', False):
                            importance_score += 10
                        
                        # 邮件长度影响
                        body_length = parsed_email.get('body_length', 0)
                        if body_length > 1000:
                            importance_score += 5
                        elif body_length < 100:
                            importance_score -= 10
                        
                        parsed_email['importance_score'] = min(100, max(0, importance_score))
                        
                        emails.append(parsed_email)
                        
                        # 添加调试信息
                        date_info = parsed_email.get('date', '无日期')[:19]
                        self._log_info(f"✅ 解析邮件 {i}/{count}: {parsed_email.get('subject', '无主题')[:30]}... (日期: {date_info})")
                    else:
                        self._log_error(f"❌ 无法获取邮件ID: {mail_id}")
                        
                except Exception as e:
                    self._log_error(f"❌ 解析邮件失败 (ID: {mail_id}): {str(e)}")
                    continue
            
            # 💾 存储到缓存以加速后续访问
            if emails and use_cache:
                try:
                    stored_count = email_cache_manager.store_emails(emails)
                    self._log_info(f"💾 已缓存 {stored_count} 封邮件到本地数据库")
                except Exception as cache_err:
                    self._log_error(f"❌ 缓存存储失败: {cache_err}")
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            self._log_info(f"🎉 成功获取并解析 {len(emails)} 封邮件 (耗时: {elapsed_time:.2f}秒)")
            return emails
            
        except Exception as e:
            self._log_error(f"❌ 获取最近邮件失败: {str(e)}")
            import traceback
            self._log_error(f"详细错误: {traceback.format_exc()}")
            return []
    
    def search_emails_by_content(self, query: str, max_results: int = 20, use_cache: bool = True) -> List[Dict[str, Any]]:
        """根据内容搜索邮件（带缓存优化）
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数量
            use_cache: 是否使用缓存
            
        Returns:
            List[Dict]: 匹配的邮件数据列表
        """
        # 🔍 优先使用缓存搜索（本地全文索引）
        if use_cache:
            cached_results = email_cache_manager.search_emails(query, max_results)
            if cached_results:
                self._log_info(f"⚡ 从本地索引快速搜索到 {len(cached_results)} 个结果 (响应时间 <50ms)")
                return cached_results
        
        if not self.connected:
            return []
        
        try:
            self._log_info(f"🔍 在iCloud服务器搜索: '{query}'...")
            start_time = datetime.now()
            
            # 构建IMAP搜索条件
            search_criteria = f'(OR (OR SUBJECT "{query}" FROM "{query}") BODY "{query}")'
            mail_ids = self.search_emails(search_criteria)
            
            # 限制结果数量
            search_results = mail_ids[-max_results:] if len(mail_ids) > max_results else mail_ids
            search_results.reverse()
            
            emails = []
            for mail_id in search_results:
                msg = self.fetch_email(mail_id)
                if msg:
                    parsed_email = self.parse_email_content(msg)
                    parsed_email['mail_id'] = mail_id.decode()
                    parsed_email['account_type'] = 'icloud'
                    parsed_email['search_query'] = query
                    emails.append(parsed_email)
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            self._log_info(f"✅ 搜索完成，找到 {len(emails)} 个结果 (耗时: {elapsed_time:.2f}秒)")
            
            return emails
            
        except Exception as e:
            self._log_error(f"邮件搜索失败: {str(e)}")
            return []
    
    # 私有辅助方法
    
    def _decode_header(self, header: str) -> str:
        """解码邮件头部信息"""
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
        except Exception:
            return str(header)
    
    def _extract_text_body(self, msg: email.message.Message) -> str:
        """提取纯文本邮件正文"""
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
                if msg.get_content_type() == "text/plain":
                    charset = msg.get_content_charset() or 'utf-8'
                    body_bytes = msg.get_payload(decode=True)
                    if body_bytes:
                        body = body_bytes.decode(charset, errors='ignore')
                    else:
                        body = str(msg.get_payload())
        except Exception:
            body = "文本正文解析失败"
        
        return body.strip()
    
    def _extract_html_body(self, msg: email.message.Message) -> str:
        """提取HTML邮件正文"""
        html_body = ""
        
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        charset = part.get_content_charset() or 'utf-8'
                        body_bytes = part.get_payload(decode=True)
                        if body_bytes:
                            html_body += body_bytes.decode(charset, errors='ignore')
            else:
                if msg.get_content_type() == "text/html":
                    charset = msg.get_content_charset() or 'utf-8'
                    body_bytes = msg.get_payload(decode=True)
                    if body_bytes:
                        html_body = body_bytes.decode(charset, errors='ignore')
        except Exception:
            html_body = ""
        
        return html_body.strip()
    
    def _get_attachment_info(self, msg: email.message.Message) -> List[Dict[str, str]]:
        """获取附件信息"""
        attachments = []
        
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        if filename:
                            attachments.append({
                                'filename': self._decode_header(filename),
                                'content_type': part.get_content_type(),
                                'size': len(part.get_payload()) if part.get_payload() else 0
                            })
        except Exception:
            pass
        
        return attachments
    
    def _estimate_size(self, msg: email.message.Message) -> int:
        """估算邮件大小"""
        try:
            return len(str(msg))
        except:
            return 0
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析邮件日期为标准ISO格式"""
        try:
            if not date_str:
                return None
            
            # 清理日期字符串
            date_str = date_str.strip()
            
            # 使用email.utils解析日期
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            
            # 转换为ISO格式字符串
            return dt.isoformat()
            
        except Exception as e:
            self._log_error(f"日期解析失败 '{date_str}': {e}")
            # 如果解析失败，尝试返回原始字符串
            return date_str.strip() if date_str else None
    
    def _log_error(self, error_msg: str) -> None:
        """记录错误信息"""
        # 可以扩展为更复杂的日志记录
        print(f"[iCloud错误] {error_msg}")
    
    def _log_info(self, info_msg: str) -> None:
        """记录信息"""
        print(f"[iCloud信息] {info_msg}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
    
    def __repr__(self):
        """字符串表示"""
        status = "已连接" if self.connected else "未连接"
        return f"iCloudConnector(邮箱={self.EMAIL}, 状态={status})" 