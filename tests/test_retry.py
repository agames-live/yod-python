"""Tests for the retry logic."""

from __future__ import annotations

import pytest
from httpx import Response

from yod._retry import (
    RetryConfig,
    calculate_delay,
    execute_with_retry_async,
    execute_with_retry_sync,
    get_retry_after,
    should_retry,
)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_values(self):
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0
        assert config.backoff_multiplier == 2.0
        assert config.retry_on_status == (429, 500, 502, 503, 504)

    def test_custom_values(self):
        config = RetryConfig(
            max_retries=5,
            initial_delay=1.0,
            max_delay=60.0,
        )
        assert config.max_retries == 5
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0


class TestCalculateDelay:
    """Tests for calculate_delay function."""

    def test_first_attempt_uses_initial_delay(self):
        config = RetryConfig(initial_delay=0.5, jitter=0)
        delay = calculate_delay(0, config)
        assert delay == 0.5

    def test_exponential_backoff(self):
        config = RetryConfig(initial_delay=1.0, backoff_multiplier=2.0, jitter=0)
        assert calculate_delay(0, config) == 1.0
        assert calculate_delay(1, config) == 2.0
        assert calculate_delay(2, config) == 4.0
        assert calculate_delay(3, config) == 8.0

    def test_respects_max_delay(self):
        config = RetryConfig(
            initial_delay=10.0, backoff_multiplier=2.0, max_delay=15.0, jitter=0
        )
        # 10 * 2^2 = 40, but capped at 15
        delay = calculate_delay(2, config)
        assert delay == 15.0

    def test_uses_retry_after_when_provided(self):
        config = RetryConfig(initial_delay=1.0, max_delay=30.0)
        delay = calculate_delay(0, config, retry_after=10.0)
        assert delay == 10.0

    def test_retry_after_capped_by_max_delay(self):
        config = RetryConfig(max_delay=5.0)
        delay = calculate_delay(0, config, retry_after=100.0)
        assert delay == 5.0

    def test_jitter_adds_variation(self):
        config = RetryConfig(initial_delay=1.0, jitter=0.5)
        delays = [calculate_delay(0, config) for _ in range(10)]
        # With 50% jitter on 1.0, delays should vary between 0.5 and 1.5
        assert all(0.5 <= d <= 1.5 for d in delays)
        # They shouldn't all be exactly the same (probabilistically)
        assert len(set(delays)) > 1


class TestShouldRetry:
    """Tests for should_retry function."""

    def test_retries_on_configured_status_codes(self):
        config = RetryConfig()
        assert should_retry(429, config) is True
        assert should_retry(500, config) is True
        assert should_retry(502, config) is True
        assert should_retry(503, config) is True
        assert should_retry(504, config) is True

    def test_does_not_retry_client_errors(self):
        config = RetryConfig()
        assert should_retry(400, config) is False
        assert should_retry(401, config) is False
        assert should_retry(403, config) is False
        assert should_retry(404, config) is False
        assert should_retry(422, config) is False

    def test_does_not_retry_success(self):
        config = RetryConfig()
        assert should_retry(200, config) is False
        assert should_retry(201, config) is False


class TestGetRetryAfter:
    """Tests for get_retry_after function."""

    def test_extracts_numeric_retry_after(self):
        response = Response(429, headers={"Retry-After": "30"})
        assert get_retry_after(response) == 30.0

    def test_extracts_float_retry_after(self):
        response = Response(429, headers={"Retry-After": "1.5"})
        assert get_retry_after(response) == 1.5

    def test_returns_none_when_missing(self):
        response = Response(429)
        assert get_retry_after(response) is None

    def test_returns_none_for_invalid_format(self):
        # HTTP-date format is not supported
        response = Response(429, headers={"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"})
        assert get_retry_after(response) is None


class TestExecuteWithRetrySync:
    """Tests for synchronous retry execution."""

    def test_returns_immediately_on_success(self):
        call_count = 0

        def success_request():
            nonlocal call_count
            call_count += 1
            return Response(200, json={"ok": True})

        config = RetryConfig(max_retries=3)
        response = execute_with_retry_sync(success_request, config)

        assert response.status_code == 200
        assert call_count == 1

    def test_retries_on_server_error(self):
        call_count = 0

        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return Response(500, json={"error": "Server error"})
            return Response(200, json={"ok": True})

        config = RetryConfig(max_retries=3, initial_delay=0.01, jitter=0)
        response = execute_with_retry_sync(fail_then_succeed, config)

        assert response.status_code == 200
        assert call_count == 3

    def test_returns_last_error_after_max_retries(self):
        call_count = 0

        def always_fail():
            nonlocal call_count
            call_count += 1
            return Response(500, json={"error": "Server error"})

        config = RetryConfig(max_retries=2, initial_delay=0.01, jitter=0)
        response = execute_with_retry_sync(always_fail, config)

        assert response.status_code == 500
        assert call_count == 3  # Initial + 2 retries

    def test_does_not_retry_client_errors(self):
        call_count = 0

        def client_error():
            nonlocal call_count
            call_count += 1
            return Response(400, json={"error": "Bad request"})

        config = RetryConfig(max_retries=3, initial_delay=0.01)
        response = execute_with_retry_sync(client_error, config)

        assert response.status_code == 400
        assert call_count == 1


class TestExecuteWithRetryAsync:
    """Tests for asynchronous retry execution."""

    @pytest.mark.asyncio
    async def test_returns_immediately_on_success(self):
        call_count = 0

        async def success_request():
            nonlocal call_count
            call_count += 1
            return Response(200, json={"ok": True})

        config = RetryConfig(max_retries=3)
        response = await execute_with_retry_async(success_request, config)

        assert response.status_code == 200
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_server_error(self):
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return Response(503, json={"error": "Unavailable"})
            return Response(200, json={"ok": True})

        config = RetryConfig(max_retries=3, initial_delay=0.01, jitter=0)
        response = await execute_with_retry_async(fail_then_succeed, config)

        assert response.status_code == 200
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_returns_last_error_after_max_retries(self):
        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            return Response(502, json={"error": "Bad gateway"})

        config = RetryConfig(max_retries=1, initial_delay=0.01, jitter=0)
        response = await execute_with_retry_async(always_fail, config)

        assert response.status_code == 502
        assert call_count == 2  # Initial + 1 retry
