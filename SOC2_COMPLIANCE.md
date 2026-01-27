# SOC 2 Compliance Implementation

This document outlines the SOC 2 compliance features implemented in the AI Review microservice.

## 🔒 Security Controls

### PII Data Protection
- **Automatic PII Sanitization**: All log entries are automatically scanned and PII is redacted with `[REDACTED]`
- **Supported PII Types**:
  - Email addresses
  - Social Security Numbers (XXX-XX-XXXX format)
  - Phone numbers (various US formats)
  - Credit card numbers
  - API keys and tokens (32+ character alphanumeric strings)
  - Password, token, secret, and key fields in JSON

### Request Correlation
- **Unique Request IDs**: Every API request gets a UUID for end-to-end traceability
- **Context Propagation**: Request IDs are maintained across async operations
- **Response Headers**: Request IDs are returned in `X-Request-ID` header for client correlation

### Audit Trail
- **Structured JSON Logging**: All logs use JSON format for machine parsing
- **Required Fields**: Every log entry includes:
  - `timestamp`: ISO 8601 timestamp
  - `level`: Log level (INFO, WARNING, ERROR)
  - `service`: Service identifier ("ai-review")
  - `request_id`: Unique request identifier
  - `logger`: Source logger name
  - `message`: Sanitized log message

## 🔍 Request/Response Logging

### API Request Logging
All API requests are logged with:
- HTTP method and path
- Query parameters
- Client IP address (considering proxy headers)
- User agent
- Content type and length
- Request duration in milliseconds

### Security Event Logging
Automatic logging of security-relevant events:
- Authentication failures (401 responses)
- Authorization failures (403 responses)
- Rate limit violations (429 responses)
- Request processing errors (500+ responses)

### Performance Monitoring
- Request duration tracking
- Response size monitoring
- Error rate calculation
- Service availability metrics

## ⚙️ Configuration

### Health Check Optimization
- **Configurable Timeout**: `HEALTH_CHECK_TIMEOUT_SECONDS` (default: 300s/5 minutes)
- **Resource Optimization**: Extended timeout reduces unnecessary health check failures
- **Detailed Status**: Health endpoints return timing information and configuration details

### Environment Variables
```bash
# Logging Configuration
LOG_LEVEL=info                           # Log level (debug, info, warning, error)
HEALTH_CHECK_TIMEOUT_SECONDS=300         # Health check timeout (5 minutes)

# Request/Response Logging
# (No additional configuration needed - automatically enabled)
```

## 📋 SOC 2 Trust Services Criteria Mapping

| Trust Service | Implementation |
|---------------|---------------|
| **Security** | PII sanitization, request correlation, security event logging |
| **Availability** | Health check monitoring, error tracking, performance metrics |
| **Processing Integrity** | Request validation, error handling, audit trails |
| **Confidentiality** | PII redaction, secure logging practices |
| **Privacy** | Data minimization in logs, PII protection |

## 🧪 Testing & Validation

### Test Coverage
- **PII Sanitization**: 8 test cases covering all PII pattern types
- **Request ID Tracking**: Context variable functionality
- **JSON Formatter**: SOC 2 compliant log structure
- **Middleware Integration**: Request/response logging and security events
- **Error Handling**: Exception capture and logging

### Running Tests
```bash
# Run all SOC 2 compliance tests
python -m pytest app/tests/test_logging.py app/tests/test_middleware.py -v

# Run specific test categories
python -m pytest app/tests/test_logging.py::TestPIISanitization -v
python -m pytest app/tests/test_middleware.py::TestSecurityAuditMiddleware -v
```

## 🚀 Implementation Details

### Files Modified/Created
- `app/core/logging.py` - Enhanced with PII sanitization and request ID tracking
- `app/middleware/logging_middleware.py` - New request/response logging middleware
- `app/middleware/security_middleware.py` - New security audit middleware  
- `app/api/routers/health.py` - Enhanced with configurable timeouts
- `app/core/config.py` - Added health check timeout configuration
- `app/main.py` - Integrated logging and security middleware

### Middleware Order
1. `SecurityAuditMiddleware` - Captures security events
2. `RequestLoggingMiddleware` - Logs requests/responses with PII protection
3. `CORSMiddleware` - Handles CORS (existing)

## 📊 Log Examples

### Successful Request
```json
{
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "level": "INFO", 
  "service": "ai-review",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "logger": "app.middleware.logging_middleware",
  "message": "api.request.complete",
  "method": "POST",
  "path": "/v1/chat",
  "status_code": 200,
  "duration_ms": 1250.5,
  "client_ip": "192.168.1.100"
}
```

### Security Event
```json
{
  "timestamp": "2024-01-15T10:31:00.789012Z",
  "level": "WARNING",
  "service": "ai-review", 
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "logger": "security_audit",
  "message": "security_event.authentication_failure",
  "event_type": "authentication_failure",
  "status_code": 401,
  "client_ip": "203.0.113.1",
  "method": "POST",
  "path": "/v1/chat"
}
```

### PII Sanitization Example
```json
{
  "timestamp": "2024-01-15T10:32:00.345678Z",
  "level": "INFO",
  "service": "ai-review",
  "request_id": "550e8400-e29b-41d4-a716-446655440002", 
  "logger": "app.api.routers.chat",
  "message": "User data: email [REDACTED], phone [REDACTED], safe data preserved"
}
```

## ✅ Compliance Checklist

- [x] PII automatically sanitized from all log entries
- [x] Request IDs generated and tracked across operations
- [x] Structured JSON logging implemented
- [x] Security events logged with proper context
- [x] Request/response logging with duration tracking
- [x] Health check timeouts configurable (5 minutes default)
- [x] Client IP extraction considering proxy headers
- [x] Comprehensive test coverage (29 tests passing)
- [x] Error handling and exception logging
- [x] SOC 2 Trust Services Criteria mapped and implemented

## 🔄 Maintenance

### Regular Tasks
- Monitor log storage and rotation policies
- Review PII patterns for new data types
- Validate request ID uniqueness and distribution
- Test health check timeout effectiveness
- Update security event detection rules

### Monitoring Alerts
- High error rate (>5% of requests failing)
- Health check timeouts exceeding threshold
- Security events (authentication/authorization failures)
- PII detected in logs (should not occur with sanitization)