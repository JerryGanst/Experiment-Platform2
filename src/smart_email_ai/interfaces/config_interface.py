"""配置管理接口"""

import json
import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigInterface(ABC):
    """配置管理抽象接口"""
    
    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        pass
    
    @abstractmethod
    def get_data_processing_settings(self) -> Dict[str, Any]:
        """获取数据处理配置"""
        pass
    
    @abstractmethod
    def get_parser_settings(self) -> Dict[str, Any]:
        """获取邮件解析器配置"""
        pass
    
    @abstractmethod
    def get_system_settings(self) -> Dict[str, Any]:
        """获取系统运行配置"""
        pass


class YamlConfigManager(ConfigInterface):
    """基于YAML的配置管理器"""
    
    def __init__(self, config_path: str = "data/config.yaml"):
        self.config_path = config_path
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path) and YAML_AVAILABLE:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            else:
                if not YAML_AVAILABLE:
                    print("⚠️ YAML模块未找到，将使用默认配置")
                self._config = self._get_default_config()
                if YAML_AVAILABLE:
                    self._save_default_config()
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            self._config = self._get_default_config()
    
    def load_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config or {}
    
    def get_data_processing_settings(self) -> Dict[str, Any]:
        """获取数据处理配置"""
        return self._config.get('data_processing', {})
    
    def get_parser_settings(self) -> Dict[str, Any]:
        """获取邮件解析器配置"""
        return self._config.get('parser_settings', {})
    
    def get_system_settings(self) -> Dict[str, Any]:
        """获取系统运行配置"""
        return self._config.get('system_settings', {})
    
    def get_mcp_settings(self) -> Dict[str, Any]:
        """获取MCP服务配置"""
        return self._config.get('mcp_settings', {})
    
    def get_forward_patterns(self) -> List[str]:
        """获取转发邮件识别模式"""
        parser_settings = self.get_parser_settings()
        return parser_settings.get('forward_patterns', [])
    
    def get_header_patterns(self) -> Dict[str, List[str]]:
        """获取邮件头字段匹配模式"""
        parser_settings = self.get_parser_settings()
        return parser_settings.get('header_patterns', {})
    
    def get_file_paths(self) -> Dict[str, str]:
        """获取文件路径配置"""
        system_settings = self.get_system_settings()
        return system_settings.get('paths', {})
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'data_processing': {
                'email_processing': {
                    'max_content_length': 1000000,
                    'preserve_formatting': True,
                    'extract_metadata': True
                }
            },
            'parser_settings': {
                'forward_patterns': [
                    "-----\\s*原始邮件\\s*-----",
                    "-----\\s*Forwarded message\\s*-----",
                    "发件人:",
                    "From:"
                ]
            },
            'system_settings': {
                'demo_mode': False,
                'log_level': 'INFO'
            },
            'mcp_settings': {
                'server_name': 'smart_email_ai',
                'enable_debug': False
            }
        }
    
    def _save_default_config(self) -> None:
        """保存默认配置到文件"""
        if not YAML_AVAILABLE:
            return
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"❌ 保存默认配置失败: {e}")


# 全局配置管理器实例
config_manager = YamlConfigManager() 