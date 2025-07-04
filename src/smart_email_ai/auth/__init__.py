"""权限控制模块"""

from .permission_manager import PermissionManager, require_permission, has_permission
from .roles import UserRole, Permission

__all__ = ['PermissionManager', 'require_permission', 'has_permission', 'UserRole', 'Permission'] 