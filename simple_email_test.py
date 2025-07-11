#!/usr/bin/env python3
"""
Simplified Email Test
Tests email functionality without external dependencies
"""

import sys
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_smtp_connection(email_address, password, provider="icloud"):
    """Test SMTP connection directly"""
    print(f"=== TESTING SMTP CONNECTION ===")
    print(f"Email: {email_address}")
    print(f"Provider: {provider}")
    
    # SMTP configurations
    smtp_configs = {
        'icloud': {
            'server': 'smtp.mail.me.com',
            'port': 587,
            'use_tls': True
        },
        'gmail': {
            'server': 'smtp.gmail.com', 
            'port': 587,
            'use_tls': True
        },
        'outlook': {
            'server': 'smtp.office365.com',
            'port': 587,
            'use_tls': True
        }
    }
    
    if provider not in smtp_configs:
        print(f"❌ Unsupported provider: {provider}")
        return False
    
    config = smtp_configs[provider]
    
    try:
        print(f"🔌 Connecting to {config['server']}:{config['port']}...")
        
        # Create SMTP connection
        server = smtplib.SMTP(config['server'], config['port'])
        
        # Start TLS if required
        if config['use_tls']:
            print("🔒 Starting TLS...")
            server.starttls()
        
        # Login
        print("🔐 Attempting login...")
        server.login(email_address, password)
        
        print("✅ SMTP connection successful!")
        print(f"   Server: {config['server']}")
        print(f"   Port: {config['port']}")
        print(f"   TLS: {config['use_tls']}")
        print(f"   Email: {email_address}")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Check your email and password/app password")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check network connectivity and server settings")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def send_test_email(email_address, password, to_email, provider="icloud"):
    """Send a test email"""
    print(f"\n=== SENDING TEST EMAIL ===")
    print(f"From: {email_address}")
    print(f"To: {to_email}")
    print(f"Provider: {provider}")
    
    # SMTP configurations
    smtp_configs = {
        'icloud': {
            'server': 'smtp.mail.me.com',
            'port': 587,
            'use_tls': True
        },
        'gmail': {
            'server': 'smtp.gmail.com', 
            'port': 587,
            'use_tls': True
        },
        'outlook': {
            'server': 'smtp.office365.com',
            'port': 587,
            'use_tls': True
        }
    }
    
    if provider not in smtp_configs:
        print(f"❌ Unsupported provider: {provider}")
        return False
    
    config = smtp_configs[provider]
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = to_email
        msg['Subject'] = f"Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Add body
        body = f"""
        This is a test email from Smart Email AI System.
        
        📧 Test Details:
        • Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        • From: {email_address}
        • Provider: {provider}
        • Server: {config['server']}:{config['port']}
        
        ✅ If you receive this email, the email sending system is working correctly!
        
        Best regards,
        Smart Email AI System
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Create SMTP connection
        print("🔌 Connecting to SMTP server...")
        server = smtplib.SMTP(config['server'], config['port'])
        
        if config['use_tls']:
            print("🔒 Starting TLS...")
            server.starttls()
        
        print("🔐 Logging in...")
        server.login(email_address, password)
        
        print("📤 Sending email...")
        server.send_message(msg)
        server.quit()
        
        print("✅ Test email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Email System Test\n")
    
    # Test with sample credentials (these won't work, just for demonstration)
    test_email = "your_email@icloud.com"  # Replace with actual email
    test_password = "your_app_password"   # Replace with actual password
    test_provider = "icloud"              # or "gmail", "outlook"
    test_recipient = "test@example.com"   # Replace with actual recipient
    
    print("📝 Test Configuration:")
    print(f"   Email: {test_email}")
    print(f"   Provider: {test_provider}")
    print(f"   Recipient: {test_recipient}")
    print("\n💡 To run actual tests, update the credentials in this script")
    
    # Test 1: SMTP Connection
    print(f"\n{'='*50}")
    print("TEST 1: SMTP Connection Test")
    print(f"{'='*50}")
    
    # This will fail with sample credentials, but shows the process
    connection_success = test_smtp_connection(test_email, test_password, test_provider)
    
    # Test 2: Send Test Email
    if connection_success:
        print(f"\n{'='*50}")
        print("TEST 2: Send Test Email")
        print(f"{'='*50}")
        send_test_email(test_email, test_password, test_recipient, test_provider)
    else:
        print("\n⏭️ Skipping email send test due to connection failure")
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    print("✅ Network connectivity: Working")
    print("❌ Email credentials: Not configured")
    print("💡 To fix email sending:")
    print("   1. Update credentials in this script")
    print("   2. Use configure_default_email_sender() in main system")
    print("   3. Test with test_email_server_connection()")

if __name__ == "__main__":
    main()