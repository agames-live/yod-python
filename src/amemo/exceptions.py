"""Custom exceptions for the Amemo SDK."""

from __future__ import annotations

from typing import Any


class AmemoError(Exception):
    """Base exception for all Amemo SDK errors."""

    pass


class AmemoAPIError(AmemoError):
    """API returned an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        self.request_id = request_id
        super().__init__(message)

    def __str__(self) -> str:
        msg = f"{self.status_code}: {super().__str__()}"
        if self.request_id:
            msg += f" (request_id: {self.request_id})"
        return msg


class AuthenticationError(AmemoAPIError):
    """401 Unauthorized - Invalid or missing credentials."""

    def __init__(
        self,
        message: str = "Authentication failed",
        response_body: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, status_code=401, response_body=response_body, request_id=request_id)


class AuthorizationError(AmemoAPIError):
    """403 Forbidden - Insufficient permissions."""

    def __init__(
        self,
        message: str = "Permission denied",
        response_body: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, status_code=403, response_body=response_body, request_id=request_id)


class NotFoundError(AmemoAPIError):
    """404 Not Found - Resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        response_body: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, status_code=404, response_body=response_body, request_id=request_id)


class ValidationError(AmemoAPIError):
    """422 Unprocessable Entity - Request validation failed."""

    def __init__(
        self,
        message: str = "Validation error",
        response_body: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, status_code=422, response_body=response_body, request_id=request_id)


class RateLimitError(AmemoAPIError):
    """429 Too Many Requests - Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
        response_body: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, status_code=429, response_body=response_body, request_id=request_id)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.retry_after:
            msg += f" (retry after {self.retry_after}s)"
        return msg


class ServerError(AmemoAPIError):
    """5xx Server Error - API is experiencing issues."""

    def __init__(
        self,
        message: str = "Server error",
        status_code: int = 500,
        response_body: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body, request_id=request_id)


class AmemoConnectionError(AmemoError):
    """Network-level connection error."""

    pass


class AmemoTimeoutError(AmemoError):
    """Request timed out."""

    pass


# Backwards compatibility aliases (deprecated - will be removed in 1.0)
ConnectionError = AmemoConnectionError
TimeoutError = AmemoTimeoutError
