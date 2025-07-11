"""
邮件缓存管理器 - 多级缓存优化邮件检索性能

实现L1(内存) + L2(SQLite) + L3(文件)三级缓存架构
目标：将邮件检索时间从3-5秒降低到100-500ms
"""

import sqlite3
import json
import hashlib
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import pickle
import threading
from collections import OrderedDict
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager


class MemoryCache:
    """L1缓存 - 内存缓存 (最快访问)"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                # 检查TTL
                if time.time() - self.timestamps[key] < self.ttl_seconds:
                    # 移到末尾 (LRU)
                    self.cache.move_to_end(key)
                    return self.cache[key]
                else:
                    # 过期删除
                    del self.cache[key]
                    del self.timestamps[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        with self.lock:
            # 检查容量限制
            if len(self.cache) >= self.max_size and key not in self.cache:
                # 删除最老的条目
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
            self.cache.move_to_end(key)
    
    def clear(self) -> None:
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def stats(self) -> Dict[str, Any]:
        with self.lock:
            current_time = time.time()
            valid_entries = sum(
                1 for ts in self.timestamps.values() 
                if current_time - ts < self.ttl_seconds
            )
            return {
                'total_entries': len(self.cache),
                'valid_entries': valid_entries,
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds
            }


class SQLiteCache:
    """L2缓存 - SQLite本地数据库 (快速访问)"""
    
    def __init__(self, db_path: str = "data/email_cache.db", pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._connection_pool = []
        self._pool_lock = threading.Lock()
        self.ensure_db_directory()
        self.init_database()
        self._init_connection_pool()

    def ensure_db_directory(self):
        """确保数据库目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            # 应用性能优化设置
            self._apply_performance_optimizations(conn)
            # 邮件索引表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emails_index (
                    id TEXT PRIMARY KEY,
                    account_type TEXT,
                    message_id TEXT UNIQUE,
                    subject TEXT,
                    from_email TEXT,
                    from_name TEXT,
                    to_emails TEXT,
                    date_received DATETIME,
                    importance_score INTEGER DEFAULT 50,
                    has_attachments BOOLEAN DEFAULT FALSE,
                    is_read BOOLEAN DEFAULT FALSE,
                    content_hash TEXT,
                    size_bytes INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 邮件内容表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_content (
                    email_id TEXT PRIMARY KEY,
                    body_text TEXT,
                    body_html TEXT,
                    attachments_json TEXT,
                    FOREIGN KEY(email_id) REFERENCES emails_index(id)
                )
            """)
            
            # 全文搜索表
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS email_fts USING fts5(
                    email_id,
                    subject,
                    body_text,
                    from_name
                )
            """)
            
            # 性能优化索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_date_received ON emails_index(date_received DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_from_email ON emails_index(from_email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_importance ON emails_index(importance_score DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_account_date ON emails_index(account_type, date_received)")
    
    def store_email(self, email_data: Dict[str, Any]) -> bool:
        """存储邮件到缓存"""
        try:
            with self._get_connection() as conn:
                # 计算内容哈希
                content_str = f"{email_data.get('subject', '')}{email_data.get('body_text', '')}"
                content_hash = hashlib.md5(content_str.encode()).hexdigest()
                
                # 存储邮件索引
                conn.execute("""
                    INSERT OR REPLACE INTO emails_index 
                    (id, account_type, message_id, subject, from_email, from_name, 
                     to_emails, date_received, importance_score, has_attachments, 
                     is_read, content_hash, size_bytes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    email_data.get('mail_id', ''),
                    email_data.get('account_type', 'icloud'),
                    email_data.get('message_id', ''),
                    email_data.get('subject', ''),
                    email_data.get('sender', ''),
                    email_data.get('sender', '').split('<')[0].strip(),
                    json.dumps([email_data.get('recipient', '')]),
                    email_data.get('parsed_date', datetime.now().isoformat()),
                    self._calculate_importance(email_data),
                    email_data.get('has_attachments', False),
                    False,  # 默认未读
                    content_hash,
                    email_data.get('size', 0),
                    datetime.now().isoformat()
                ))
                
                # 存储邮件内容
                conn.execute("""
                    INSERT OR REPLACE INTO email_content 
                    (email_id, body_text, body_html, attachments_json)
                    VALUES (?, ?, ?, ?)
                """, (
                    email_data.get('mail_id', ''),
                    email_data.get('body_text', ''),
                    email_data.get('body_html', ''),
                    json.dumps(email_data.get('attachments', []))
                ))
                
                # 更新全文搜索索引
                conn.execute("""
                    INSERT OR REPLACE INTO email_fts 
                    (email_id, subject, body_text, from_name)
                    VALUES (?, ?, ?, ?)
                """, (
                    email_data.get('mail_id', ''),
                    email_data.get('subject', ''),
                    email_data.get('body_text', ''),
                    email_data.get('sender', '').split('<')[0].strip()
                ))
                
                return True
        except Exception as e:
            # 移除print语句，避免MCP JSON解析错误
            return False
    
    def get_recent_emails(self, count: int = 10, account_type: str = 'icloud') -> List[Dict[str, Any]]:
        """快速获取最近邮件"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT e.*, c.body_text, c.body_html, c.attachments_json
                    FROM emails_index e
                    LEFT JOIN email_content c ON e.id = c.email_id
                    WHERE e.account_type = ?
                    ORDER BY e.date_received DESC
                    LIMIT ?
                """, (account_type, count))
                
                emails = []
                for row in cursor.fetchall():
                    email_dict = dict(row)
                    # 解析JSON字段
                    email_dict['to_emails'] = json.loads(email_dict['to_emails'] or '[]')
                    email_dict['attachments'] = json.loads(email_dict['attachments_json'] or '[]')
                    emails.append(email_dict)
                
                return emails
        except Exception as e:
            print(f"[缓存错误] 获取最近邮件失败: {e}")
            return []
    
    def search_emails(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """全文搜索邮件"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT e.*, c.body_text, c.body_html
                    FROM email_fts
                    JOIN emails_index e ON email_fts.email_id = e.id
                    LEFT JOIN email_content c ON e.id = c.email_id
                    WHERE email_fts MATCH ?
                    ORDER BY e.date_received DESC
                    LIMIT ?
                """, (query, limit))
                
                results = []
                for row in cursor.fetchall():
                    email_dict = dict(row)
                    email_dict['to_emails'] = json.loads(email_dict['to_emails'] or '[]')
                    results.append(email_dict)
                
                return results
        except Exception as e:
            # 移除print语句，避免MCP JSON解析错误
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM emails_index")
                total_emails = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM email_content")
                cached_content = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM emails_index 
                    WHERE date_received >= date('now', '-1 day')
                """)
                recent_emails = cursor.fetchone()[0]
                
                return {
                    'total_emails': total_emails,
                    'cached_content': cached_content,
                    'recent_emails': recent_emails,
                    'db_size_mb': os.path.getsize(self.db_path) / 1024 / 1024 if os.path.exists(self.db_path) else 0
                }
        except Exception as e:
            # 移除print语句，避免MCP JSON解析错误
            return {}
    
    def _calculate_importance(self, email_data: Dict[str, Any]) -> int:
        """计算邮件重要性分数 (0-100)"""
        score = 50  # 基础分数
        
        # 发件人重要性
        sender = email_data.get('sender', '').lower()
        if any(domain in sender for domain in ['apple.com', 'google.com', 'microsoft.com']):
            score += 20
        
        # 主题关键词
        subject = email_data.get('subject', '').lower()
        important_keywords = ['urgent', '紧急', 'important', '重要', 'security', '安全']
        if any(keyword in subject for keyword in important_keywords):
            score += 15
        
        # 有附件
        if email_data.get('has_attachments', False):
            score += 10
        
        # 邮件大小
        size = email_data.get('size', 0)
        if size > 50000:  # 大于50KB
            score += 5
        
        return min(100, max(0, score))

    def _init_connection_pool(self):
        """初始化连接池"""
        with self._pool_lock:
            for _ in range(self.pool_size):
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                self._apply_performance_optimizations(conn)
                self._connection_pool.append(conn)

    def _apply_performance_optimizations(self, conn: sqlite3.Connection) -> None:
        """应用SQLite性能优化设置"""
        try:
            # WAL模式 - 提高并发性能
            conn.execute("PRAGMA journal_mode=WAL")
            # 同步模式 - 平衡性能和数据安全
            conn.execute("PRAGMA synchronous=NORMAL")
            # 缓存大小 - 增加内存缓存
            conn.execute("PRAGMA cache_size=10000")
            # 临时存储 - 使用内存存储临时数据
            conn.execute("PRAGMA temp_store=memory")
            # 页面大小 - 优化存储效率
            conn.execute("PRAGMA page_size=4096")
            # 内存映射 - 提高读取性能
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
        except Exception as e:
            # 如果PRAGMA设置失败，记录但不中断连接创建
            pass

    @contextmanager
    def _get_connection(self):
        """从连接池获取连接"""
        with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
            else:
                # 池子空了，创建新连接
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                # 应用性能优化设置，确保与池化连接一致
                self._apply_performance_optimizations(conn)
        
        try:
            yield conn
        finally:
            with self._pool_lock:
                if len(self._connection_pool) < self.pool_size:
                    self._connection_pool.append(conn)
                else:
                    conn.close()


