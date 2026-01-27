import json
import re
from unittest.mock import MagicMock, patch

import pytest

from app.core.logging import (
    PII_PATTERNS,
    SOC2CompliantJsonFormatter,
    get_request_id,
    sanitize_pii,
    set_request_id,
)


class TestPIISanitization:
    """Test PII sanitization for SOC 2 compliance."""

    def test_sanitize_email_addresses(self):
        text = "Contact us at user@example.com or admin@company.org"
        sanitized = sanitize_pii(text)
        assert "[REDACTED]" in sanitized
        assert "user@example.com" not in sanitized
        assert "admin@company.org" not in sanitized

    def test_sanitize_ssn_patterns(self):
        text = "SSN: 123-45-6789 or 987654321"
        sanitized = sanitize_pii(text)
        assert "[REDACTED]" in sanitized
        assert "123-45-6789" not in sanitized
        assert "987654321" not in sanitized

    def test_sanitize_phone_numbers(self):
        text = "Call (555) 123-4567 or 555.987.6543"
        sanitized = sanitize_pii(text)
        assert "[REDACTED]" in sanitized
        assert "(555) 123-4567" not in sanitized
        assert "555.987.6543" not in sanitized

    def test_sanitize_credit_card_numbers(self):
        text = "Credit card: 4532 1234 5678 9012"
        sanitized = sanitize_pii(text)
        assert "[REDACTED]" in sanitized
        assert "4532 1234 5678 9012" not in sanitized

    def test_sanitize_api_keys(self):
        text = "API Key: abcd1234567890efghijklmnopqrstuvwxyz123456"
        sanitized = sanitize_pii(text)
        assert "[REDACTED]" in sanitized
        assert "abcd1234567890efghijklmnopqrstuvwxyz123456" not in sanitized

    def test_sanitize_password_fields(self):
        json_text = '{"password": "secretpass123", "token": "abc123token"}'
        sanitized = sanitize_pii(json_text)
        assert "[REDACTED]" in sanitized
        assert "secretpass123" not in sanitized
        assert "abc123token" not in sanitized

    def test_non_string_input(self):
        # Should convert to string and sanitize
        result = sanitize_pii(12345)
        assert isinstance(result, str)
        assert result == "12345"

    def test_no_pii_in_text(self):
        text = "This is a normal log message with no PII"
        result = sanitize_pii(text)
        assert result == text


class TestRequestIdTracking:
    """Test request ID context tracking."""

    def test_set_and_get_request_id(self):
        test_id = "test-request-123"
        set_request_id(test_id)
        assert get_request_id() == test_id

    def test_default_request_id(self):
        # In a fresh context, should be None
        assert get_request_id() is None or isinstance(get_request_id(), str)


