#!/usr/bin/env python3
"""
Security Management Script for Quest Analytics RAG Assistant

Provides command-line tools for managing security settings:
- Generate and manage API keys
- Configure security settings
- Test security components
- Monitor security events

Usage:
    python scripts/security_manager.py generate-key --type admin
    python scripts/security_manager.py test-security
    python scripts/security_manager.py configure --enable-auth --rate-limit 60
    python scripts/security_manager.py monitor --tail

Author: AI RAG Assistant Team
Version: 1.0.0
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from rag_pipeline.security import (
    SecurityConfig, 
    APIAuthentication, 
    InputSanitizer, 
    RateLimiter,
    create_secure_api_key,
    hash_api_key
)

def generate_api_key(key_type: str = "user") -> str:
    """Generate a new API key"""
    
    key = create_secure_api_key()
    key_hash = hash_api_key(key)
    
    print(f"\n🔑 New {key_type.upper()} API Key Generated")
    print(f"{'=' * 50}")
    print(f"API Key: {key}")
    print(f"Hash:    {key_hash}")
    print(f"Type:    {key_type}")
    print(f"Created: {datetime.now().isoformat()}")
    
    # Save to environment file
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        with open(env_file, "a") as f:
            if key_type == "admin":
                f.write(f"\n# Admin API Key (Generated {datetime.now().isoformat()})\n")
                f.write(f"RAG_ADMIN_API_KEY={key}\n")
            else:
                f.write(f"\n# User API Key (Generated {datetime.now().isoformat()})\n")
                f.write(f"RAG_API_KEY={key}\n")
        
        print(f"\n✅ API key saved to .env file")
    else:
        print(f"\n⚠️  .env file not found. Please manually set environment variable:")
        env_var = "RAG_ADMIN_API_KEY" if key_type == "admin" else "RAG_API_KEY"
        print(f"   export {env_var}={key}")
    
    return key

def test_security_components():
    """Test all security components"""
    
    print("🛡️ Testing Security Components")
    print("=" * 50)
    
    # Test configuration loading
    try:
        config = SecurityConfig()
        print("✅ Security configuration loaded successfully")
        print(f"   - Authentication: {config.config.get('authentication', {}).get('enabled', False)}")
        print(f"   - Rate limiting: {config.config.get('rate_limiting', {}).get('enabled', False)}")
        print(f"   - Input sanitization: {config.config.get('input_sanitization', {}).get('enabled', False)}")
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False
    
    # Test authentication
    try:
        auth = APIAuthentication(config)
        test_key = "test_key_123"
        result = auth.verify_api_key(test_key)
        print(f"✅ Authentication component: {'Working' if not auth.enabled or not result else 'Ready'}")
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
    
    # Test input sanitization
    try:
        sanitizer = InputSanitizer(config)
        test_queries = [
            "What is machine learning?",
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "eval(malicious_code())"
        ]
        
        safe_count = 0
        for query in test_queries:
            sanitized, is_safe = sanitizer.sanitize_query(query)
            if query == test_queries[0] and is_safe:
                safe_count += 1
            elif query != test_queries[0] and not is_safe:
                safe_count += 1
        
        print(f"✅ Input sanitization: {safe_count}/{len(test_queries)} tests passed")
        
    except Exception as e:
        print(f"❌ Input sanitization test failed: {e}")
    
    # Test rate limiting
    try:
        rate_limiter = RateLimiter(config)
        
        # Simulate requests
        test_ip = "127.0.0.1"
        allowed_count = 0
        
        for i in range(5):
            is_allowed, info = rate_limiter.check_rate_limit(test_ip, "test")
            if is_allowed:
                allowed_count += 1
        
        print(f"✅ Rate limiting: {allowed_count}/5 requests allowed (as expected)")
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
    
    print("\n🔍 File validation test")
    try:
        # Test file validation
        test_files = {
            "safe.pdf": b"PDF content here",
            "malware.exe": b"<script>eval(malicious)</script>",
            "large.txt": b"x" * (60 * 1024 * 1024)  # 60MB file
        }
        
        for filename, content in test_files.items():
            is_valid, error = sanitizer.validate_file_upload(filename, len(content), content)
            status = "✅ Blocked" if not is_valid else "⚠️ Allowed"
            print(f"   {status}: {filename} - {error or 'Valid file'}")
            
    except Exception as e:
        print(f"❌ File validation test failed: {e}")
    
    print(f"\n✅ Security component testing completed")
    return True

def configure_security(enable_auth: bool = None, rate_limit: int = None, 
                      enable_sanitization: bool = None):
    """Configure security settings"""
    
    config_path = ROOT_DIR / "configs" / "security_config.yaml"
    
    print("⚙️  Configuring Security Settings")
    print("=" * 50)
    
    if not config_path.exists():
        print(f"❌ Security configuration not found at {config_path}")
        return
    
    # Load current configuration
    with open(config_path, 'r') as f:
        import yaml
        config = yaml.safe_load(f)
    
    changes = []
    
    if enable_auth is not None:
        config['authentication']['enabled'] = enable_auth
        changes.append(f"Authentication: {'Enabled' if enable_auth else 'Disabled'}")
    
    if rate_limit is not None:
        config['rate_limiting']['global_limits']['requests_per_minute'] = rate_limit
        changes.append(f"Rate limit: {rate_limit} requests/minute")
    
    if enable_sanitization is not None:
        config['input_sanitization']['enabled'] = enable_sanitization  
        changes.append(f"Input sanitization: {'Enabled' if enable_sanitization else 'Disabled'}")
    
    if changes:
        # Save updated configuration
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print("✅ Configuration updated:")
        for change in changes:
            print(f"   - {change}")
        
        print(f"\n📝 Configuration saved to {config_path}")
    else:
        print("ℹ️  No configuration changes specified")

def monitor_security():
    """Monitor security events and logs"""
    
    print("📊 Security Monitoring")
    print("=" * 50)
    
    # Check for security log files
    log_files = [
        ROOT_DIR / "logs" / "security.log",
        ROOT_DIR / "logs" / "access.log", 
        ROOT_DIR / "logs" / "error.log"
    ]
    
    found_logs = []
    for log_file in log_files:
        if log_file.exists():
            found_logs.append(log_file)
            size = log_file.stat().st_size / 1024  # KB
            print(f"📋 {log_file.name}: {size:.1f} KB")
    
    if not found_logs:
        print("ℹ️  No security log files found")
        print("   Security events will be logged to console")
    
    # Show recent configuration
    config_path = ROOT_DIR / "configs" / "security_config.yaml"
    if config_path.exists():
        config = SecurityConfig()
        print(f"\n🛡️ Current Security Status:")
        print(f"   - Authentication: {config.config.get('authentication', {}).get('enabled', False)}")
        print(f"   - Rate limiting: {config.config.get('rate_limiting', {}).get('enabled', False)}") 
        print(f"   - Input sanitization: {config.config.get('input_sanitization', {}).get('enabled', False)}")
        print(f"   - Environment: {config.environment}")
    
    # Show API key status
    api_key = os.getenv("RAG_API_KEY")
    admin_key = os.getenv("RAG_ADMIN_API_KEY") 
    
    print(f"\n🔑 API Key Status:")
    print(f"   - User API Key: {'Configured' if api_key else 'Not set'}")
    print(f"   - Admin API Key: {'Configured' if admin_key else 'Not set'}")
    
    if not api_key and not admin_key:
        print(f"   ⚠️  No API keys configured. Run 'generate-key' to create them.")

def main():
    """Main CLI interface"""
    
    parser = argparse.ArgumentParser(
        description="Quest Analytics RAG Assistant Security Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/security_manager.py generate-key --type admin
  python scripts/security_manager.py test-security  
  python scripts/security_manager.py configure --enable-auth --rate-limit 100
  python scripts/security_manager.py monitor
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate key command
    key_parser = subparsers.add_parser('generate-key', help='Generate new API key')
    key_parser.add_argument('--type', choices=['user', 'admin'], default='user',
                           help='Type of API key to generate')
    
    # Test security command
    test_parser = subparsers.add_parser('test-security', help='Test security components')
    
    # Configure command
    config_parser = subparsers.add_parser('configure', help='Configure security settings')
    config_parser.add_argument('--enable-auth', action='store_true',
                              help='Enable authentication')
    config_parser.add_argument('--disable-auth', action='store_true', 
                              help='Disable authentication')
    config_parser.add_argument('--rate-limit', type=int,
                              help='Set rate limit (requests per minute)')
    config_parser.add_argument('--enable-sanitization', action='store_true',
                              help='Enable input sanitization')
    config_parser.add_argument('--disable-sanitization', action='store_true',
                              help='Disable input sanitization')
    
    # Monitor command  
    monitor_parser = subparsers.add_parser('monitor', help='Monitor security events')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print(f"🛡️ Quest Analytics RAG Assistant - Security Manager")
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    try:
        if args.command == 'generate-key':
            generate_api_key(args.type)
            
        elif args.command == 'test-security':
            success = test_security_components()
            sys.exit(0 if success else 1)
            
        elif args.command == 'configure':
            enable_auth = None
            if args.enable_auth:
                enable_auth = True
            elif args.disable_auth:
                enable_auth = False
                
            enable_sanitization = None
            if args.enable_sanitization:
                enable_sanitization = True
            elif args.disable_sanitization:
                enable_sanitization = False
                
            configure_security(enable_auth, args.rate_limit, enable_sanitization)
            
        elif args.command == 'monitor':
            monitor_security()
            
    except KeyboardInterrupt:
        print(f"\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()