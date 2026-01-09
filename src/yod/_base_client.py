"""Base client with shared logic for sync and async clients."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, NoReturn

from yod._retry import RetryConfig
from yod._version import __version__
from yod.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    YodAPIError,
)


@dataclass
class ClientConfig:
    """Configuration for the Yod client."""

    base_url: str = "https://api.yod.agames.ai"

    # Authentication (priority: api_key > bearer_token > user_id)
    api_key: str | None = None  # Yod API key (sk-yod-*)
    bearer_token: str | None = None  # JWT token (alternative)
    user_id: str | None = None  # X-User-Id header (dev mode only)

    # Timeouts
    timeout: float = 30.0
    connect_timeout: float = 5.0

    # Retry configuration
    max_retries: int = 3

    # Custom headers
    custom_headers: dict[str, str] = field(default_factory=dict)


class BaseClient:
    """
    Base client with shared configuration and helper methods.

    Not intended for direct use - use YodClient or AsyncYodClient.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        bearer_token: str | None = None,
        user_id: str | None = None,
        timeout: float = 30.0,
        connect_timeout: float = 5.0,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """
        Initialize client with configuration.

        Authentication priority:
        1. api_key - Yod API key (sk-yod-*) - recommended for production
        2. bearer_token - JWT token (alternative auth method)
        3. user_id - X-User-Id header (dev mode only)

        Args:
            api_key: Yod API key (starts with sk-yod-)
            base_url: API base URL (default: https://api.yod.agames.ai)
            bearer_token: JWT bearer token (alternative to api_key)
            user_id: User ID for X-User-Id header (dev mode)
            timeout: Request timeout in seconds
            connect_timeout: Connection timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.config = ClientConfig(
            base_url=base_url or "https://api.yod.agames.ai",
            api_key=api_key,
            bearer_token=bearer_token,
            user_id=user_id,
            timeout=timeout,
            connect_timeout=connect_timeout,
            max_retries=max_retries,
            custom_headers=kwargs.get("custom_headers", {}),
        )

        self.retry_config = RetryConfig(max_retries=max_retries)

    def _build_headers(self) -> dict[str, str]:
        """Construct request headers with authentication."""
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"yod-python-sdk/{__version__}",
        }

        # Add authentication headers (priority: api_key > bearer_token > user_id)
        if self.config.api_key:
            # API keys are sent as Bearer tokens
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        elif self.config.bearer_token:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"

        # X-User-Id for dev mode (works alongside or without auth)
        if self.config.user_id:
            headers["X-User-Id"] = self.config.user_id

        # Add custom headers
        headers.update(self.config.custom_headers)

        return headers

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        base = self.config.base_url.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"

    def _handle_error_response(
        self,
        status_code: int,
        body: dict[str, Any] | None,
        request_id: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> NoReturn:
        """Raise appropriate exception based on status code."""
        message = "Unknown error"
        if body:
            message = body.get("detail", body.get("message", str(body)))

        if status_code == 401:
            raise AuthenticationError(message, response_body=body, request_id=request_id)
        elif status_code == 403:
            raise AuthorizationError(message, response_body=body, request_id=request_id)
        elif status_code == 404:
            raise NotFoundError(message, response_body=body, request_id=request_id)
        elif status_code == 422:
            raise ValidationError(message, response_body=body, request_id=request_id)
        elif status_code == 429:
            retry_after = None
            if headers:
                retry_after_str = headers.get("Retry-After") or headers.get("retry-after")
                if retry_after_str:
                    try:
                        retry_after = float(retry_after_str)
                    except ValueError:
                        pass
            raise RateLimitError(
                message, retry_after=retry_after, response_body=body, request_id=request_id
            )
        elif status_code >= 500:
            raise ServerError(
                message, status_code=status_code, response_body=body, request_id=request_id
            )
        else:
            raise YodAPIError(
                message, status_code=status_code, response_body=body, request_id=request_id
            )

    def _parse_response_body(self, content: bytes) -> dict[str, Any] | list[Any] | None:
        """Parse response body as JSON, return None on failure."""
        if not content:
            return None
        try:
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return None
