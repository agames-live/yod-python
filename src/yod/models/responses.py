"""Response models for the Yod SDK."""

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


class MemoryLink(BaseModel):
    """
    Semantic link between memories discovered by A-MEM algorithm.

    When MEMORY_LINKING_ENABLED=true on the server, the system discovers
    relationships between claims using the A-MEM two-step process:
    1. Candidate retrieval (keyword/entity matching)
    2. LLM relationship classification
    """

    target: str
    """The memory_id of the linked memory."""

    type: str
    """Relationship type: supports, contradicts, refines, elaborates, supersedes."""

    confidence: float
    """Confidence score (0.0-1.0) from LLM classification."""

    reason: str | None = None
    """Optional explanation for the relationship."""


class Contradiction(BaseModel):
    """
    Detected contradiction between user's memories.

    Surfaced during chat queries when MEMORY_LINKING_ENABLED=true and
    conflicting claims are found in the retrieved memories.
    """

    claim_a: str
    """Summary of first conflicting claim."""

    claim_b: str
    """Summary of second conflicting claim."""

    reason: str | None = None
    """Explanation of why the claims conflict."""


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
    links: list[MemoryLink] = Field(default_factory=list)
    """Semantic links to other memories (A-MEM). Empty if linking disabled."""


class MemoryListResponse(BaseModel):
    """Response containing a list of memories."""

    items: list[MemoryItem] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response from a chat/query request."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    used_memory_ids: list[str] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    """Detected contradictions in retrieved memories (A-MEM). Empty if none found."""
    tokens_input: int = 0
    """Number of input tokens used."""
    tokens_output: int = 0
    """Number of output tokens generated."""
    search_latency_ms: float = 0.0
    """Time for retrieval phase (embedding + vector + graph search) in milliseconds."""
    total_latency_ms: float = 0.0
    """Total end-to-end latency in milliseconds."""


class ExtractedEntity(BaseModel):
    """An entity extracted during ingestion."""

    entity_id: str
    type: str
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)


class MergeInfo(BaseModel):
    """Information about a merged memory when decision is MERGE."""

    existing_value: str
    """The original value before merge."""
    new_value: str
    """The incoming value that triggered the merge."""
    merged_value: str
    """The resulting merged value."""


class ExtractedMemory(BaseModel):
    """A memory extracted during ingestion."""

    memory_id: str
    kind: str
    summary: str
    entity_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.6
    evidence_quotes: list[str] = Field(default_factory=list)
    links: list[MemoryLink] = Field(default_factory=list)
    """Discovered links to existing memories (A-MEM). Empty if linking disabled."""
    decision: str | None = None
    """Memory decision: ADD, UPDATE, KEEP, MERGE, or DELETE."""
    merge_info: MergeInfo | None = None
    """Merge details when decision is MERGE."""


class IngestResponse(BaseModel):
    """Response from ingesting chat/text data."""

    source_id: str
    chunks: int = 0
    entities: list[ExtractedEntity] = Field(default_factory=list)
    memories: list[ExtractedMemory] = Field(default_factory=list)
    embedding_failed: bool | None = None
    """True if embedding generation failed (memories still extracted)."""


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


class Session(BaseModel):
    """A memory session for scoping memories to specific contexts."""

    session_id: str
    user_id: str
    agent_id: str | None = None
    created_at: str
    metadata: dict = Field(default_factory=dict)
    claim_count: int = 0


class SessionListResponse(BaseModel):
    """Response containing a list of sessions."""

    sessions: list[Session] = Field(default_factory=list)
    total: int = 0


# --- API Key Models ---


class KeyUsageStats(BaseModel):
    """Usage stats for a single API key."""

    calls: int = 0
    tokens_input: int = 0
    tokens_output: int = 0


class APIKeyItem(BaseModel):
    """An API key (without the secret)."""

    key_id: str
    name: str
    scopes: list[str] = Field(default_factory=list)
    created_at: str
    last_used_at: str | None = None
    expires_at: str | None = None
    revoked: bool = False
    usage: KeyUsageStats = Field(default_factory=KeyUsageStats)


class CreateKeyResponse(BaseModel):
    """Response containing the new API key."""

    key_id: str
    secret_key: str
    """Full API key - SAVE THIS, shown only once!"""
    name: str
    scopes: list[str] = Field(default_factory=list)
    created_at: str
    expires_at: str | None = None


class KeyListResponse(BaseModel):
    """Response containing list of API keys."""

    keys: list[APIKeyItem] = Field(default_factory=list)


class UsageSummary(BaseModel):
    """Usage summary for billing."""

    total_calls: int
    total_tokens_input: int
    total_tokens_output: int
    total_cost_usd: float
    period_start: str
    period_end: str


class EndpointUsage(BaseModel):
    """Usage breakdown by endpoint."""

    endpoint: str
    calls: int
    tokens_input: int
    tokens_output: int
    cost_usd: float


class UsageResponse(BaseModel):
    """Full usage response."""

    summary: UsageSummary
    by_endpoint: list[EndpointUsage] = Field(default_factory=list)


class QuotaLimit(BaseModel):
    """A single quota limit with usage."""

    used: int
    limit: int
    """Limit value. -1 means unlimited."""
    remaining: int
    """Remaining quota. -1 means unlimited."""


class QuotaResponse(BaseModel):
    """Full quota status response."""

    plan: str
    month: str
    chat: QuotaLimit
    ingest: QuotaLimit
    memories: QuotaLimit
    api_keys: QuotaLimit
