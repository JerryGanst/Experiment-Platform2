#!/usr/bin/env python3
"""
Smart Email AI - 快速开始示例

演示如何使用Smart Email AI的主要功能
"""

import sys
from pathlib import Path

# 添加src路径
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path / "src"))

from smart_email_ai import RefactoredEmailSystem, EmailData


def main():
    """快速开始示例"""
    print("🚀 Smart Email AI 快速开始")
    print("=" * 50)
    
    # 1. 初始化系统
    system = RefactoredEmailSystem()
    
    # 2. 显示系统信息
    print("\n📊 系统信息:")
    system.show_system_info()
    
    # 3. 加载演示邮件
    print("\n📧 加载演示邮件...")
    from smart_email_ai import email_data_manager
    demo_emails = email_data_manager.load_demo_emails()
    print(f"✅ 加载了 {len(demo_emails)} 封演示邮件")
    
    # 4. 分析第一封邮件
    if demo_emails:
        print("\n🔍 分析第一封邮件:")
        first_email = demo_emails[0]
        print(f"主题: {first_email.subject}")
        print(f"发件人: {first_email.sender}")
        
        # 进行AI分析
        analysis = system.analyze_email_priority(first_email.body)
        print(f"\n分析结果:")
        print(f"• 优先级: {analysis.get('priority', 'N/A')}")
        print(f"• 情感倾向: {analysis.get('sentiment', 'N/A')}")
        print(f"• 关键特征: {', '.join(analysis.get('key_features', []))}")
    
    # 5. 解析Outlook邮件示例
    print("\n🔧 Outlook邮件解析器演示:")
    from smart_email_ai import OutlookEmailParser
    
    parser = OutlookEmailParser()
    
    # 示例HTML邮件内容
    sample_html = """
    <html>
    <body>
        <p>Dear Team,</p>
        <p>Please find the quarterly report below:</p>
        <table border="1">
            <tr><th>Quarter</th><th>Revenue</th></tr>
            <tr><td>Q1</td><td>$100K</td></tr>
            <tr><td>Q2</td><td>$120K</td></tr>
        </table>
        <p>Best regards,<br>Manager</p>
        
        <div style="border-top:solid #E1E1E1 1.0pt">
        <p>-----原始邮件-----</p>
        <p>发件人: john@company.com</p>
        <p>主题: Q2 Numbers</p>
        <p>The Q2 revenue exceeded expectations!</p>
        </div>
    </body>
    </html>
    """
    
    parsed_email = parser.parse_email(sample_html)
    markdown_result = parser.format_to_markdown(parsed_email)
    
    print("解析结果（Markdown格式）:")
    print(markdown_result[:500] + "..." if len(markdown_result) > 500 else markdown_result)
    
    print("\n🎉 快速开始演示完成！")
    print("\n💡 下一步:")
    print("  1. 运行完整演示: python main.py --demo")
    print("  2. 分析自己的邮件: python main.py --analyze your_email.html")
    print("  3. 查看完整文档: docs/README.md")


if __name__ == "__main__":
    main() 