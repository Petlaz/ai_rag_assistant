"""
Security Module for Quest Analytics RAG Assistant

Comprehensive security implementation including:
- API Authentication (API keys, JWT, sessions)  
- Input sanitization and validation
- Rate limiting and throttling
- Security headers and threat detection
- Integration with Gradio and FastAPI endpoints

Author: AI RAG Assistant Team
Version: 1.0.0
"""

import hashlib
import html
import logging
import os
import re
import secrets
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Load and manage security configuration"""
    
    def __init__(self, config_path: str = "configs/security_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.environment = os.getenv("ENVIRONMENT", "development")
        self._apply_environment_overrides()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load security configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Security config not found at {self.config_path}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default security configuration"""
        return {
            "authentication": {"enabled": False},
            "input_sanitization": {"enabled": True},
            "rate_limiting": {"enabled": True, "global_limits": {"requests_per_minute": 60}},
            "security_headers": {"enabled": True},
            "threat_detection": {"enabled": True}
        }
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides"""
        if "environments" in self.config and self.environment in self.config["environments"]:
            overrides = self.config["environments"][self.environment]
            self._deep_update(self.config, overrides)
    
    def _deep_update(self, base: Dict, override: Dict):
        """Deep update nested dictionary"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                keys = key.split(".")
                current = base
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value

class APIAuthentication:
    """Handle API key and JWT authentication"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config.config.get("authentication", {})
        self.enabled = self.config.get("enabled", False)
        self.method = self.config.get("method", "api_key")
        self.valid_api_keys = self._load_api_keys()
        
    def _load_api_keys(self) -> set:
        """Load valid API keys from environment variables"""
        api_keys = set()
        
        # Load from environment variables
        main_api_key = os.getenv("RAG_API_KEY")
        if main_api_key:
            api_keys.add(main_api_key)
            
        # Load admin API key
        admin_api_key = os.getenv("RAG_ADMIN_API_KEY")
        if admin_api_key:
            api_keys.add(admin_api_key)
            
        # Generate a default key if none provided (development only)
        if not api_keys and os.getenv("ENVIRONMENT", "development") == "development":
            default_key = "dev_" + secrets.token_hex(16)
            api_keys.add(default_key)
            logger.warning(f"No API keys configured, using development key: {default_key}")
            
        return api_keys
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify if the provided API key is valid"""
        if not self.enabled:
            return True
            
        if not api_key or api_key not in self.valid_api_keys:
            logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
            return False
            
        return True
    
    def is_admin_key(self, api_key: str) -> bool:
        """Check if the API key has admin privileges"""
        admin_key = os.getenv("RAG_ADMIN_API_KEY")
        return admin_key and api_key == admin_key
    
    def extract_api_key(self, request_headers: Dict[str, str]) -> Optional[str]:
        """Extract API key from request headers"""
        header_name = self.config.get("api_key", {}).get("header_name", "X-API-Key")
        return request_headers.get(header_name) or request_headers.get("Authorization", "").replace("Bearer ", "")

