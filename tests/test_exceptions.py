"""Tests for Amemo SDK exceptions."""

from __future__ import annotations

import pytest

from amemo.exceptions import (
    AmemoError,
    AmemoAPIError,
    AmemoConnectionError,
    AmemoTimeoutError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    # Deprecated aliases
    ConnectionError as DeprecatedConnectionError,
    TimeoutError as DeprecatedTimeoutError,
)


class TestExceptionHierarchy:
    """Tests for exception class hierarchy."""

    def test_amemo_error_is_base(self):
        assert issubclass(AmemoAPIError, AmemoError)
        assert issubclass(AmemoConnectionError, AmemoError)
        assert issubclass(AmemoTimeoutError, AmemoError)

    def test_api_errors_inherit_from_amemo_api_error(self):
        assert issubclass(AuthenticationError, AmemoAPIError)
        assert issubclass(AuthorizationError, AmemoAPIError)
        assert issubclass(NotFoundError, AmemoAPIError)
        assert issubclass(ValidationError, AmemoAPIError)
        assert issubclass(RateLimitError, AmemoAPIError)
        assert issubclass(ServerError, AmemoAPIError)

    def test_deprecated_aliases_point_to_new_classes(self):
        assert DeprecatedConnectionError is AmemoConnectionError
        assert DeprecatedTimeoutError is AmemoTimeoutError


class TestAmemoAPIError:
    """Tests for AmemoAPIError."""

    def test_stores_status_code(self):
        error = AmemoAPIError("Test error", status_code=500)
        assert error.status_code == 500

    def test_stores_response_body(self):
        body = {"detail": "Something went wrong"}
        error = AmemoAPIError("Test", status_code=500, response_body=body)
        assert error.response_body == body

    def test_stores_request_id(self):
        error = AmemoAPIError("Test", status_code=500, request_id="req-123")
        assert error.request_id == "req-123"

    def test_str_includes_status_code(self):
        error = AmemoAPIError("Server error", status_code=500)
        assert "500" in str(error)
        assert "Server error" in str(error)

    def test_str_includes_request_id(self):
        error = AmemoAPIError("Error", status_code=500, request_id="req-456")
        error_str = str(error)
        assert "req-456" in error_str


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_message(self):
        error = AuthenticationError()
        assert "Authentication failed" in str(error)
        assert error.status_code == 401

    def test_custom_message(self):
        error = AuthenticationError("Invalid API key")
        assert "Invalid API key" in str(error)

    def test_with_request_id(self):
        error = AuthenticationError(request_id="req-auth")
        assert error.request_id == "req-auth"


class TestAuthorizationError:
    """Tests for AuthorizationError."""

    def test_default_message(self):
        error = AuthorizationError()
        assert "Permission denied" in str(error)
        assert error.status_code == 403


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_default_message(self):
        error = NotFoundError()
        assert "not found" in str(error).lower()
        assert error.status_code == 404


class TestValidationError:
    """Tests for ValidationError."""

    def test_default_message(self):
        error = ValidationError()
        assert error.status_code == 422

    def test_stores_validation_details(self):
        body = {"detail": [{"loc": ["body", "text"], "msg": "field required"}]}
        error = ValidationError("Validation failed", response_body=body)
        assert error.response_body == body


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_default_message(self):
        error = RateLimitError()
        assert error.status_code == 429

    def test_stores_retry_after(self):
        error = RateLimitError(retry_after=30.0)
        assert error.retry_after == 30.0

    def test_str_includes_retry_after(self):
        error = RateLimitError("Rate limited", retry_after=60.0)
        error_str = str(error)
        assert "60" in error_str

    def test_str_without_retry_after(self):
        error = RateLimitError("Rate limited")
        error_str = str(error)
        assert "429" in error_str


class TestServerError:
    """Tests for ServerError."""

    def test_default_status_code(self):
        error = ServerError()
        assert error.status_code == 500

    def test_custom_status_code(self):
        error = ServerError("Bad gateway", status_code=502)
        assert error.status_code == 502

    def test_accepts_5xx_codes(self):
        for code in [500, 501, 502, 503, 504]:
            error = ServerError(status_code=code)
            assert error.status_code == code


class TestAmemoConnectionError:
    """Tests for AmemoConnectionError."""

    def test_is_amemo_error(self):
        error = AmemoConnectionError("Connection refused")
        assert isinstance(error, AmemoError)
        assert "Connection refused" in str(error)


class TestAmemoTimeoutError:
    """Tests for AmemoTimeoutError."""

    def test_is_amemo_error(self):
        error = AmemoTimeoutError("Request timed out")
        assert isinstance(error, AmemoError)
        assert "timed out" in str(error)


class TestExceptionCatching:
    """Tests for catching exceptions in try/except blocks."""

    def test_catch_all_amemo_errors(self):
        errors = [
            AmemoAPIError("test", status_code=400),
            AuthenticationError(),
            NotFoundError(),
            RateLimitError(),
            AmemoConnectionError("conn error"),
            AmemoTimeoutError("timeout"),
        ]

        for error in errors:
            try:
                raise error
            except AmemoError:
                pass  # Should catch all

    def test_catch_all_api_errors(self):
        errors = [
            AuthenticationError(),
            AuthorizationError(),
            NotFoundError(),
            ValidationError(),
            RateLimitError(),
            ServerError(),
        ]

        for error in errors:
            try:
                raise error
            except AmemoAPIError:
                pass  # Should catch all API errors
