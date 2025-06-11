#!/usr/bin/env python3
"""
Smart Email AI - 项目主入口

使用方法:
    python main.py                     # 启动交互式演示
    python main.py --demo              # 运行演示模式  
    python main.py --analyze <email>   # 分析指定邮件
    python main.py --test              # 运行测试
"""

import sys
import argparse
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from smart_email_ai import RefactoredEmailSystem


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="Smart Email AI - 智能邮件分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py                    # 交互式模式
  python main.py --demo             # 演示模式
  python main.py --analyze file.html    # 分析邮件文件
  python main.py --test             # 运行系统测试
        """
    )
    
    parser.add_argument(
        "--demo", 
        action="store_true", 
        help="运行演示模式，分析内置演示邮件"
    )
    
    parser.add_argument(
        "--analyze", 
        type=str, 
        metavar="EMAIL_FILE",
        help="分析指定的邮件文件"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="运行系统功能测试"
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="data/config.yaml",
        help="指定配置文件路径 (默认: data/config.yaml)"
    )
    
    args = parser.parse_args()
    
    try:
        system = RefactoredEmailSystem()
        
        if args.demo:
            print("🚀 启动演示模式...")
            demo_result = system.run_demo_analysis()
            print(demo_result)  # 显示演示结果
            print("\n" + "="*50)
            print("演示完成！查看上述分析结果。")
            
        elif args.analyze:
            email_file = Path(args.analyze)
            if not email_file.exists():
                print(f"❌ 邮件文件不存在: {email_file}")
                return 1
                
            print(f"📧 分析邮件文件: {email_file}")
            with open(email_file, 'r', encoding='utf-8') as f:
                email_content = f.read()
            
            result = system.analyze_single_email(email_content)
            print("\n分析结果:")
            print(result)
            
        elif args.test:
            print("🧪 运行系统测试...")
            test_result = system.run_system_tests()
            print(test_result)
            
        else:
            # 交互式模式
            print("🤖 欢迎使用 Smart Email AI!")
            print("=" * 50)
            system.show_system_info()
            print("\n可用命令:")
            print("  --demo    : 运行演示")
            print("  --analyze : 分析邮件文件")
            print("  --test    : 运行测试")
            print("  --help    : 查看帮助")
            
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 