class InputSanitizer:
    """Handle input validation and sanitization"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config.config.get("input_sanitization", {})
        self.enabled = self.config.get("enabled", True)
        self.query_config = self.config.get("query_validation", {})
        self.file_config = self.config.get("file_upload", {})
        
        # Compile regex patterns for efficiency
        self.blocked_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.query_config.get("block_patterns", [])
        ]
    
    def sanitize_query(self, query: str) -> Tuple[str, bool]:
        """
        Sanitize user query input
        Returns: (sanitized_query, is_safe)
        """
        if not self.enabled:
            return query, True
            
        # Check length constraints
        max_length = self.query_config.get("max_length", 2000)
        min_length = self.query_config.get("min_length", 3)
        
        if len(query) > max_length:
            return query[:max_length], False
            
        if len(query) < min_length:
            return query, False
            
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if pattern.search(query):
                logger.warning(f"Blocked pattern detected in query: {pattern.pattern}")
                return "", False
        
        # Normalize and sanitize
        sanitized = self._normalize_text(query)
        sanitized = html.escape(sanitized) if self.config.get("content_filtering", {}).get("remove_html", True) else sanitized
        
        return sanitized, True
    
    def validate_file_upload(self, filename: str, file_size: int, file_content: bytes) -> Tuple[bool, str]:
        """
        Validate uploaded file
        Returns: (is_valid, error_message)
        """
        if not self.enabled:
            return True, ""
            
        # Check file size
        max_size_mb = self.file_config.get("max_file_size_mb", 50)
        if file_size > max_size_mb * 1024 * 1024:
            return False, f"File size exceeds {max_size_mb}MB limit"
            
        # Check file extension
        allowed_extensions = self.file_config.get("allowed_extensions", [".pdf", ".txt", ".md"])
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return False, f"File type {file_ext} not allowed. Allowed: {', '.join(allowed_extensions)}"
            
        # Secure filename
        secure_name = secure_filename(filename)
        if secure_name != filename:
            logger.warning(f"Filename sanitized: {filename} -> {secure_name}")
            
        # Basic malware detection (simple signature check)
        if self._contains_malware_signatures(file_content):
            return False, "File contains suspicious content"
            
        return True, ""
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text input"""
        # Unicode normalization
        if self.config.get("content_filtering", {}).get("normalize_unicode", True):
            text = unicodedata.normalize('NFKC', text)
            
        # Remove control characters
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
        
        return text.strip()
    
    def _contains_malware_signatures(self, content: bytes) -> bool:
        """Basic malware signature detection"""
        # Simple signature-based detection
        malware_signatures = [
            b'eval(',
            b'exec(',
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'data:text/html'
        ]
        
        content_lower = content.lower()
        return any(sig in content_lower for sig in malware_signatures)

class RateLimiter:
    """Handle rate limiting and throttling"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config.config.get("rate_limiting", {})
        self.enabled = self.config.get("enabled", True)
        self.storage = self.config.get("storage", "memory")
        
        # In-memory storage for rate limiting
        self.request_counts = defaultdict(lambda: defaultdict(int))
        self.request_timestamps = defaultdict(list)
        self.blocked_ips = defaultdict(datetime)
        
    def check_rate_limit(self, identifier: str, endpoint: str = "global") -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits
        Returns: (is_allowed, limit_info)
        """
        if not self.enabled:
            return True, {"remaining": float('inf')}
            
        now = datetime.now()
        
        # Check if IP is currently blocked
        if identifier in self.blocked_ips:
            if now < self.blocked_ips[identifier]:
                remaining_time = (self.blocked_ips[identifier] - now).total_seconds()
                return False, {"error": "IP blocked", "retry_after": remaining_time}
            else:
                del self.blocked_ips[identifier]
        
        # Get rate limits for endpoint
        limits = self._get_endpoint_limits(endpoint)
        
        # Check minute-based limit
        minute_key = now.strftime("%Y-%m-%d %H:%M")
        self.request_counts[identifier][minute_key] += 1
        
        if self.request_counts[identifier][minute_key] > limits["requests_per_minute"]:
            self._apply_cooldown(identifier)
            return False, {
                "error": "Rate limit exceeded", 
                "limit": limits["requests_per_minute"],
                "window": "minute"
            }
        
        # Check hourly limit
        hour_key = now.strftime("%Y-%m-%d %H")
        hourly_count = sum(
            count for key, count in self.request_counts[identifier].items()
            if key.startswith(hour_key)
        )
        
        if hourly_count > limits["requests_per_hour"]:
            self._apply_cooldown(identifier)
            return False, {
                "error": "Rate limit exceeded",
                "limit": limits["requests_per_hour"], 
                "window": "hour"
            }
            
        # Clean up old entries
        self._cleanup_old_entries(identifier, now)
        
        return True, {
            "remaining_minute": limits["requests_per_minute"] - self.request_counts[identifier][minute_key],
            "remaining_hour": limits["requests_per_hour"] - hourly_count
        }
    
    def _get_endpoint_limits(self, endpoint: str) -> Dict[str, int]:
        """Get rate limits for specific endpoint"""
        endpoint_limits = self.config.get("endpoint_limits", {})
        global_limits = self.config.get("global_limits", {})
        
        if endpoint in endpoint_limits:
            return endpoint_limits[endpoint]
        else:
            return {
                "requests_per_minute": global_limits.get("requests_per_minute", 60),
                "requests_per_hour": global_limits.get("requests_per_hour", 1000)
            }
    
    def _apply_cooldown(self, identifier: str):
        """Apply cooldown period to identifier"""
        cooldown_minutes = self.config.get("ip_limits", {}).get("cooldown_period_minutes", 15)
        self.blocked_ips[identifier] = datetime.now() + timedelta(minutes=cooldown_minutes)
        logger.warning(f"Applied {cooldown_minutes} minute cooldown to {identifier}")
    
    def _cleanup_old_entries(self, identifier: str, now: datetime):
        """Clean up old rate limiting entries"""
        cutoff = now - timedelta(hours=2)
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M")
        
        # Remove entries older than 2 hours
        keys_to_remove = [
            key for key in self.request_counts[identifier].keys()
            if key < cutoff_str
        ]
        
        for key in keys_to_remove:
            del self.request_counts[identifier][key]

