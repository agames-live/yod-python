"""Tests for Yod SDK models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from yod.models import (
    ChatResponse,
    Citation,
    ExtractedEntity,
    ExtractedMemory,
    HealthResponse,
    IngestResponse,
    MemoryItem,
    MemoryListResponse,
    MemorySupport,
    ReadyResponse,
    ServiceStatus,
    IngestChatRequest,
    ChatRequest,
    MemoryUpdateRequest,
)


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_parse_valid_response(self, sample_chat_response: dict):
        response = ChatResponse.model_validate(sample_chat_response)
        assert response.answer == "Your favorite color is blue."
        assert len(response.citations) == 1
        assert response.citations[0].source_id == "src_123"
        assert response.used_memory_ids == ["mem_123", "mem_456"]

    def test_parse_minimal_response(self):
        response = ChatResponse.model_validate({"answer": "Test"})
        assert response.answer == "Test"
        assert response.citations == []
        assert response.used_memory_ids == []


class TestMemoryItem:
    """Tests for MemoryItem model."""

    def test_parse_full_memory(self, sample_memory_item: dict):
        memory = MemoryItem.model_validate(sample_memory_item)
        assert memory.memory_id == "mem_123"
        assert memory.kind == "preference"
        assert memory.summary == "User likes coffee"
        assert memory.confidence == 0.9
        assert memory.status == "active"
        assert memory.key == "pref_beverage"
        assert len(memory.support) == 1
        assert memory.support[0].source_id == "src_123"

    def test_parse_minimal_memory(self):
        memory = MemoryItem.model_validate({
            "memory_id": "mem_1",
            "kind": "fact",
            "summary": "Test fact",
            "confidence": 0.5,
        })
        assert memory.memory_id == "mem_1"
        assert memory.entity_ids == []
        assert memory.support == []
        assert memory.status is None


class TestMemoryListResponse:
    """Tests for MemoryListResponse model."""

    def test_parse_list_response(self, sample_memory_list_response: dict):
        response = MemoryListResponse.model_validate(sample_memory_list_response)
        assert len(response.items) == 1
        assert response.items[0].memory_id == "mem_123"

    def test_parse_empty_list(self):
        response = MemoryListResponse.model_validate({"items": []})
        assert response.items == []


class TestIngestResponse:
    """Tests for IngestResponse model."""

    def test_parse_full_response(self, sample_ingest_response: dict):
        response = IngestResponse.model_validate(sample_ingest_response)
        assert response.source_id == "src_abc123"
        assert response.chunks == 3
        assert len(response.entities) == 1
        assert response.entities[0].entity_id == "ent_user"
        assert len(response.memories) == 1
        assert response.memories[0].kind == "preference"

    def test_parse_minimal_response(self):
        response = IngestResponse.model_validate({"source_id": "src_1"})
        assert response.source_id == "src_1"
        assert response.chunks == 0
        assert response.entities == []
        assert response.memories == []


class TestReadyResponse:
    """Tests for ReadyResponse model with nested ServiceStatus."""

    def test_parse_healthy_response(self, sample_ready_response: dict):
        response = ReadyResponse.model_validate(sample_ready_response)
        assert response.status == "ok"
        assert response.neo4j is not None
        assert response.neo4j.ok is True
        assert response.neo4j.error is None
        assert response.qdrant is not None
        assert response.qdrant.ok is True

    def test_parse_degraded_response(self):
        response = ReadyResponse.model_validate({
            "status": "degraded",
            "neo4j": {"ok": False, "error": "Connection refused"},
            "qdrant": {"ok": True},
        })
        assert response.status == "degraded"
        assert response.neo4j.ok is False
        assert response.neo4j.error == "Connection refused"
        assert response.qdrant.ok is True

    def test_parse_minimal_response(self):
        response = ReadyResponse.model_validate({"status": "ok"})
        assert response.status == "ok"
        assert response.neo4j is None
        assert response.qdrant is None


class TestServiceStatus:
    """Tests for ServiceStatus model."""

    def test_parse_healthy(self):
        status = ServiceStatus.model_validate({"ok": True})
        assert status.ok is True
        assert status.error is None

    def test_parse_unhealthy(self):
        status = ServiceStatus.model_validate({"ok": False, "error": "Timeout"})
        assert status.ok is False
        assert status.error == "Timeout"


class TestRequestModels:
    """Tests for request models."""

    def test_ingest_chat_request_valid(self):
        req = IngestChatRequest(text="Hello world")
        assert req.text == "Hello world"
        assert req.source_id is None

    def test_ingest_chat_request_with_options(self):
        req = IngestChatRequest(
            text="Test",
            source_id="src_1",
            timestamp="2024-01-15T10:00:00Z",
        )
        assert req.source_id == "src_1"
        assert req.timestamp == "2024-01-15T10:00:00Z"

    def test_ingest_chat_request_empty_text_fails(self):
        with pytest.raises(PydanticValidationError):
            IngestChatRequest(text="")

    def test_chat_request_valid(self):
        req = ChatRequest(question="What is my name?")
        assert req.question == "What is my name?"
        assert req.language is None
        assert req.as_of is None

    def test_chat_request_with_options(self):
        req = ChatRequest(
            question="Test?",
            language="en",
            as_of="2024-01-01T00:00:00Z",
        )
        assert req.language == "en"
        assert req.as_of == "2024-01-01T00:00:00Z"

    def test_memory_update_request(self):
        req = MemoryUpdateRequest(confidence=0.8)
        assert req.confidence == 0.8
        assert req.kind is None
        assert req.summary is None

    def test_memory_update_request_confidence_bounds(self):
        with pytest.raises(PydanticValidationError):
            MemoryUpdateRequest(confidence=1.5)
        with pytest.raises(PydanticValidationError):
            MemoryUpdateRequest(confidence=-0.1)