class EmailCacheManager:
    """邮件缓存管理器 - 统一缓存接口"""
    
    def __init__(self):
        self.memory_cache = MemoryCache(max_size=100, ttl_seconds=300)  # 5分钟
        self.sqlite_cache = SQLiteCache()
        self.stats = {
            'hits': {'memory': 0, 'sqlite': 0, 'miss': 0},
            'operations': {'get': 0, 'set': 0, 'search': 0}
        }
    
    def get_recent_emails(self, count: int = 10, account_type: str = 'icloud') -> List[Dict[str, Any]]:
        """获取最近邮件 - 优先从缓存"""
        self.stats['operations']['get'] += 1
        
        cache_key = f"recent_{account_type}_{count}"
        
        # L1: 内存缓存
        cached_emails = self.memory_cache.get(cache_key)
        if cached_emails:
            self.stats['hits']['memory'] += 1
            return cached_emails
        
        # L2: SQLite缓存
        emails = self.sqlite_cache.get_recent_emails(count, account_type)
        if emails:
            self.stats['hits']['sqlite'] += 1
            # 回填到内存缓存
            self.memory_cache.set(cache_key, emails)
            return emails
        
        # 缓存未命中
        self.stats['hits']['miss'] += 1
        return []
    
    def store_emails(self, emails: List[Dict[str, Any]]) -> int:
        """批量存储邮件到缓存"""
        self.stats['operations']['set'] += 1
        
        stored_count = 0
        for email in emails:
            if self.sqlite_cache.store_email(email):
                stored_count += 1
        
        # 清空相关的内存缓存
        self.memory_cache.clear()
        
        return stored_count
    
    def search_emails(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索邮件"""
        self.stats['operations']['search'] += 1
        
        cache_key = f"search_{hashlib.md5(query.encode()).hexdigest()}_{limit}"
        
        # 检查内存缓存
        cached_results = self.memory_cache.get(cache_key)
        if cached_results:
            self.stats['hits']['memory'] += 1
            return cached_results
        
        # 执行搜索
        results = self.sqlite_cache.search_emails(query, limit)
        if results:
            self.stats['hits']['sqlite'] += 1
            # 缓存搜索结果
            self.memory_cache.set(cache_key, results)
        else:
            self.stats['hits']['miss'] += 1
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        total_operations = sum(self.stats['operations'].values())
        total_hits = sum(self.stats['hits'].values())
        
        cache_hit_rate = (
            (self.stats['hits']['memory'] + self.stats['hits']['sqlite']) / total_hits * 100
            if total_hits > 0 else 0
        )
        
        return {
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'memory_cache': self.memory_cache.stats(),
            'sqlite_cache': self.sqlite_cache.get_cache_stats(),
            'operation_stats': self.stats['operations'],
            'hit_stats': self.stats['hits']
        }
    
    def clear_all_caches(self):
        """清空所有缓存"""
        self.memory_cache.clear()
        # SQLite缓存保留，只清空内存
    
    def clear_cache(self, account_type: str = None):
        """清空指定类型的缓存
        
        Args:
            account_type: 账户类型（如'icloud'），为None时清空所有缓存
        """
        # 清空内存缓存
        self.memory_cache.clear()
        
        # 如果指定了账户类型，清空对应的SQLite缓存
        if account_type:
            try:
                with sqlite3.connect(self.sqlite_cache.db_path, check_same_thread=False) as conn:
                    # 应用性能优化设置
                    self.sqlite_cache._apply_performance_optimizations(conn)
                    # 先删除依赖表中的数据，再删除主表数据
                    conn.execute("DELETE FROM email_content WHERE email_id IN (SELECT id FROM emails_index WHERE account_type = ?)", (account_type,))
                    conn.execute("DELETE FROM email_fts WHERE email_id IN (SELECT id FROM emails_index WHERE account_type = ?)", (account_type,))
                    conn.execute("DELETE FROM emails_index WHERE account_type = ?", (account_type,))
                    conn.commit()
                    # 移除print语句，避免MCP JSON解析错误
                    pass
            except Exception as e:
                # 移除print语句，避免MCP JSON解析错误  
                pass
        else:
            # 清空所有SQLite缓存
            try:
                with sqlite3.connect(self.sqlite_cache.db_path, check_same_thread=False) as conn:
                    # 应用性能优化设置
                    self.sqlite_cache._apply_performance_optimizations(conn)
                    # 先删除依赖表，再删除主表
                    conn.execute("DELETE FROM email_content")
                    conn.execute("DELETE FROM email_fts")
                    conn.execute("DELETE FROM emails_index")
                    conn.commit()
                    # 移除print语句，避免MCP JSON解析错误
                    pass
            except Exception as e:
                # 移除print语句，避免MCP JSON解析错误
                pass


# 全局缓存管理器实例
email_cache_manager = EmailCacheManager() 