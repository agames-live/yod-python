"""Response models for the Amemo SDK."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A citation referencing a source."""

    source_id: str
    quote: str | None = None


class MemorySupport(BaseModel):
    """Evidence supporting a memory."""

    source_id: str
    quotes: list[str] = Field(default_factory=list)


class MemoryItem(BaseModel):
    """A single memory item."""

    memory_id: str
    kind: str
    summary: str
    confidence: float
    updated_at: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    support: list[MemorySupport] = Field(default_factory=list)
    status: str | None = None
    key: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None


class MemoryListResponse(BaseModel):
    """Response containing a list of memories."""

    items: list[MemoryItem] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response from a chat/query request."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    used_memory_ids: list[str] = Field(default_factory=list)


class ExtractedEntity(BaseModel):
    """An entity extracted during ingestion."""

    entity_id: str
    type: str
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)


class ExtractedMemory(BaseModel):
    """A memory extracted during ingestion."""

    memory_id: str
    kind: str
    summary: str
    entity_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.6
    evidence_quotes: list[str] = Field(default_factory=list)


class IngestResponse(BaseModel):
    """Response from ingesting chat/text data."""

    source_id: str
    chunks: int = 0
    entities: list[ExtractedEntity] = Field(default_factory=list)
    memories: list[ExtractedMemory] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response from health check endpoint."""

    status: str


class ServiceStatus(BaseModel):
    """Status of a backend service (Neo4j, Qdrant)."""

    ok: bool
    error: str | None = None


class ReadyResponse(BaseModel):
    """Response from readiness check endpoint."""

    status: str
    neo4j: ServiceStatus | None = None
    qdrant: ServiceStatus | None = None