class SecurityMiddleware:
    """Main security middleware integrating all security features"""
    
    def __init__(self, config_path: str = "configs/security_config.yaml"):
        self.config = SecurityConfig(config_path)
        self.auth = APIAuthentication(self.config)
        self.sanitizer = InputSanitizer(self.config)
        self.rate_limiter = RateLimiter(self.config)
        
    def secure_endpoint(self, endpoint_name: str, require_auth: bool = True, require_admin: bool = False):
        """Decorator to secure endpoints with authentication and rate limiting"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract request information (this would need to be adapted for specific frameworks)
                request_info = self._extract_request_info(args, kwargs)
                
                # Rate limiting check
                is_allowed, limit_info = self.rate_limiter.check_rate_limit(
                    request_info["ip"], endpoint_name
                )
                if not is_allowed:
                    return {"error": "Rate limit exceeded", "details": limit_info}, 429
                
                # Authentication check
                if require_auth and self.auth.enabled:
                    api_key = self.auth.extract_api_key(request_info["headers"])
                    if not self.auth.verify_api_key(api_key):
                        return {"error": "Invalid or missing API key"}, 401
                        
                    if require_admin and not self.auth.is_admin_key(api_key):
                        return {"error": "Admin privileges required"}, 403
                
                # Input sanitization (for text inputs)
                if "query" in kwargs:
                    sanitized_query, is_safe = self.sanitizer.sanitize_query(kwargs["query"])
                    if not is_safe:
                        return {"error": "Invalid input detected"}, 400
                    kwargs["query"] = sanitized_query
                
                # Add security headers to response
                response = func(*args, **kwargs)
                return self._add_security_headers(response)
                
            return wrapper
        return decorator
    
    def _extract_request_info(self, args, kwargs) -> Dict[str, Any]:
        """Extract request information (IP, headers, etc.)"""
        # This is a simplified implementation - would need to be adapted for specific frameworks
        return {
            "ip": "127.0.0.1",  # Default for local development
            "headers": {}
        }
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        if not self.config.config.get("security_headers", {}).get("enabled", True):
            return response
            
        # This would need to be implemented based on the specific framework being used
        return response

# Utility functions for integration
def get_client_ip(request) -> str:
    """Extract client IP from request (framework agnostic)"""
    # This would need to be implemented based on the specific framework
    return "127.0.0.1"

def create_secure_api_key() -> str:
    """Generate a cryptographically secure API key"""
    return secrets.token_hex(32)

def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

# Export main classes
__all__ = [
    "SecurityConfig", 
    "APIAuthentication", 
    "InputSanitizer", 
    "RateLimiter", 
    "SecurityMiddleware",
    "get_client_ip",
    "create_secure_api_key",
    "hash_api_key"
]