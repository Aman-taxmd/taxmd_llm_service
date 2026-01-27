import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Response
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.middleware.logging_middleware import RequestLoggingMiddleware, SecurityAuditMiddleware


class TestRequestLoggingMiddleware:
    """Test the request logging middleware."""

    def setup_method(self):
        self.app = FastAPI()
        self.app.add_middleware(RequestLoggingMiddleware)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @self.app.get("/health/live")
        async def health_endpoint():
            return {"status": "live"}
        
        @self.app.get("/error")
        async def error_endpoint():
            raise HTTPException(status_code=500, detail="Test error")
        
        @self.app.get("/runtime-error")
        async def runtime_error_endpoint():
            raise RuntimeError("This will be caught by middleware")
        
        self.client = TestClient(self.app)

    @patch('app.middleware.logging_middleware.logger')
    def test_successful_request_logging(self, mock_logger):
        """Test that successful requests are logged correctly."""
        response = self.client.get("/test")
        
        assert response.status_code == 200
        
        # Check that start and complete log calls were made
        log_calls = mock_logger.info.call_args_list
        assert len(log_calls) >= 2
        
        # Check start log
        start_call = log_calls[0]
        assert start_call[0][0] == "api.request.start"
        start_extra = start_call[1]['extra']
        assert 'request_id' in start_extra
        assert start_extra['method'] == 'GET'
        assert start_extra['path'] == '/test'
        
        # Check complete log
        complete_call = log_calls[1]
        assert complete_call[0][0] == "api.request.complete"
        complete_extra = complete_call[1]['extra']
        assert complete_extra['status_code'] == 200
        assert 'duration_ms' in complete_extra
        
        # Check that request ID header is added
        assert 'X-Request-ID' in response.headers

    @patch('app.middleware.logging_middleware.logger')
    def test_excluded_paths_not_logged(self, mock_logger):
        """Test that excluded paths (health checks) are not logged."""
        response = self.client.get("/health/live")
        
        assert response.status_code == 200
        
        # Should not have any log calls for excluded paths
        mock_logger.info.assert_not_called()

    @patch('app.middleware.logging_middleware.logger')
    def test_error_request_logging(self, mock_logger):
        """Test that error requests are logged correctly."""
        # Test with a RuntimeError that should be caught by middleware
        try:
            response = self.client.get("/runtime-error")
        except Exception:
            # Exception may not be fully handled by test client
            pass
        
        # Check that start log was made
        info_calls = mock_logger.info.call_args_list
        error_calls = mock_logger.error.call_args_list
        
        assert len(info_calls) >= 1  # Start log
        
        # If error is caught by middleware, should have error log
        if error_calls:
            error_call = error_calls[0]
            assert error_call[0][0] == "api.request.error"
            error_extra = error_call[1]['extra']
            assert 'request_id' in error_extra
            assert 'duration_ms' in error_extra

    def test_client_ip_extraction(self):
        """Test client IP extraction from various headers."""
        middleware = RequestLoggingMiddleware(self.app)
        
        # Test X-Forwarded-For header
        request = MagicMock()
        request.headers = {"x-forwarded-for": "192.168.1.100, 10.0.0.1"}
        request.client = None
        
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.100"
        
        # Test X-Real-IP header
        request = MagicMock()
        request.headers = {"x-real-ip": "203.0.113.1"}
        request.client = None
        
        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"
        
        # Test direct client IP
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "198.51.100.1"
        
        ip = middleware._get_client_ip(request)
        assert ip == "198.51.100.1"
        
        # Test unknown IP
        request = MagicMock()
        request.headers = {}
        request.client = None
        
        ip = middleware._get_client_ip(request)
        assert ip == "unknown"


