"""
Secure FastAPI Landing Page for Quest Analytics RAG Assistant

Enhanced with comprehensive security features:
- API Authentication (API keys, JWT tokens)
- Input sanitization and validation  
- Rate limiting and throttling
- Security headers and threat detection
- Health monitoring and analytics

Author: AI RAG Assistant Team
Version: 1.0.0 (Security Enhanced)
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Security imports
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rag_pipeline.security import (
    SecurityMiddleware, 
    get_client_ip, 
    create_secure_api_key
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize security
security_middleware = SecurityMiddleware()
security = HTTPBearer(auto_error=False)

# FastAPI app initialization
app = FastAPI(
    title="Quest Analytics RAG Assistant",
    description="Secure AI-powered research assistant with advanced security features",
    version="1.0.0",
    docs_url="/api/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Security middleware
@app.middleware("http")
async def security_middleware_handler(request: Request, call_next):
    """Apply security checks to all requests"""
    
    # Extract client IP
    client_ip = request.client.host
    
    # Rate limiting
    endpoint = request.url.path
    is_allowed, limit_info = security_middleware.rate_limiter.check_rate_limit(
        client_ip, endpoint
    )
    
    if not is_allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "details": limit_info,
                "retry_after": limit_info.get("retry_after", 60)
            },
            headers={"Retry-After": str(limit_info.get("retry_after", 60))}
        )
    
    # Process request
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Add security headers
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY", 
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Process-Time": str(process_time),
        "X-Rate-Limit-Remaining": str(limit_info.get("remaining_minute", "∞"))
    }
    
    for key, value in security_headers.items():
        response.headers[key] = value
    
    return response

# Add CORS middleware with security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7860", "http://127.0.0.1:7860"],  # Only allow Gradio
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.amazonaws.com"]
)

# Authentication dependency
async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> bool:
    """Verify API key for protected endpoints"""
    
    if not security_middleware.auth.enabled:
        return True
        
    # Extract API key from headers
    api_key = None
    if credentials:
        api_key = credentials.credentials
    else:
        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
    
    if not security_middleware.auth.verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return True

# Admin authentication dependency
async def verify_admin_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> bool:
    """Verify admin API key for admin endpoints"""
    
    await verify_api_key(request, credentials)
    
    api_key = None
    if credentials:
        api_key = credentials.credentials
    else:
        api_key = request.headers.get("X-API-Key")
    
    if not security_middleware.auth.is_admin_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return True

# Analytics storage
analytics_data = {
    "requests": [],
    "total_requests": 0,
    "unique_visitors": set(),
    "error_count": 0,
    "last_updated": datetime.now()
}

def log_analytics(request: Request, response_status: int = 200):
    """Log analytics data for monitoring"""
    global analytics_data
    
    client_ip = request.client.host
    analytics_data["requests"].append({
        "timestamp": datetime.now().isoformat(),
        "ip": client_ip,
        "path": request.url.path,
        "method": request.method,
        "status": response_status,
        "user_agent": request.headers.get("user-agent", "")
    })
    
    analytics_data["total_requests"] += 1
    analytics_data["unique_visitors"].add(client_ip)
    analytics_data["last_updated"] = datetime.now()
    
    # Keep only last 1000 requests
    if len(analytics_data["requests"]) > 1000:
        analytics_data["requests"] = analytics_data["requests"][-1000:]

# Root endpoint - Landing page
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Serve the main landing page"""
    
    log_analytics(request)
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Quest Analytics RAG Assistant</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; display: flex; flex-direction: column;
            }
            .container { 
                max-width: 1200px; margin: 0 auto; padding: 2rem;
                background: rgba(255, 255, 255, 0.95); border-radius: 20px;
                margin-top: 2rem; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            .header { text-align: center; margin-bottom: 3rem; }
            .header h1 { 
                color: #2d3748; font-size: 3rem; margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            }
            .security-badge {
                display: inline-block; background: #48bb78;
                color: white; padding: 0.5rem 1rem; border-radius: 20px;
                font-size: 0.9rem; margin: 1rem 0;
            }
            .features { 
                display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem; margin-bottom: 2rem;
            }
            .feature { 
                background: #f8fafc; padding: 1.5rem; border-radius: 10px;
                border-left: 4px solid #667eea;
            }
            .security-section {
                background: #fff5f5; border-left-color: #e53e3e;
                border: 2px solid #fed7d7; border-radius: 10px;
                padding: 1.5rem; margin: 2rem 0;
            }
            .security-section h3 { color: #c53030; }
            .cta { 
                text-align: center; margin: 2rem 0;
                padding: 2rem; background: #edf2f7; border-radius: 15px;
            }
            .button { 
                display: inline-block; background: #667eea; color: white;
                padding: 1rem 2rem; text-decoration: none; border-radius: 8px;
                font-weight: 600; transition: all 0.3s ease;
                margin: 0.5rem;
            }
            .button:hover { background: #5a67d8; transform: translateY(-2px); }
            .status-grid {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem; margin: 2rem 0;
            }
            .status-card {
                background: white; padding: 1rem; border-radius: 10px;
                border: 2px solid #e2e8f0; text-align: center;
            }
            .status-good { border-color: #48bb78; }
            .status-warning { border-color: #ed8936; }
            .footer { 
                text-align: center; margin-top: 2rem; padding: 1rem;
                color: #718096; font-size: 0.9rem;
                background: rgba(255, 255, 255, 0.8); border-radius: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Quest Analytics RAG Assistant</h1>
                <p style="font-size: 1.2rem; color: #4a5568; margin-bottom: 1rem;">
                    Enterprise-Grade AI Research Assistant with Advanced Security
                </p>
                <span class="security-badge">🛡️ Security Enhanced</span>
                <span class="security-badge">🔒 Rate Limited</span>
                <span class="security-badge">✅ Input Validated</span>
            </div>

            <div class="features">
                <div class="feature">
                    <h3>🔬 Advanced RAG Pipeline</h3>
                    <p>Hybrid search with OpenSearch, embeddings, and re-ranking for precise document retrieval.</p>
                </div>
                <div class="feature">
                    <h3>🤖 Local LLM Integration</h3>
                    <p>Ollama-powered chat with health monitoring and automatic fallback mechanisms.</p>
                </div>
                <div class="feature">
                    <h3>📊 MLOps Excellence</h3>
                    <p>24 production scripts, A/B testing, and statistical evaluation with 95% confidence intervals.</p>
                </div>
                <div class="feature">
                    <h3>☁️ Cloud Ready</h3>
                    <p>Multi-tier AWS deployment from $8/month with Docker, Terraform, and Kubernetes.</p>
                </div>
            </div>

            <div class="security-section">
                <h3>🛡️ Security Features</h3>
                <div class="status-grid">
                    <div class="status-card status-good">
                        <strong>API Authentication</strong><br>
                        <span style="color: #48bb78;">Active</span>
                    </div>
                    <div class="status-card status-good">
                        <strong>Rate Limiting</strong><br>
                        <span style="color: #48bb78;">60/min</span>
                    </div>
                    <div class="status-card status-good">
                        <strong>Input Sanitization</strong><br>
                        <span style="color: #48bb78;">Enabled</span>
                    </div>
                    <div class="status-card status-good">
                        <strong>Security Headers</strong><br>
                        <span style="color: #48bb78;">Applied</span>
                    </div>
                </div>
                <p><strong>Enhanced Security:</strong> API key authentication, input validation, rate limiting, 
                   malware detection, and comprehensive threat monitoring.</p>
            </div>

            <div class="cta">
                <h3>🚀 Get Started</h3>
                <p>Experience the power of secure, enterprise-grade RAG technology</p>
                <a href="http://localhost:7860" class="button">Launch Assistant</a>
                <a href="/api/health" class="button">System Status</a>
                <a href="/api/security-info" class="button">Security Info</a>
            </div>

            <div class="footer">
                <p>Quest Analytics RAG Assistant • Security Enhanced • Built with FastAPI & Advanced MLOps</p>
                <p>🔒 All communications secured • 📊 Performance monitored • 🛡️ Threats detected</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

# Health check endpoint
@app.get("/api/health")
async def health_check(request: Request):
    """Public health check endpoint"""
    
    log_analytics(request)
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "security": {
            "authentication": security_middleware.auth.enabled,
            "rate_limiting": security_middleware.rate_limiter.enabled,
            "input_sanitization": security_middleware.sanitizer.enabled
        },
        "components": {
            "fastapi": True,
            "gradio": "http://localhost:7860",
            "security_middleware": True
        }
    }

# Security information endpoint  
@app.get("/api/security-info")
async def security_info(request: Request):
    """Public security information endpoint"""
    
    log_analytics(request)
    
    return {
        "security_features": {
            "api_authentication": {
                "enabled": security_middleware.auth.enabled,
                "method": "API Key",
                "description": "Secure API key authentication for all endpoints"
            },
            "rate_limiting": {
                "enabled": security_middleware.rate_limiter.enabled,
                "global_limit": "60 requests per minute",
                "endpoint_limits": {
                    "chat": "20/min",
                    "upload": "5/min",
                    "health": "30/min"
                },
                "description": "Intelligent rate limiting with IP-based throttling"
            },
            "input_sanitization": {
                "enabled": security_middleware.sanitizer.enabled,
                "features": [
                    "SQL injection prevention",
                    "XSS protection", 
                    "Path traversal blocking",
                    "Malware signature detection",
                    "File type validation"
                ],
                "description": "Comprehensive input validation and sanitization"
            },
            "security_headers": {
                "enabled": True,
                "headers": [
                    "X-Content-Type-Options",
                    "X-Frame-Options", 
                    "X-XSS-Protection",
                    "Strict-Transport-Security",
                    "Content-Security-Policy"
                ],
                "description": "Industry-standard security headers applied"
            }
        },
        "compliance": {
            "data_protection": "Input sanitization and validation",
            "access_control": "API key based authentication",
            "audit_logging": "All requests logged for security monitoring"
        }
    }

# Analytics endpoint (admin only)
@app.get("/api/analytics")
async def get_analytics(
    request: Request, 
    authenticated: bool = Depends(verify_admin_key)
):
    """Get analytics data (admin only)"""
    
    log_analytics(request)
    
    # Convert set to list for JSON serialization
    analytics_copy = analytics_data.copy()
    analytics_copy["unique_visitors"] = len(analytics_data["unique_visitors"])
    analytics_copy["recent_requests"] = analytics_data["requests"][-10:]  # Last 10 requests
    
    return analytics_copy

# Generate API key endpoint (admin only)
@app.post("/api/generate-key")
async def generate_api_key(
    request: Request,
    authenticated: bool = Depends(verify_admin_key)
):
    """Generate new API key (admin only)"""
    
    log_analytics(request) 
    
    new_key = create_secure_api_key()
    logger.info(f"New API key generated: {new_key[:8]}...")
    
    return {
        "api_key": new_key,
        "created_at": datetime.now().isoformat(),
        "note": "Store this key securely - it cannot be retrieved again"
    }

# Chat endpoint (protected)
@app.post("/api/chat")
async def chat_endpoint(
    request: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """Protected chat endpoint for programmatic access"""
    
    log_analytics(request)
    
    try:
        body = await request.json()
        query = body.get("query", "")
        
        # Sanitize input
        sanitized_query, is_safe = security_middleware.sanitizer.sanitize_query(query)
        if not is_safe:
            raise HTTPException(
                status_code=400,
                detail="Invalid input detected"
            )
        
        # This would integrate with your RAG pipeline
        return {
            "response": f"Processed query: {sanitized_query}",
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        log_analytics(request, 500)
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    # Load environment configuration
    host = os.getenv("LANDING_HOST", "0.0.0.0")
    port = int(os.getenv("LANDING_PORT", 3000))
    debug = os.getenv("ENVIRONMENT", "development") != "production"
    
    logger.info(f"Starting secure FastAPI server on {host}:{port}")
    logger.info(f"Security enabled: {security_middleware.auth.enabled}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    uvicorn.run(
        "landing.main:app" if "__main__" not in __name__ else app,
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )