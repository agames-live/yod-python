"""Tests for the synchronous YodClient."""

from __future__ import annotations

import json
import pytest
import respx
from httpx import Response

from yod import YodClient
from yod.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


class TestClientInitialization:
    """Tests for client initialization."""

    def test_default_base_url(self):
        client = YodClient(api_key="sk-yod-test")
        assert client.config.base_url == "https://api.yod.agames.ai"
        client.close()

    def test_custom_base_url(self):
        client = YodClient(api_key="sk-yod-test", base_url="http://localhost:8000")
        assert client.config.base_url == "http://localhost:8000"
        client.close()

    def test_timeout_configuration(self):
        client = YodClient(api_key="sk-yod-test", timeout=60.0, connect_timeout=10.0)
        assert client.config.timeout == 60.0
        assert client.config.connect_timeout == 10.0
        client.close()

    def test_context_manager(self):
        with YodClient(api_key="sk-yod-test") as client:
            assert client._client is None  # Lazy initialization
        # After exiting, client should be closed
        assert client._client is None


class TestClientHeaders:
    """Tests for client header construction."""

    def test_api_key_auth(self):
        client = YodClient(api_key="sk-yod-test123")
        headers = client._build_headers()
        assert headers["Authorization"] == "Bearer sk-yod-test123"
        client.close()

    def test_bearer_token_auth(self):
        client = YodClient(bearer_token="jwt-token-xyz")
        headers = client._build_headers()
        assert headers["Authorization"] == "Bearer jwt-token-xyz"
        client.close()

    def test_user_id_header(self):
        client = YodClient(user_id="user-123")
        headers = client._build_headers()
        assert headers["X-User-Id"] == "user-123"
        client.close()

    def test_api_key_takes_priority(self):
        client = YodClient(api_key="sk-yod-key", bearer_token="jwt-token")
        headers = client._build_headers()
        assert headers["Authorization"] == "Bearer sk-yod-key"
        client.close()

    def test_user_agent_includes_version(self):
        from yod._version import __version__

        client = YodClient(api_key="sk-yod-test")
        headers = client._build_headers()
        assert headers["User-Agent"] == f"yod-python-sdk/{__version__}"
        client.close()


class TestChatEndpoint:
    """Tests for the /chat endpoint."""

    @respx.mock
    def test_chat_success(self, sample_chat_response: dict):
        respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(200, json=sample_chat_response)
        )

        with YodClient(api_key="sk-yod-test") as client:
            response = client.chat("What is my favorite color?")

        assert response.answer == "Your favorite color is blue."
        assert len(response.citations) == 1
        assert response.used_memory_ids == ["mem_123", "mem_456"]

    @respx.mock
    def test_chat_with_options(self, sample_chat_response: dict):
        route = respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(200, json=sample_chat_response)
        )

        with YodClient(api_key="sk-yod-test") as client:
            client.chat("Test?", language="fa", as_of="2024-01-01T00:00:00Z")

        request = route.calls[0].request
        body = json.loads(request.content)
        assert body["question"] == "Test?"
        assert body["language"] == "fa"
        assert body["as_of"] == "2024-01-01T00:00:00Z"


class TestIngestEndpoint:
    """Tests for the /ingest/chat endpoint."""

    @respx.mock
    def test_ingest_success(self, sample_ingest_response: dict):
        respx.post("https://api.yod.agames.ai/ingest/chat").mock(
            return_value=Response(200, json=sample_ingest_response)
        )

        with YodClient(api_key="sk-yod-test") as client:
            response = client.ingest_chat("My favorite color is blue")

        assert response.source_id == "src_abc123"
        assert response.chunks == 3
        assert len(response.entities) == 1
        assert len(response.memories) == 1


