#!/usr/bin/env python3
"""
Comprehensive Email Diagnostic
Checks all aspects of the email system including configuration, connectivity, and functionality
"""

import sys
import os
import socket
import smtplib
import ssl
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_system_environment():
    """Check system environment and dependencies"""
    print("=== SYSTEM ENVIRONMENT CHECK ===\n")
    
    # Check Python version
    print(f"🐍 Python Version: {sys.version}")
    
    # Check if we're in the right directory
    current_dir = os.getcwd()
    print(f"📁 Current Directory: {current_dir}")
    
    # Check if src directory exists
    src_path = os.path.join(current_dir, 'src')
    if os.path.exists(src_path):
        print("✅ src/ directory found")
    else:
        print("❌ src/ directory not found")
        return False
    
    # Check if data directory exists
    data_path = os.path.join(current_dir, 'data')
    if os.path.exists(data_path):
        print("✅ data/ directory found")
    else:
        print("❌ data/ directory not found")
    
    return True

def check_configuration_files():
    """Check configuration files"""
    print(f"\n=== CONFIGURATION FILES CHECK ===\n")
    
    config_files = [
        'data/config.yaml',
        'data/demo_emails.json'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            size = os.path.getsize(config_file)
            print(f"✅ {config_file} - {size} bytes")
        else:
            print(f"❌ {config_file} - Not found")
    
    # Check for email cache database
    cache_db = 'data/email_cache.db'
    if os.path.exists(cache_db):
        size = os.path.getsize(cache_db)
        print(f"✅ {cache_db} - {size} bytes")
    else:
        print(f"⚠️ {cache_db} - Not found (will be created on first use)")

def check_network_connectivity():
    """Check network connectivity to email servers"""
    print(f"\n=== NETWORK CONNECTIVITY TEST ===\n")
    
    email_servers = [
        ('smtp.mail.me.com', 587, 'iCloud'),
        ('smtp.gmail.com', 587, 'Gmail'),
        ('smtp.office365.com', 587, 'Outlook'),
        ('smtp.qq.com', 587, 'QQ Mail'),
        ('smtp.163.com', 587, '163 Mail')
    ]
    
    results = {}
    
    for server, port, provider in email_servers:
        try:
            print(f"🔌 Testing {provider} ({server}:{port})...")
            
            # Test basic socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((server, port))
            sock.close()
            
            if result == 0:
                print(f"   ✅ {provider} - Connection successful")
                results[provider] = True
            else:
                print(f"   ❌ {provider} - Connection failed (error: {result})")
                results[provider] = False
                
        except Exception as e:
            print(f"   ❌ {provider} - Connection error: {e}")
            results[provider] = False
    
    return results

def check_email_module_imports():
    """Check if email modules can be imported"""
    print(f"\n=== EMAIL MODULE IMPORT CHECK ===\n")
    
    modules_to_test = [
        ('smtplib', 'SMTP library'),
        ('email.mime.text', 'MIME text'),
        ('email.mime.multipart', 'MIME multipart'),
        ('ssl', 'SSL/TLS support')
    ]
    
    import_results = {}
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name} - {description}")
            import_results[module_name] = True
        except ImportError as e:
            print(f"❌ {module_name} - {description} (Error: {e})")
            import_results[module_name] = False
    
    # Try to import our custom modules
    try:
        from smart_email_ai.core.email_sender import EmailSender
        print("✅ smart_email_ai.core.email_sender - EmailSender class")
        import_results['EmailSender'] = True
    except ImportError as e:
        print(f"❌ smart_email_ai.core.email_sender - EmailSender class (Error: {e})")
        import_results['EmailSender'] = False
    
    try:
        from smart_email_ai.core.email_sender import email_sender
        print(f"✅ smart_email_ai.core.email_sender - Global email_sender (is None: {email_sender is None})")
        import_results['email_sender'] = email_sender is not None
    except ImportError as e:
        print(f"❌ smart_email_ai.core.email_sender - Global email_sender (Error: {e})")
        import_results['email_sender'] = False
    
    return import_results

def test_smtp_connection_with_credentials(email, password, provider="icloud"):
    """Test SMTP connection with actual credentials"""
    print(f"\n=== SMTP CONNECTION TEST WITH CREDENTIALS ===\n")
    
    if email == "your_email@icloud.com" or password == "your_app_password":
        print("⚠️ Using placeholder credentials - skipping actual connection test")
        print("💡 Update credentials in the script to test real connection")
        return False
    
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
        server.login(email, password)
        
        print("✅ SMTP connection successful!")
        print(f"   Server: {config['server']}")
        print(f"   Port: {config['port']}")
        print(f"   TLS: {config['use_tls']}")
        print(f"   Email: {email}")
        
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

def check_email_system_status():
    """Check the overall email system status"""
    print(f"\n=== EMAIL SYSTEM STATUS ===\n")
    
    try:
        from smart_email_ai.core.email_sender import email_sender
        
        if email_sender is None:
            print("❌ Global email_sender is None")
            print("💡 No default email sender configured")
            print("💡 Use configure_default_email_sender() to set up")
            return False
        else:
            print("✅ Global email_sender is configured")
            print(f"   📧 Email: {email_sender.email_address}")
            print(f"   🌐 Provider: {email_sender.provider}")
            print(f"   🔧 Server: {email_sender.smtp_config[email_sender.provider]['server']}")
            return True
            
    except Exception as e:
        print(f"❌ Error checking email system status: {e}")
        return False

def generate_diagnostic_report():
    """Generate a comprehensive diagnostic report"""
    print(f"\n{'='*60}")
    print("COMPREHENSIVE EMAIL DIAGNOSTIC REPORT")
    print(f"{'='*60}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Run all diagnostic checks
    env_ok = check_system_environment()
    check_configuration_files()
    network_results = check_network_connectivity()
    import_results = check_email_module_imports()
    
    # Test with placeholder credentials (won't actually connect)
    test_smtp_connection_with_credentials("your_email@icloud.com", "your_app_password")
    
    # Check email system status
    email_system_ok = check_email_system_status()
    
    # Summary
    print(f"\n{'='*60}")
    print("DIAGNOSTIC SUMMARY")
    print(f"{'='*60}")
    
    # Network connectivity summary
    working_servers = sum(1 for result in network_results.values() if result)
    total_servers = len(network_results)
    print(f"🌐 Network Connectivity: {working_servers}/{total_servers} servers reachable")
    
    # Module imports summary
    working_modules = sum(1 for result in import_results.values() if result)
    total_modules = len(import_results)
    print(f"📦 Module Imports: {working_modules}/{total_modules} modules available")
    
    # Overall status
    print(f"🔧 System Environment: {'✅ OK' if env_ok else '❌ Issues'}")
    print(f"📧 Email System: {'✅ Configured' if email_system_ok else '❌ Not configured'}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if not email_system_ok:
        print("   1. Configure email credentials using configure_default_email_sender()")
    if working_servers == 0:
        print("   2. Check network connectivity and firewall settings")
    if working_modules < total_modules:
        print("   3. Install missing dependencies")
    
    print("   4. Test with real credentials to verify full functionality")

def main():
    """Main diagnostic function"""
    generate_diagnostic_report()

if __name__ == "__main__":
    main()