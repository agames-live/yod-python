"""Retry logic with exponential backoff for the Yod SDK."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

import httpx


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    initial_delay: float = 0.5
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    retry_on_status: tuple[int, ...] = (429, 500, 502, 503, 504)
    jitter: float = 0.1


def calculate_delay(
    attempt: int,
    config: RetryConfig,
    retry_after: float | None = None,
) -> float:
    """
    Calculate delay before next retry.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
        retry_after: Value from Retry-After header if present

    Returns:
        Delay in seconds before next retry
    """
    if retry_after is not None:
        return min(retry_after, config.max_delay)

    delay = config.initial_delay * (config.backoff_multiplier ** attempt)
    delay = min(delay, config.max_delay)

    # Add jitter to prevent thundering herd
    jitter_range = delay * config.jitter
    delay += random.uniform(-jitter_range, jitter_range)

    return max(0.0, delay)


def should_retry(status_code: int, config: RetryConfig) -> bool:
    """Determine if request should be retried based on status code."""
    return status_code in config.retry_on_status


def get_retry_after(response: httpx.Response) -> float | None:
    """Extract Retry-After header value in seconds."""
    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return None

    try:
        return float(retry_after)
    except ValueError:
        # Could be HTTP-date format, ignore for simplicity
        return None


def execute_with_retry_sync(
    request_func: Callable[[], httpx.Response],
    config: RetryConfig,
) -> httpx.Response:
    """
    Execute a sync request with automatic retry on failure.

    Args:
        request_func: Function that makes the HTTP request
        config: Retry configuration

    Returns:
        HTTP response

    Raises:
        The last exception if all retries fail
    """
    last_response: httpx.Response | None = None

    for attempt in range(config.max_retries + 1):
        try:
            response = request_func()

            if response.status_code < 400:
                return response

            if not should_retry(response.status_code, config):
                return response

            if attempt == config.max_retries:
                return response

            last_response = response
            retry_after = get_retry_after(response)
            delay = calculate_delay(attempt, config, retry_after)
            time.sleep(delay)

        except (httpx.ConnectError, httpx.TimeoutException):
            if attempt == config.max_retries:
                raise
            delay = calculate_delay(attempt, config)
            time.sleep(delay)

    # Should not reach here, but return last response if it does
    if last_response is not None:
        return last_response
    raise RuntimeError("Retry logic failed unexpectedly")


async def execute_with_retry_async(
    request_func: Callable[[], Awaitable[httpx.Response]],
    config: RetryConfig,
) -> httpx.Response:
    """
    Execute an async request with automatic retry on failure.

    Args:
        request_func: Async coroutine function that makes the HTTP request
        config: Retry configuration

    Returns:
        HTTP response

    Raises:
        The last exception if all retries fail
    """
    import asyncio

    last_response: httpx.Response | None = None

    for attempt in range(config.max_retries + 1):
        try:
            response = await request_func()

            if response.status_code < 400:
                return response

            if not should_retry(response.status_code, config):
                return response

            if attempt == config.max_retries:
                return response

            last_response = response
            retry_after = get_retry_after(response)
            delay = calculate_delay(attempt, config, retry_after)
            await asyncio.sleep(delay)

        except (httpx.ConnectError, httpx.TimeoutException):
            if attempt == config.max_retries:
                raise
            delay = calculate_delay(attempt, config)
            await asyncio.sleep(delay)

    if last_response is not None:
        return last_response
    raise RuntimeError("Retry logic failed unexpectedly")
