"""Pytest configuration and fixtures for the Amemo SDK tests."""

from __future__ import annotations

import pytest
import respx
from httpx import Response


@pytest.fixture
def mock_api():
    """Create a mock API context using respx."""
    with respx.mock(base_url="https://api.amemo.ai") as mock:
        yield mock


@pytest.fixture
def sample_chat_response() -> dict:
    """Sample response from /chat endpoint."""
    return {
        "answer": "Your favorite color is blue.",
        "citations": [{"source_id": "src_123", "quote": "I love blue"}],
        "used_memory_ids": ["mem_123", "mem_456"],
    }


@pytest.fixture
def sample_ingest_response() -> dict:
    """Sample response from /ingest/chat endpoint."""
    return {
        "source_id": "src_abc123",
        "chunks": 3,
        "entities": [
            {
                "entity_id": "ent_user",
                "type": "self",
                "canonical_name": "User",
                "aliases": [],
            }
        ],
        "memories": [
            {
                "memory_id": "mem_xyz",
                "kind": "preference",
                "summary": "User likes blue",
                "entity_ids": ["ent_user"],
                "confidence": 0.85,
                "evidence_quotes": ["My favorite color is blue"],
            }
        ],
    }


@pytest.fixture
def sample_memory_item() -> dict:
    """Sample memory item response."""
    return {
        "memory_id": "mem_123",
        "kind": "preference",
        "summary": "User likes coffee",
        "confidence": 0.9,
        "updated_at": "2024-01-15T10:30:00Z",
        "entity_ids": ["ent_user"],
        "support": [{"source_id": "src_123", "quotes": ["I love coffee"]}],
        "status": "active",
        "key": "pref_beverage",
        "valid_from": "2024-01-15T10:30:00Z",
        "valid_to": None,
    }


@pytest.fixture
def sample_memory_list_response(sample_memory_item: dict) -> dict:
    """Sample response from /memories endpoint."""
    return {"items": [sample_memory_item]}


@pytest.fixture
def sample_health_response() -> dict:
    """Sample response from /health endpoint."""
    return {"status": "ok"}


@pytest.fixture
def sample_ready_response() -> dict:
    """Sample response from /ready endpoint."""
    return {
        "status": "ok",
        "neo4j": {"ok": True, "error": None},
        "qdrant": {"ok": True, "error": None},
    }


def create_json_response(data: dict, status_code: int = 200) -> Response:
    """Helper to create a JSON response."""
    import json

    return Response(
        status_code=status_code,
        content=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )


def create_error_response(
    status_code: int, detail: str, request_id: str | None = None
) -> Response:
    """Helper to create an error response."""
    import json

    headers = {"Content-Type": "application/json"}
    if request_id:
        headers["X-Request-Id"] = request_id
    return Response(
        status_code=status_code,
        content=json.dumps({"detail": detail}).encode(),
        headers=headers,
    )
