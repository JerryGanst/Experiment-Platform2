#!/usr/bin/env python3
"""
Email Diagnostic Script
Checks email configuration and connection status
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_email_configuration():
    """Check email configuration status"""
    print("=== EMAIL CONFIGURATION DIAGNOSTIC ===\n")
    
    try:
        # Check if email_sender module can be imported
        from smart_email_ai.core.email_sender import email_sender, EmailSender
        print("✅ Email sender module imported successfully")
        
        # Check global email_sender status
        print(f"\n📧 Global email_sender status:")
        print(f"   email_sender is None: {email_sender is None}")
        
        if email_sender is None:
            print("   ❌ No default email sender configured")
            print("   💡 Use configure_default_email_sender(email, password) to set up")
        else:
            print(f"   ✅ Email sender configured")
            print(f"   📧 Email: {email_sender.email_address}")
            print(f"   🌐 Provider: {email_sender.provider}")
            print(f"   🔧 Server: {email_sender.smtp_config[email_sender.provider]['server']}")
            print(f"   🔌 Port: {email_sender.smtp_config[email_sender.provider]['port']}")
            print(f"   🔒 TLS: {email_sender.smtp_config[email_sender.provider]['use_tls']}")
        
        # Test EmailSender class functionality
        print(f"\n🔧 EmailSender class test:")
        try:
            # Test creating an instance (without actually connecting)
            test_sender = EmailSender(
                email_address="test@example.com", 
                password="test_password",
                provider="icloud"
            )
            print("   ✅ EmailSender class instantiation successful")
            print(f"   📧 Test email: {test_sender.email_address}")
            print(f"   🌐 Test provider: {test_sender.provider}")
            print(f"   🔧 Test server config: {test_sender.smtp_config[test_sender.provider]}")
        except Exception as e:
            print(f"   ❌ EmailSender instantiation failed: {e}")
        
        # Check SMTP configuration
        print(f"\n🌐 SMTP Configuration:")
        smtp_configs = {
            'icloud': {'server': 'smtp.mail.me.com', 'port': 587, 'use_tls': True},
            'gmail': {'server': 'smtp.gmail.com', 'port': 587, 'use_tls': True},
            'outlook': {'server': 'smtp.office365.com', 'port': 587, 'use_tls': True}
        }
        
        for provider, config in smtp_configs.items():
            print(f"   {provider.upper()}: {config['server']}:{config['port']} (TLS: {config['use_tls']})")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Missing dependencies - install required packages")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_network_connectivity():
    """Check basic network connectivity to email servers"""
    print(f"\n=== NETWORK CONNECTIVITY TEST ===\n")
    
    import socket
    
    email_servers = [
        ('smtp.mail.me.com', 587),  # iCloud
        ('smtp.gmail.com', 587),    # Gmail
        ('smtp.office365.com', 587) # Outlook
    ]
    
    for server, port in email_servers:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((server, port))
            sock.close()
            
            if result == 0:
                print(f"✅ {server}:{port} - Connection successful")
            else:
                print(f"❌ {server}:{port} - Connection failed (error code: {result})")
        except Exception as e:
            print(f"❌ {server}:{port} - Connection error: {e}")

def main():
    """Main diagnostic function"""
    print("🚀 Starting Email System Diagnostic...\n")
    
    # Check configuration
    config_ok = check_email_configuration()
    
    # Check network connectivity
    check_network_connectivity()
    
    # Summary
    print(f"\n=== DIAGNOSTIC SUMMARY ===")
    if config_ok:
        print("✅ Configuration check completed")
        print("💡 To test email sending, you need to:")
        print("   1. Configure email credentials using configure_default_email_sender()")
        print("   2. Test connection using test_email_server_connection()")
        print("   3. Send test email using send_email()")
    else:
        print("❌ Configuration check failed")
        print("💡 Fix import issues before proceeding")

if __name__ == "__main__":
    main()