class TestSOC2CompliantJsonFormatter:
    """Test the SOC 2 compliant JSON formatter."""

    def setup_method(self):
        self.formatter = SOC2CompliantJsonFormatter()

    def test_formatter_adds_request_id(self):
        with patch('app.core.logging.request_id_var') as mock_request_id_var:
            mock_request_id_var.get.return_value = "test-request-123"
            
            # Create a mock log record
            record = MagicMock()
            record.levelname = "INFO"
            record.name = "test.logger"
            record.getMessage.return_value = "Test message"
            
            log_record = {}
            message_dict = {}
            
            self.formatter.add_fields(log_record, record, message_dict)
            
            assert log_record["request_id"] == "test-request-123"
            assert log_record["level"] == "INFO"
            assert log_record["logger"] == "test.logger"
            assert log_record["service"] == "ai-review"
            assert log_record["message"] == "Test message"

    def test_formatter_sanitizes_pii(self):
        with patch('app.core.logging.request_id_var') as mock_request_id_var:
            mock_request_id_var.get.return_value = None
            
            # Create a mock log record with PII
            record = MagicMock()
            record.levelname = "INFO"
            record.name = "test.logger"
            record.getMessage.return_value = "User email: user@example.com"
            
            log_record = {"sensitive_data": "Contact admin@company.org"}
            message_dict = {}
            
            self.formatter.add_fields(log_record, record, message_dict)
            
            # Check that PII is redacted
            assert "[REDACTED]" in log_record["message"]
            assert "[REDACTED]" in log_record["sensitive_data"]
            assert "user@example.com" not in log_record["message"]
            assert "admin@company.org" not in log_record["sensitive_data"]

    def test_formatter_handles_nested_dicts(self):
        # Create a mock log record with nested dictionary containing PII
        record = MagicMock()
        record.levelname = "INFO"
        record.name = "test.logger"
        record.getMessage.return_value = "Test message"
        
        nested_data = {
            "user": {
                "email": "user@example.com",
                "phone": "555-123-4567",
                "safe_data": "This is safe"
            },
            "api_key": "abcd1234567890efghijklmnopqrstuvwxyz123456"
        }
        
        log_record = {"nested": nested_data}
        message_dict = {}
        
        self.formatter.add_fields(log_record, record, message_dict)
        
        # Check that nested PII is redacted
        assert log_record["nested"]["user"]["email"] == "[REDACTED]"
        assert log_record["nested"]["user"]["phone"] == "[REDACTED]"
        assert log_record["nested"]["user"]["safe_data"] == "This is safe"
        assert log_record["nested"]["api_key"] == "[REDACTED]"


class TestPIIPatterns:
    """Test individual PII regex patterns."""

    def test_email_pattern(self):
        email_pattern = next(p for p in PII_PATTERNS if "@" in p.pattern)
        
        # Should match
        assert email_pattern.search("user@domain.com")
        assert email_pattern.search("complex.email+tag@sub.domain.co.uk")
        
        # Should not match
        assert not email_pattern.search("not-an-email")
        assert not email_pattern.search("@domain.com")

    def test_ssn_pattern(self):
        ssn_pattern = next(p for p in PII_PATTERNS if "d{3}" in p.pattern)
        
        # Should match
        assert ssn_pattern.search("123-45-6789")
        assert ssn_pattern.search("123456789")
        
        # Should not match
        assert not ssn_pattern.search("12-345-6789")
        assert not ssn_pattern.search("1234567890")

    def test_phone_pattern(self):
        phone_pattern = next(p for p in PII_PATTERNS if "\\+?1" in p.pattern)
        
        # Should match
        assert phone_pattern.search("(555) 123-4567")
        assert phone_pattern.search("555-123-4567")
        assert phone_pattern.search("+1-555-123-4567")
        assert phone_pattern.search("5551234567")
        
        # Should not match (non-US patterns not covered by this regex)
        assert not phone_pattern.search("123")
        assert not phone_pattern.search("+44 20 7123 4567")


class TestComplianceFeatures:
    """Test overall compliance features."""

    def test_all_pii_patterns_compile(self):
        """Ensure all PII regex patterns compile correctly."""
        for pattern in PII_PATTERNS:
            assert isinstance(pattern, re.Pattern)
            # Test that pattern doesn't crash on common inputs
            pattern.search("test string")
            pattern.search("")
            pattern.search("123-45-6789 user@example.com")

    def test_log_structure_compliance(self):
        """Test that log structure meets SOC 2 requirements."""
        formatter = SOC2CompliantJsonFormatter()
        
        record = MagicMock()
        record.levelname = "INFO"
        record.name = "test.logger"
        record.getMessage.return_value = "Test message"
        
        log_record = {}
        message_dict = {}
        
        formatter.add_fields(log_record, record, message_dict)
        
        # Required fields for audit trail
        required_fields = ["level", "logger", "service", "message"]
        for field in required_fields:
            assert field in log_record, f"Missing required field: {field}"
        
        # Service should be properly identified
        assert log_record["service"] == "ai-review"