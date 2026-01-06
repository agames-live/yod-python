"""Request models for the Yod SDK."""

from __future__ import annotations

from pydantic import BaseModel, Field


class IngestChatRequest(BaseModel):
    """Request body for ingesting chat/text data."""

    text: str = Field(min_length=1, max_length=100_000, description="Text content to ingest")
    source_id: str | None = Field(default=None, description="Optional source identifier")
    timestamp: str | None = Field(default=None, description="Optional ISO8601 timestamp")


class ChatRequest(BaseModel):
    """Request body for querying memories."""

    question: str = Field(min_length=1, max_length=10_000, description="Question to ask")
    language: str | None = Field(
        default=None, description="Force response in specific language (e.g., 'en', 'fa')"
    )
    as_of: str | None = Field(
        default=None, description="ISO8601 timestamp for temporal queries"
    )


class MemoryUpdateRequest(BaseModel):
    """Request body for updating a memory."""

    kind: str | None = Field(default=None, description="New memory kind")
    summary: str | None = Field(default=None, description="New summary text")
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="New confidence score (0.0-1.0)"
    )