class TestMemoriesEndpoint:
    """Tests for /memories endpoints."""

    @respx.mock
    def test_list_memories(self, sample_memory_list_response: dict):
        respx.get("https://api.yod.agames.ai/memories").mock(
            return_value=Response(200, json=sample_memory_list_response)
        )

        with YodClient(api_key="sk-yod-test") as client:
            response = client.list_memories()

        assert len(response.items) == 1
        assert response.items[0].memory_id == "mem_123"

    @respx.mock
    def test_list_memories_with_filters(self, sample_memory_list_response: dict):
        route = respx.get("https://api.yod.agames.ai/memories").mock(
            return_value=Response(200, json=sample_memory_list_response)
        )

        with YodClient(api_key="sk-yod-test") as client:
            client.list_memories(kind="preference", search="coffee", limit=10)

        request = route.calls[0].request
        assert "kind=preference" in str(request.url)
        assert "search=coffee" in str(request.url)
        assert "limit=10" in str(request.url)

    @respx.mock
    def test_get_memory(self, sample_memory_item: dict):
        respx.get("https://api.yod.agames.ai/memories/mem_123").mock(
            return_value=Response(200, json=sample_memory_item)
        )

        with YodClient(api_key="sk-yod-test") as client:
            memory = client.get_memory("mem_123")

        assert memory.memory_id == "mem_123"
        assert memory.kind == "preference"

    @respx.mock
    def test_delete_memory(self):
        respx.delete("https://api.yod.agames.ai/memories/mem_123").mock(
            return_value=Response(200, json={"ok": True, "qdrant_deleted": 2})
        )

        with YodClient(api_key="sk-yod-test") as client:
            result = client.delete_memory("mem_123")

        assert result["ok"] is True
        assert result["qdrant_deleted"] == 2


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @respx.mock
    def test_health(self, sample_health_response: dict):
        respx.get("https://api.yod.agames.ai/health").mock(
            return_value=Response(200, json=sample_health_response)
        )

        with YodClient(api_key="sk-yod-test") as client:
            response = client.health()

        assert response.status == "ok"

    @respx.mock
    def test_ready(self, sample_ready_response: dict):
        respx.get("https://api.yod.agames.ai/ready").mock(
            return_value=Response(200, json=sample_ready_response)
        )

        with YodClient(api_key="sk-yod-test") as client:
            response = client.ready()

        assert response.status == "ok"
        assert response.neo4j.ok is True
        assert response.qdrant.ok is True


class TestErrorHandling:
    """Tests for error response handling."""

    @respx.mock
    def test_authentication_error(self):
        respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(401, json={"detail": "Invalid token"})
        )

        with YodClient(api_key="bad-key") as client:
            with pytest.raises(AuthenticationError) as exc_info:
                client.chat("Test")

        assert "Invalid token" in str(exc_info.value)
        assert exc_info.value.status_code == 401

    @respx.mock
    def test_authorization_error(self):
        respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(403, json={"detail": "Forbidden"})
        )

        with YodClient(api_key="sk-yod-test") as client:
            with pytest.raises(AuthorizationError):
                client.chat("Test")

    @respx.mock
    def test_not_found_error(self):
        respx.get("https://api.yod.agames.ai/memories/nonexistent").mock(
            return_value=Response(404, json={"detail": "Memory not found"})
        )

        with YodClient(api_key="sk-yod-test") as client:
            with pytest.raises(NotFoundError):
                client.get_memory("nonexistent")

    @respx.mock
    def test_validation_error(self):
        respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(422, json={"detail": "Question too short"})
        )

        with YodClient(api_key="sk-yod-test") as client:
            with pytest.raises(ValidationError):
                client.chat("?")

    @respx.mock
    def test_rate_limit_error_with_retry_after(self):
        respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(
                429,
                json={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "30"},
            )
        )

        # Disable retries to test error handling directly
        with YodClient(api_key="sk-yod-test", max_retries=0) as client:
            with pytest.raises(RateLimitError) as exc_info:
                client.chat("Test")

        assert exc_info.value.retry_after == 30.0
        assert exc_info.value.status_code == 429

    @respx.mock
    def test_server_error(self):
        respx.post("https://api.yod.agames.ai/chat").mock(
            return_value=Response(500, json={"detail": "Internal error"})
        )

        with YodClient(api_key="sk-yod-test", max_retries=0) as client:
            with pytest.raises(ServerError) as exc_info:
                client.chat("Test")

        assert exc_info.value.status_code == 500
