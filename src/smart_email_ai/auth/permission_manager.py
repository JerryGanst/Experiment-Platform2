"""权限管理器 - 统一权限控制入口"""

import functools
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from .roles import UserRole, Permission, has_permission as check_permission
from ..interfaces.config_interface import config_manager


class PermissionManager:
    """权限管理器 - 负责权限验证和控制"""
    
    def __init__(self):
        self.current_user_role: Optional[UserRole] = None
        self.session_data: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """从配置文件加载权限设置"""
        try:
            system_settings = config_manager.get_system_settings()
            demo_mode = system_settings.get('demo_mode', False)
            
            # 根据配置设置默认角色
            if demo_mode:
                self.current_user_role = UserRole.DEMO_USER
            else:
                # 从配置或环境变量获取用户角色
                default_role = system_settings.get('default_user_role', 'basic_user')
                self.current_user_role = UserRole(default_role)
                
        except Exception:
            # 默认为基础用户
            self.current_user_role = UserRole.BASIC_USER
    
    def set_user_role(self, role: UserRole) -> str:
        """设置当前用户角色"""
        old_role = self.current_user_role
        self.current_user_role = role
        self.session_data['role_changed_at'] = datetime.now().isoformat()
        
        return f"✅ 用户角色已从 {old_role.value if old_role else 'None'} 更改为 {role.value}"
    
    def get_current_role(self) -> Optional[UserRole]:
        """获取当前用户角色"""
        return self.current_user_role
    
    def has_permission(self, permission: Permission) -> bool:
        """检查当前用户是否有指定权限"""
        if not self.current_user_role:
            return False
        return check_permission(self.current_user_role, permission)
    
    def require_permission(self, permission: Permission) -> bool:
        """要求特定权限，如果没有则抛出异常"""
        if not self.has_permission(permission):
            raise PermissionError(
                f"权限不足：需要 {permission.value} 权限，当前角色: {self.current_user_role.value if self.current_user_role else 'None'}"
            )
        return True
    
    def get_accessible_features(self) -> Dict[str, bool]:
        """获取当前用户可访问的功能列表"""
        if not self.current_user_role:
            return {}
        
        features = {}
        for permission in Permission:
            features[permission.value] = self.has_permission(permission)
        
        return features
    
    def get_permission_report(self) -> str:
        """生成权限报告"""
        if not self.current_user_role:
            return "❌ 未设置用户角色"
        
        accessible_features = self.get_accessible_features()
        granted = [k for k, v in accessible_features.items() if v]
        denied = [k for k, v in accessible_features.items() if not v]
        
        report = f"🔐 **权限报告**\n"
        report += f"📋 当前角色: {self.current_user_role.value}\n\n"
        
        report += f"✅ **已授权功能** ({len(granted)}):\n"
        for feature in granted:
            report += f"  • {feature}\n"
        
        report += f"\n❌ **受限功能** ({len(denied)}):\n"
        for feature in denied:
            report += f"  • {feature}\n"
        
        return report


# 全局权限管理器实例
permission_manager = PermissionManager()


def require_permission(permission: Permission):
    """装饰器：要求特定权限才能执行函数"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                permission_manager.require_permission(permission)
                return func(*args, **kwargs)
            except PermissionError as e:
                return f"❌ {str(e)}"
        return wrapper
    return decorator


def has_permission(permission: Permission) -> bool:
    """便捷函数：检查是否有权限"""
    return permission_manager.has_permission(permission)


def demo_mode_only(func: Callable):
    """装饰器：仅在演示模式下可用"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not has_permission(Permission.ACCESS_DEMO):
            return f"❌ 此功能仅在演示模式下可用\n💡 使用 set_demo_mode() 启用演示模式"
        return func(*args, **kwargs)
    return wrapper


def production_mode_only(func: Callable):
    """装饰器：仅在生产模式下可用"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if has_permission(Permission.ACCESS_DEMO) and permission_manager.get_current_role() == UserRole.DEMO_USER:
            return f"❌ 此功能在演示模式下不可用\n💡 使用 set_production_mode() 切换到生产模式"
        return func(*args, **kwargs)
    return wrapper


def admin_only(func: Callable):
    """装饰器：仅管理员可用"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not has_permission(Permission.ADMIN_TOOLS):
            return f"❌ 此功能仅管理员可用"
        return func(*args, **kwargs)
    return wrapper 