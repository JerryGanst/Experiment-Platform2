"""用户角色和权限定义"""

from enum import Enum
from typing import Set, List
from dataclasses import dataclass


class Permission(Enum):
    """权限枚举"""
    # 基础权限
    READ_EMAILS = "read_emails"
    SEND_EMAILS = "send_emails"
    SEARCH_EMAILS = "search_emails"
    
    # 高级权限
    MANAGE_CACHE = "manage_cache"
    EXPORT_DATA = "export_data"
    SYSTEM_CONFIG = "system_config"
    
    # 演示权限
    ACCESS_DEMO = "access_demo"
    MANAGE_DEMO = "manage_demo"
    
    # 管理权限
    ADMIN_TOOLS = "admin_tools"
    DEBUG_MODE = "debug_mode"
    
    # 连接权限
    CONNECT_ICLOUD = "connect_icloud"
    CONNECT_GMAIL = "connect_gmail"
    CONNECT_OUTLOOK = "connect_outlook"


class UserRole(Enum):
    """用户角色枚举"""
    GUEST = "guest"           # 访客 - 最低权限
    DEMO_USER = "demo_user"   # 演示用户 - 只能使用演示功能
    BASIC_USER = "basic_user" # 基础用户 - 基本邮件功能
    POWER_USER = "power_user" # 高级用户 - 完整邮件功能
    ADMIN = "admin"           # 管理员 - 全部权限


@dataclass
class RolePermissions:
    """角色权限映射"""
    role: UserRole
    permissions: Set[Permission]
    description: str


# 权限配置
ROLE_PERMISSIONS = {
    UserRole.GUEST: RolePermissions(
        role=UserRole.GUEST,
        permissions={
            Permission.READ_EMAILS,
        },
        description="访客用户，只能读取邮件"
    ),
    
    UserRole.DEMO_USER: RolePermissions(
        role=UserRole.DEMO_USER,
        permissions={
            Permission.READ_EMAILS,
            Permission.ACCESS_DEMO,
            Permission.SEARCH_EMAILS,
        },
        description="演示用户，只能使用演示功能"
    ),
    
    UserRole.BASIC_USER: RolePermissions(
        role=UserRole.BASIC_USER,
        permissions={
            Permission.READ_EMAILS,
            Permission.SEND_EMAILS,
            Permission.SEARCH_EMAILS,
            Permission.CONNECT_ICLOUD,
            Permission.CONNECT_GMAIL,
            Permission.CONNECT_OUTLOOK,
        },
        description="基础用户，基本邮件功能"
    ),
    
    UserRole.POWER_USER: RolePermissions(
        role=UserRole.POWER_USER,
        permissions={
            Permission.READ_EMAILS,
            Permission.SEND_EMAILS,
            Permission.SEARCH_EMAILS,
            Permission.MANAGE_CACHE,
            Permission.EXPORT_DATA,
            Permission.CONNECT_ICLOUD,
            Permission.CONNECT_GMAIL,
            Permission.CONNECT_OUTLOOK,
            Permission.ACCESS_DEMO,
        },
        description="高级用户，完整邮件功能"
    ),
    
    UserRole.ADMIN: RolePermissions(
        role=UserRole.ADMIN,
        permissions=set(Permission),  # 所有权限
        description="管理员，拥有全部权限"
    )
}


def get_role_permissions(role: UserRole) -> Set[Permission]:
    """获取角色的权限集合"""
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(user_role: UserRole, permission: Permission) -> bool:
    """检查用户角色是否有指定权限"""
    role_perms = get_role_permissions(user_role)
    return permission in role_perms.permissions if role_perms else False


def get_available_roles() -> List[UserRole]:
    """获取所有可用的角色"""
    return list(UserRole) 