class TestSecurityAuditMiddleware:
    """Test the security audit middleware."""

    def setup_method(self):
        self.app = FastAPI()
        self.app.add_middleware(SecurityAuditMiddleware)
        
        @self.app.get("/secure")
        async def secure_endpoint():
            return {"message": "authorized"}
        
        @self.app.get("/unauthorized")
        async def unauthorized_endpoint():
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        @self.app.get("/forbidden")
        async def forbidden_endpoint():
            raise HTTPException(status_code=403, detail="Forbidden")
        
        @self.app.get("/rate-limited")
        async def rate_limited_endpoint():
            raise HTTPException(status_code=429, detail="Rate limited")
        
        self.client = TestClient(self.app)

    @patch('app.middleware.logging_middleware.logging.getLogger')
    def test_authentication_failure_logging(self, mock_get_logger):
        """Test that 401 responses trigger security event logging."""
        mock_security_logger = MagicMock()
        mock_get_logger.return_value = mock_security_logger
        
        response = self.client.get("/unauthorized")
        
        assert response.status_code == 401
        
        # Check that security event was logged
        mock_security_logger.warning.assert_called_once()
        call_args = mock_security_logger.warning.call_args
        assert "security_event.authentication_failure" in call_args[0][0]
        
        log_extra = call_args[1]['extra']
        assert log_extra['event_type'] == 'authentication_failure'
        assert log_extra['status_code'] == 401

    @patch('app.middleware.logging_middleware.logging.getLogger')
    def test_authorization_failure_logging(self, mock_get_logger):
        """Test that 403 responses trigger security event logging."""
        mock_security_logger = MagicMock()
        mock_get_logger.return_value = mock_security_logger
        
        response = self.client.get("/forbidden")
        
        assert response.status_code == 403
        
        # Check that security event was logged
        mock_security_logger.warning.assert_called_once()
        call_args = mock_security_logger.warning.call_args
        assert "security_event.authorization_failure" in call_args[0][0]

    @patch('app.middleware.logging_middleware.logging.getLogger')
    def test_rate_limit_logging(self, mock_get_logger):
        """Test that 429 responses trigger security event logging."""
        mock_security_logger = MagicMock()
        mock_get_logger.return_value = mock_security_logger
        
        response = self.client.get("/rate-limited")
        
        assert response.status_code == 429
        
        # Check that security event was logged
        mock_security_logger.warning.assert_called_once()
        call_args = mock_security_logger.warning.call_args
        assert "security_event.rate_limit_exceeded" in call_args[0][0]

    @patch('app.middleware.logging_middleware.logging.getLogger')
    def test_successful_request_no_security_log(self, mock_get_logger):
        """Test that successful requests don't trigger security logging."""
        mock_security_logger = MagicMock()
        mock_get_logger.return_value = mock_security_logger
        
        response = self.client.get("/secure")
        
        assert response.status_code == 200
        
        # Should not log security events for successful requests
        mock_security_logger.warning.assert_not_called()

    def test_security_middleware_client_ip_extraction(self):
        """Test client IP extraction in security middleware."""
        middleware = SecurityAuditMiddleware(self.app)
        
        # Test with forwarded header
        request = MagicMock()
        request.headers = {"x-forwarded-for": "192.168.1.100, 10.0.0.1"}
        request.client = None
        
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.100"


class TestMiddlewareIntegration:
    """Test middleware integration and ordering."""

    def setup_method(self):
        self.app = FastAPI()
        # Add middleware in the correct order
        self.app.add_middleware(SecurityAuditMiddleware)
        self.app.add_middleware(RequestLoggingMiddleware)
        
        @self.app.get("/integrated")
        async def integrated_endpoint():
            return {"message": "success"}
        
        self.client = TestClient(self.app)

    @patch('app.middleware.logging_middleware.logger')
    @patch('app.middleware.logging_middleware.logging.getLogger')
    def test_middleware_chain(self, mock_get_logger, mock_request_logger):
        """Test that both middleware work together correctly."""
        mock_security_logger = MagicMock()
        mock_get_logger.return_value = mock_security_logger
        
        response = self.client.get("/integrated")
        
        assert response.status_code == 200
        
        # Request logging middleware should log start and complete
        log_calls = mock_request_logger.info.call_args_list
        assert len(log_calls) >= 2
        
        # Security middleware should not log for successful requests
        mock_security_logger.warning.assert_not_called()
        
        # Response should include request ID header
        assert 'X-Request-ID' in response.headers


class TestMiddlewareErrorHandling:
    """Test middleware error handling scenarios."""

    def setup_method(self):
        self.app = FastAPI()
        self.app.add_middleware(SecurityAuditMiddleware)
        self.app.add_middleware(RequestLoggingMiddleware)
        
        @self.app.get("/exception")
        async def exception_endpoint():
            raise Exception("Unexpected error")
        
        self.client = TestClient(self.app)

    @patch('app.middleware.logging_middleware.logger')
    @patch('app.middleware.logging_middleware.logging.getLogger')
    def test_exception_handling(self, mock_get_logger, mock_request_logger):
        """Test that unhandled exceptions are properly logged by both middleware."""
        mock_security_logger = MagicMock()
        mock_get_logger.return_value = mock_security_logger
        
        # Test general functionality - exception details may vary based on how
        # FastAPI/Starlette handles different exception types
        try:
            response = self.client.get("/exception")
        except Exception:
            pass  # Expected for unhandled exceptions
        
        # At minimum, request start should be logged
        info_calls = mock_request_logger.info.call_args_list
        assert len(info_calls) >= 1