import logging
import re
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger import jsonlogger

# Context variable for request ID tracking across async calls
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# PII patterns for SOC 2 compliance - these will be redacted from logs
PII_PATTERNS = [
    # Email addresses
    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE),
    # SSN patterns (XXX-XX-XXXX, XXXXXXXXX)
    re.compile(r'\b(?:\d{3}-?\d{2}-?\d{4})\b'),
    # Phone numbers (various formats)
    re.compile(r'(?:\+?1[-.\s]?)?(?:\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})\b'),
    # Credit card numbers (basic pattern)
    re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    # API keys and tokens (alphanumeric strings 32+ chars)
    re.compile(r'\b[a-zA-Z0-9]{32,}\b'),
    # Common password fields
    re.compile(r'"password"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"token"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"secret"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"key"\s*:\s*"[^"]*"', re.IGNORECASE),
]


def sanitize_pii(text: str) -> str:
    """Remove PII from log messages for SOC 2 compliance."""
    if not isinstance(text, str):
        text = str(text)
    
    for pattern in PII_PATTERNS:
        text = pattern.sub('[REDACTED]', text)
    
    return text


class SOC2CompliantJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that includes request IDs and sanitizes PII for SOC 2 compliance."""
    
    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)
        log_record.setdefault("service", "ai-review")
        
        # Add request ID from context if available
        request_id = request_id_var.get()
        if request_id:
            log_record["request_id"] = request_id
        
        # Ensure message exists
        if not log_record.get("message"):
            log_record["message"] = record.getMessage()
        
        # Sanitize all string values for PII
        for key, value in log_record.items():
            if isinstance(value, str):
                log_record[key] = sanitize_pii(value)
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                log_record[key] = _sanitize_dict(value)


def _sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize dictionary values for PII."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_pii(value)
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_pii(str(item)) if isinstance(item, str) else item for item in value]
        else:
            sanitized[key] = value
    return sanitized


def configure_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging with SOC 2 compliance features."""
    handler = logging.StreamHandler()
    formatter = SOC2CompliantJsonFormatter(
        "%(asctime)s %(level)s %(name)s %(message)s %(request_id)s %(service)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    root_logger.handlers = [handler]


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current async context."""
    request_id_var.set(request_id)


def get_request_id() -> str | None:
    """Get the current request ID from async context."""
    return request_id_var.get()
