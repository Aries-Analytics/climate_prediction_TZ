"""
Security middleware for rate limiting and input validation.
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import re


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse and brute force attacks.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old requests
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=1)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )
        
        # Add current request
        self.requests[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Input sanitization middleware to prevent injection attacks.
    """
    
    # Patterns to detect potential injection attacks
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(--|\#|\/\*|\*\/)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Only check for POST, PUT, PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Get request body
                body = await request.body()
                body_str = body.decode('utf-8')
                
                # Check for SQL injection patterns
                for pattern in self.SQL_INJECTION_PATTERNS:
                    if re.search(pattern, body_str, re.IGNORECASE):
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid input detected"
                        )
                
                # Check for XSS patterns
                for pattern in self.XSS_PATTERNS:
                    if re.search(pattern, body_str, re.IGNORECASE):
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid input detected"
                        )
                
                # Reconstruct request with validated body
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
                
            except UnicodeDecodeError:
                # If body can't be decoded, let it pass (might be binary data)
                pass
        
        # Process request
        response = await call_next(request)
        return response


def add_security_headers(response):
    """Add security headers to response"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response = add_security_headers(response)
        return response
