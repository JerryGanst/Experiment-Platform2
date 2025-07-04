"""演示功能模块包初始化"""

from .demo_manager import DemoEmailManager, DemoModeManager
from .demo_data import DEMO_EMAILS_DATA

__all__ = ['DemoEmailManager', 'DemoModeManager', 'DEMO_EMAILS_DATA'] 