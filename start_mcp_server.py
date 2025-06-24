#!/usr/bin/env python3
"""
Smart Email AI MCP服务器启动脚本
解决相对导入问题，提供稳定的服务器启动
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 现在可以正常导入模块
from src.smart_email_ai.main import mcp

def main():
    """启动MCP服务器"""
    print("🚀 启动Smart Email AI MCP服务器...")
    print("📡 等待Claude Desktop连接...")
    
    try:
        # 启动MCP服务器
        mcp.run()
    except KeyboardInterrupt:
        print("\n👋 服务器已安全关闭")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 