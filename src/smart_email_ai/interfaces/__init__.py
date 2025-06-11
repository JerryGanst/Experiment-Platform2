"""接口模块包初始化"""

from .config_interface import config_manager
from .email_interface import email_data_manager, EmailData

__all__ = ['config_manager', 'email_data_manager', 'EmailData'] 