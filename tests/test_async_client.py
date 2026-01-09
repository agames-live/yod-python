"""Tests for the asynchronous AsyncYodClient."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from yod import AsyncYodClient
from yod.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)


class TestAsyncClientInitialization:
    """Tests for async client initialization."""

    def test_default_base_url(self):
        client = AsyncYodClient(api_key="sk-yod-test")
        assert client.config.base_url == "https://api.yod.agames.ai"

    def test_timeout_configuration(self):
        client = AsyncYodClient(
            api_key="sk-yod-test", timeout=60.0, connect_timeout=10.0
        )
        assert client.config.timeout == 60.0
        assert client.config.connect_timeout == 10.0


class TestAsyncContextManager:
    """Tests for async context manager."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with AsyncYodClient(api_key="sk-yod-test") as client:
            assert client._client is None  # Lazy initialization
        # After exiting, client should be closed
        assert client._client is None


class TestAsyncChatEndpoint:
    """Tests for the async /chat endpoint."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_chat_success(self, sample_chat_response: dict):
        respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(200, json=sample_chat_response)
        )

        async with AsyncYodClient(api_key="sk-yod-test") as client:
            response = await client.chat("What is my favorite color?")

        assert response.answer == "Your favorite color is blue."
        assert len(response.citations) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_chat_with_options(self, sample_chat_response: dict):
        route = respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(200, json=sample_chat_response)
        )

        async with AsyncYodClient(api_key="sk-yod-test") as client:
            await client.chat("Test?", language="en", as_of="2024-01-01T00:00:00Z")

        request = route.calls[0].request
        body = json.loads(request.content)
        assert body["question"] == "Test?"
        assert body["language"] == "en"


class TestAsyncIngestEndpoint:
    """Tests for the async /ingest/chat endpoint."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_ingest_success(self, sample_ingest_response: dict):
        respx.post("https://api.yod.agames.ai/ingest/chat").mock(
            return_value=Response(200, json=sample_ingest_response)
        )

        async with AsyncYodClient(api_key="sk-yod-test") as client:
            response = await client.ingest_chat("My favorite color is blue")

        assert response.source_id == "src_abc123"
        assert response.chunks == 3


class TestAsyncMemoriesEndpoint:
    """Tests for async /memories endpoints."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_memories(self, sample_memory_list_response: dict):
        respx.get("https://api.yod.agames.ai/memories").mock(
            return_value=Response(200, json=sample_memory_list_response)
        )

        async with AsyncYodClient(api_key="sk-yod-test") as client:
            response = await client.list_memories()

        assert len(response.items) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_memory(self, sample_memory_item: dict):
        respx.get("https://api.yod.agames.ai/memories/mem_123").mock(
            return_value=Response(200, json=sample_memory_item)
        )

        async with AsyncYodClient(api_key="sk-yod-test") as client:
            memory = await client.get_memory("mem_123")

        assert memory.memory_id == "mem_123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_delete_memory(self):
        respx.delete("https://api.yod.agames.ai/memories/mem_123").mock(
            return_value=Response(200, json={"ok": True, "qdrant_deleted": 1})
        )

        async with AsyncYodClient(api_key="sk-yod-test") as client:
            result = await client.delete_memory("mem_123")

        assert result["ok"] is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_memory_history(self, sample_memory_list_response: dict):
        respx.get("https://api.yod.agames.ai/memories/mem_123/history").mock(
            return_value=Response(200, json=sample_memory_list_response)
        )

        async with AsyncYodClient(api_key="sk-yod-test") as client:
            response = await client.get_memory_history("mem_123")

        assert len(response.items) == 1


class TestAsyncHealthEndpoints:
    """Tests for async health check endpoints."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_health(self, sample_health_response: dict):
        respx.get("https://api.yod.agames.ai/health").mock(
            return_value=Response(200, json=sample_health_response)
        )

        async with AsyncYodClient(api_key="sk-yod-test") as client:
            response = await client.health()

        assert response.status == "ok"

    @pytest.mark.asyncio
    @respx.mock
    async def test_ready(self, sample_ready_response: dict):
        respx.get("https://api.yod.agames.ai/ready").mock(
            return_value=Response(200, json=sample_ready_response)
        )

        async with AsyncYodClient(api_key="sk-yod-test") as client:
            response = await client.ready()

        assert response.status == "ok"
        assert response.neo4j.ok is True


class TestAsyncErrorHandling:
    """Tests for async error response handling."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_authentication_error(self):
        respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(401, json={"detail": "Invalid token"})
        )

        async with AsyncYodClient(api_key="bad-key") as client:
            with pytest.raises(AuthenticationError):
                await client.chat("Test")

    @pytest.mark.asyncio
    @respx.mock
    async def test_not_found_error(self):
        respx.get("https://api.yod.agames.ai/memories/nonexistent").mock(
            return_value=Response(404, json={"detail": "Not found"})
        )

        async with AsyncYodClient(api_key="sk-yod-test") as client:
            with pytest.raises(NotFoundError):
                await client.get_memory("nonexistent")

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limit_with_retry_after(self):
        respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(
                429,
                json={"detail": "Rate limited"},
                headers={"Retry-After": "60"},
            )
        )

        async with AsyncYodClient(api_key="sk-yod-test", max_retries=0) as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.chat("Test")

        assert exc_info.value.retry_after == 60.0
