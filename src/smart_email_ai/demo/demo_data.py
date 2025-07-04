"""演示邮件数据常量"""

from datetime import datetime
from typing import List, Dict, Any

# 演示邮件数据集
DEMO_EMAILS_DATA: List[Dict[str, Any]] = [
    {
        "id": "demo_001",
        "metadata": {
            "sender": "sarah.chen@company.com",
            "subject": "URGENT: Client presentation moved to tomorrow - Need your input ASAP",
            "date": "2025-06-03T09:15:00Z",
            "category": "work",
            "expected_priority": 5,
            "demo_tags": ["urgent", "work", "deadline"]
        },
        "content": {
            "body": """Hi User,

I hope this email finds you well. Unfortunately, I have some urgent news regarding our Q2 client presentation.

The client has requested to move our presentation from Friday to TOMORROW (Thursday) at 2:00 PM. This is extremely critical for closing the deal worth $2.5M.

ACTION REQUIRED:
- Please review the updated slides (attached) and provide feedback by 6 PM today
- Confirm your availability for tomorrow's presentation
- Prepare the financial projections section you're responsible for

This is a make-or-break moment for our team. I know it's short notice, but your expertise is crucial for this presentation.

Please reply ASAP to confirm you can make it work.

Best regards,
Sarah Chen
Director of Sales""",
            "expected_analysis": {
                "action_items": ["review slides", "confirm availability", "prepare financial projections"],
                "deadline": "6 PM today",
                "urgency_score": 1.0,
                "sentiment": "urgent"
            }
        }
    },
    {
        "id": "demo_002",
        "metadata": {
            "sender": "security-alert@company.com",
            "subject": "⚠️ SECURITY BREACH DETECTED - Immediate Action Required",
            "date": "2025-06-03T11:20:00Z",
            "category": "security",
            "expected_priority": 5,
            "demo_tags": ["security", "urgent", "critical"]
        },
        "content": {
            "body": """SECURITY ALERT - CONFIDENTIAL

We have detected unauthorized access attempts on your company account from the following IP: 192.168.1.100

IMMEDIATE ACTIONS REQUIRED:
1. Change your password within the next 2 hours
2. Review your recent login activity at security.company.com
3. Report any suspicious emails to security@company.com
4. Enable two-factor authentication if not already active

FAILURE TO COMPLY WITHIN 2 HOURS WILL RESULT IN ACCOUNT SUSPENSION.

Do not forward this email. Do not ignore this warning.

If you did not authorize these login attempts, respond immediately.

Security Operations Team
Company IT Security""",
            "expected_analysis": {
                "action_items": ["change password", "review login activity", "report suspicious emails", "enable 2FA"],
                "deadline": "2 hours",
                "urgency_score": 1.0,
                "sentiment": "critical"
            }
        }
    },
    {
        "id": "demo_003",
        "metadata": {
            "sender": "newsletter@techcompany.com",
            "subject": "🎉 25% OFF Everything - Limited Time Offer!",
            "date": "2025-06-03T15:30:00Z",
            "category": "marketing",
            "expected_priority": 1,
            "demo_tags": ["marketing", "promotional", "low_priority"]
        },
        "content": {
            "body": """Don't Miss Out on Our Biggest Sale of the Year!

For a limited time only, get 25% OFF on all our premium products and services.

🎯 What's included:
- All software licenses
- Training courses
- Consulting services
- Premium support packages

Use code: SAVE25NOW

This offer expires in 48 hours. Shop now and save big!

Click here to start shopping: www.techcompany.com/sale

Questions? Reply to this email or call 1-800-TECH-HELP

Best regards,
The TechCompany Team""",
            "expected_analysis": {
                "action_items": [],
                "deadline": "48 hours",
                "urgency_score": 0.2,
                "sentiment": "promotional"
            }
        }
    },
    {
        "id": "demo_004",
        "metadata": {
            "sender": "project-manager@company.com",
            "subject": "Weekly Project Status - Action Items for Next Week",
            "date": "2025-06-03T16:45:00Z",
            "category": "work",
            "expected_priority": 3,
            "demo_tags": ["project", "weekly", "routine"]
        },
        "content": {
            "body": """Hi Team,

Here's our weekly project status update for Project Phoenix:

📊 Current Progress: 75% Complete
🎯 On Track for June 30th deadline

Completed This Week:
✅ Database migration (User)
✅ UI mockups approved (Design team)
✅ API testing phase 1 (Dev team)

Action Items for Next Week:
🔄 User: Finalize performance optimization
🔄 Design: Create final assets
🔄 QA: Begin integration testing

Blockers:
⚠️ Still waiting for client feedback on payment gateway integration

Next meeting: Monday 10 AM

Let me know if you have any concerns.

Best,
Mike Johnson
Project Manager""",
            "expected_analysis": {
                "action_items": ["finalize performance optimization"],
                "deadline": "next week",
                "urgency_score": 0.6,
                "sentiment": "neutral"
            }
        }
    },
    {
        "id": "demo_005",
        "metadata": {
            "sender": "no-reply@accounts.google.com",
            "subject": "安全提醒：在 Mac 设备上有新的登录活动",
            "date": "2025-06-11T09:30:00Z",
            "category": "security",
            "expected_priority": 4,
            "demo_tags": ["security", "notification", "google"]
        },
        "content": {
            "body": """我们发现您的 Google 账号 (user@example.com) 在一部 Mac 设备上有新的登录活动。
如果这是您本人的操作，则无需采取任何行动。
如果这不是您本人的操作，我们会帮助您保护您的账号。

查看活动
您也可以访问以下网址查看安全性活动：
https://myaccount.google.com/notifications""",
            "expected_analysis": {
                "action_items": ["check recent activity"],
                "deadline": None,
                "urgency_score": 0.7,
                "sentiment": "security"
            }
        }
    }
]

# 演示配置数据
DEMO_CONFIG: Dict[str, Any] = {
    "total_emails": len(DEMO_EMAILS_DATA),
    "categories": list(set(email["metadata"]["category"] for email in DEMO_EMAILS_DATA)),
    "priority_distribution": {
        1: len([e for e in DEMO_EMAILS_DATA if e["metadata"]["expected_priority"] == 1]),
        2: len([e for e in DEMO_EMAILS_DATA if e["metadata"]["expected_priority"] == 2]),
        3: len([e for e in DEMO_EMAILS_DATA if e["metadata"]["expected_priority"] == 3]),
        4: len([e for e in DEMO_EMAILS_DATA if e["metadata"]["expected_priority"] == 4]),
        5: len([e for e in DEMO_EMAILS_DATA if e["metadata"]["expected_priority"] == 5]),
    },
    "demo_features": [
        "紧急工作邮件处理",
        "安全警报响应",
        "营销邮件过滤",
        "项目管理协作",
        "账户安全通知"
    ]
} 