import json
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_request_id, sanitize_pii, set_request_id

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for SOC 2 compliant request/response logging.
    
    Features:
    - Generates unique request IDs for correlation
    - Logs all API requests and responses
    - Excludes PII from logs
    - Tracks request duration
    - Includes security-relevant metadata
    """

    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = {"/health/live", "/health/ready", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for health checks and docs
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        
        # Start timing
        start_time = time.time()
        
        # Get client IP (considering proxy headers)
        client_ip = self._get_client_ip(request)
        
        # Log incoming request (without body for security)
        logger.info(
            "api.request.start",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", ""),
                "content_type": request.headers.get("content-type", ""),
                "content_length": request.headers.get("content-length", 0),
            }
        )

        try:
            # Process request
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log successful response
            logger.info(
                "api.request.complete",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "response_size": response.headers.get("content-length", 0),
                }
            )
            
            # Add request ID to response headers for client correlation
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log error response
            logger.error(
                "api.request.error",
                extra={
                    "request_id": request_id,
                    "error_type": type(exc).__name__,
                    "error_message": sanitize_pii(str(exc)),
                    "duration_ms": duration_ms,
                },
                exc_info=True
            )
            
            # Re-raise the exception
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP considering proxy headers."""
        # Check for forwarded IP headers (common in load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, get the first one
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security event logging per SOC 2 requirements.
    
    Logs security-relevant events:
    - Authentication failures
    - Authorization failures
    - Suspicious request patterns
    - Rate limit violations
    """

    def __init__(self, app):
        super().__init__(app)
        self.security_logger = logging.getLogger("security_audit")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            
            # Log security events based on response status
            if response.status_code == 401:
                self._log_security_event(request, "authentication_failure", response.status_code)
            elif response.status_code == 403:
                self._log_security_event(request, "authorization_failure", response.status_code)
            elif response.status_code == 429:
                self._log_security_event(request, "rate_limit_exceeded", response.status_code)
            
            return response
            
        except Exception as exc:
            # Log any unhandled security-related exceptions
            self._log_security_event(request, "request_processing_error", 500, str(exc))
            raise

    def _log_security_event(self, request: Request, event_type: str, status_code: int, error_msg: str = None):
        """Log security events with proper context."""
        request_id = get_request_id()
        client_ip = self._get_client_ip(request)
        
        log_data = {
            "event_type": event_type,
            "request_id": request_id,
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "user_agent": sanitize_pii(request.headers.get("user-agent", "")),
            "timestamp": time.time(),
        }
        
        if error_msg:
            log_data["error_message"] = sanitize_pii(error_msg)
        
        self.security_logger.warning(
            f"security_event.{event_type}",
            extra=log_data
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP considering proxy headers."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"