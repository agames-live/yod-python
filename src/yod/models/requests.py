"""Request models for the Yod SDK."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Type aliases for request enums
FeedbackType = Literal["positive", "negative", "neutral"]
MemoryToolAction = Literal["remember", "forget", "update"]


class IngestChatRequest(BaseModel):
    """Request body for ingesting chat/text data."""

    text: str = Field(min_length=1, max_length=100_000, description="Text content to ingest")
    source_id: str | None = Field(default=None, description="Optional source identifier")
    timestamp: str | None = Field(default=None, description="Optional ISO8601 timestamp")
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for memory isolation across different contexts",
    )
    agent_id: str | None = Field(
        default=None, description="Optional agent identifier within a session"
    )


class ChatRequest(BaseModel):
    """Request body for querying memories."""

    question: str = Field(min_length=1, max_length=10_000, description="Question to ask")
    language: str | None = Field(
        default=None, description="Force response in specific language (e.g., 'en', 'fa')"
    )
    as_of: str | None = Field(
        default=None, description="ISO8601 timestamp for temporal queries"
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for scoped retrieval (includes session + global memories)",
    )


class MemoryUpdateRequest(BaseModel):
    """Request body for updating a memory."""

    kind: str | None = Field(default=None, description="New memory kind")
    summary: str | None = Field(default=None, description="New summary text")
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="New confidence score (0.0-1.0)"
    )


class FeedbackRequest(BaseModel):
    """Request body for submitting memory feedback."""

    feedback_type: FeedbackType = Field(
        description="Type of feedback: positive, negative, or neutral"
    )
    memory_ids: list[str] = Field(description="List of memory IDs to provide feedback on")
    conversation_id: str | None = Field(default=None, description="Optional conversation ID")
    session_id: str | None = Field(default=None, description="Optional session ID")


class MemoryToolRequest(BaseModel):
    """Request body for memory tool operations."""

    action: MemoryToolAction = Field(description="Action: remember, forget, or update")
    content: str = Field(description="Memory content")
    key: str | None = Field(default=None, description="Optional memory key")
    memory_type: str = Field(
        default="semantic", description="Memory type: episodic, semantic, procedural, core"
    )
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    entity_names: list[str] | None = Field(default=None, description="Optional entity names")
    reason: str | None = Field(default=None, description="Optional reason for action")
    session_id: str | None = Field(default=None, description="Optional session ID")
