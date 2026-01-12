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

    # Subject entity - who this claim is about
    subject_entity_id: str | None = None
    """Entity ID this claim is about. 'ent_self' for user's own claims, else another entity."""

    subject_entity_name: str | None = None
    """Display name for third-party claims (e.g., 'Sarah', 'Emma')."""

    # Cognitive memory architecture fields
    memory_type: str | None = None
    """Memory type: episodic, semantic, procedural, or core. See MemoryType enum."""

    access_count: int = 0
    """Number of times this memory has been accessed. Used for procedural strengthening."""


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

    # Subject entity - who this claim is about
    subject_entity_id: str | None = None
    """Entity ID this claim is about. 'ent_self' for user's own claims, else another entity."""

    # Cognitive memory architecture fields
    key: str | None = None
    """Stable predicate key in snake_case, e.g. 'pref_favorite_color'."""

    memory_type: str | None = None
    """Memory type: episodic, semantic, procedural, or core. See MemoryType enum."""


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


class RedisStatus(BaseModel):
    """Status of Redis cache service."""

    status: str
    redis_version: str | None = None
    uptime_seconds: int | None = None


class ReadyResponse(BaseModel):
    """Response from readiness check endpoint."""

    status: str
    neo4j: ServiceStatus | None = None
    qdrant: ServiceStatus | None = None
    redis: RedisStatus | None = None


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


# --- Conversation Models ---


class Conversation(BaseModel):
    """A chat conversation."""

    conversation_id: str
    title: str
    message_count: int = 0
    created_at: str
    updated_at: str


class Message(BaseModel):
    """A chat message within a conversation."""

    message_id: str
    role: str
    content: str
    citations: list[dict] = Field(default_factory=list)
    created_at: str


class MessageInput(BaseModel):
    """Input for creating or syncing a message."""

    id: str | None = None
    role: str
    content: str
    citations: list[dict] | None = None
    timestamp: str | None = None


# --- Speech Models ---


class STTResponse(BaseModel):
    """Response from speech-to-text endpoint."""

    text: str
    language: str | None = None


# --- Consolidation Models ---


class ConsolidationStatusResponse(BaseModel):
    """Response for consolidation status endpoint."""

    enabled: bool
    """Whether memory consolidation is enabled on the server."""

    schedule: str
    """Cron schedule for automatic consolidation (e.g., '0 3 * * *' for 3 AM daily)."""

    stats: dict
    """Memory statistics including total, by_status, and by_type breakdowns."""

    last_consolidation: dict | None = None
    """Details of the most recent consolidation run, if any."""


class ConsolidationTriggerResponse(BaseModel):
    """Response for manual consolidation trigger."""

    started: bool
    """Whether the consolidation job was started."""

    message: str
    """Human-readable status message."""

    job_id: str | None = None
    """Job ID for tracking the background consolidation. Use get_consolidation_result()."""


class ConsolidationResultResponse(BaseModel):
    """Response with consolidation cycle results."""

    user_id: str
    """User ID for whom consolidation was run."""

    started_at: str
    """ISO8601 timestamp when consolidation started."""

    completed_at: str | None = None
    """ISO8601 timestamp when consolidation completed, or None if still running."""

    clusters_found: int = 0
    """Number of episodic memory clusters discovered."""

    clusters_abstracted: int = 0
    """Number of clusters converted to semantic memories."""

    claims_consolidated: int = 0
    """Number of episodic claims marked as consolidated."""

    claims_archived: int = 0
    """Number of decayed memories archived (pruned)."""

    claims_boosted: int = 0
    """Number of frequently-accessed procedural memories identified."""

    links_discovered: int = 0
    """Number of new RELATES_TO links created between memories."""

    contradictions_found: int = 0
    """Number of contradictions detected among memories."""

    errors: list[str] = Field(default_factory=list)
    """List of error messages if any issues occurred during consolidation."""


# --- Evolution/Drift Models ---


class DriftScore(BaseModel):
    """Drift score for a time period."""

    period: str
    """Time period label (e.g., '1m', '3m', '6m', '1y')."""

    similarity: float
    """Cosine similarity between consecutive periods (0.0-1.0)."""

    drift_detected: bool
    """Whether drift was detected in this period."""


class EvolutionPoint(BaseModel):
    """A point in the memory evolution timeline."""

    period: str
    """Time period label."""

    claim_count: int
    """Number of claims in this period."""

    representative_value: str | None = None
    """Representative value for this period."""

    embedding_centroid: list[float] | None = None
    """Embedding centroid for this period (optional)."""


class EvolutionResponse(BaseModel):
    """Response for memory evolution/drift tracking."""

    key: str
    """Memory key being tracked."""

    total_claims: int
    """Total number of claims for this key."""

    timeline: list[EvolutionPoint] = Field(default_factory=list)
    """Evolution timeline with points per period."""

    drift_scores: list[DriftScore] = Field(default_factory=list)
    """Drift scores between consecutive periods."""

    drift_pattern: str | None = None
    """Detected drift pattern: 'gradual', 'sudden', or 'incremental'."""

    interpretation: str | None = None
    """LLM-generated interpretation of the evolution."""


class EvolutionKeysResponse(BaseModel):
    """Response listing memory keys with drift potential."""

    keys: list[str]
    """List of memory keys with multiple claims over time."""

    count: int
    """Number of keys returned."""

    min_claims_threshold: int
    """Minimum claims required for drift analysis."""


# --- Entity Models ---


class EntityLink(BaseModel):
    """Co-occurrence link between entities."""

    source: str
    """Source entity ID."""

    target: str
    """Target entity ID."""

    weight: int
    """Co-occurrence weight."""


class EntitySummary(BaseModel):
    """Summary of an entity."""

    entity_id: str
    """Entity ID."""

    type: str
    """Entity type (person, organization, etc.)."""

    canonical_name: str
    """Canonical name."""

    claim_count: int
    """Number of claims about this entity."""


class EntitiesResponse(BaseModel):
    """Response for entity list with co-occurrence links."""

    entities: list[EntitySummary]
    """List of entities."""

    links: list[EntityLink]
    """Co-occurrence links between entities."""


class EntityDetailsResponse(BaseModel):
    """Detailed entity information."""

    entity_id: str
    """Entity ID."""

    type: str
    """Entity type."""

    canonical_name: str
    """Canonical name."""

    aliases: list[str] = Field(default_factory=list)
    """Known aliases."""

    connection_count: int
    """Number of connections to other entities."""

    claim_count: int
    """Number of claims about this entity."""

    related_entities: list[EntitySummary] = Field(default_factory=list)
    """Related entities."""

    claims: list[MemoryItem] = Field(default_factory=list)
    """Claims about this entity."""


# --- Graph Models ---


class GraphNode(BaseModel):
    """Node in the claims graph."""

    id: str
    """Node ID (claim_id)."""

    label: str
    """Display label."""

    type: str
    """Node type."""

    confidence: float | None = None
    """Confidence score."""


class GraphLink(BaseModel):
    """Link in the claims graph."""

    source: str
    """Source node ID."""

    target: str
    """Target node ID."""

    type: str
    """Link type (RELATES_TO relationship type)."""

    confidence: float | None = None
    """Link confidence."""


class ClaimsGraphResponse(BaseModel):
    """Response for claims graph visualization."""

    nodes: list[GraphNode]
    """Graph nodes (claims)."""

    links: list[GraphLink]
    """Graph links (RELATES_TO edges)."""


# --- Contradiction Models ---


class ContradictionPair(BaseModel):
    """A pair of contradicting memories."""

    claim_a: MemoryItem
    """First conflicting claim."""

    claim_b: MemoryItem
    """Second conflicting claim."""

    session_a: str | None = None
    """Session ID of first claim."""

    session_b: str | None = None
    """Session ID of second claim."""


class ContradictionsResponse(BaseModel):
    """Response for cross-session contradictions summary."""

    total_conflicts: int
    """Total number of conflicts detected."""

    samples: list[ContradictionPair] = Field(default_factory=list)
    """Sample contradiction pairs."""

    session_count: int
    """Number of sessions with conflicts."""


class SessionContradictionsResponse(BaseModel):
    """Response for session-specific contradictions."""

    contradictions: list[ContradictionPair]
    """Contradiction pairs for this session."""

    count: int
    """Number of contradictions."""

    session_id: str
    """Session ID."""


# --- Audit Models ---


class AuditSummaryResponse(BaseModel):
    """Summary of memory audit activity."""

    total: int
    """Total audit events."""

    by_action: dict[str, int]
    """Breakdown by action type."""

    period_days: int
    """Period in days."""


class AuditEvent(BaseModel):
    """A single audit event."""

    event_id: str
    """Audit event ID."""

    action: str
    """Action type (create, update, delete, etc.)."""

    memory_id: str
    """Affected memory ID."""

    timestamp: str
    """ISO8601 timestamp."""

    details: dict = Field(default_factory=dict)
    """Additional details."""


class RecentAuditResponse(BaseModel):
    """Response for recent audit events."""

    modifications: list[AuditEvent]
    """Recent modification events."""

    count: int
    """Number of events returned."""


class SuspiciousPattern(BaseModel):
    """A detected suspicious activity pattern."""

    pattern_type: str
    """Type of suspicious pattern."""

    description: str
    """Human-readable description."""

    count: int
    """Number of occurrences."""

    memory_ids: list[str] = Field(default_factory=list)
    """Affected memory IDs."""


class SuspiciousActivityResponse(BaseModel):
    """Response for suspicious activity detection."""

    patterns: list[SuspiciousPattern]
    """Detected suspicious patterns."""

    count: int
    """Number of patterns found."""

    analyzed_hours: int
    """Hours analyzed."""

    has_suspicious_activity: bool
    """Whether suspicious activity was detected."""


class MemoryAuditTrailResponse(BaseModel):
    """Audit trail for a specific memory."""

    audit_trail: list[AuditEvent]
    """Audit events for this memory."""

    count: int
    """Number of events."""

    memory_id: str
    """Memory ID."""


# --- Proposed Memory Models ---


class ProposedMemoriesResponse(BaseModel):
    """Response for proposed memories awaiting review."""

    items: list[MemoryItem]
    """List of proposed memories."""

    count: int
    """Number of proposed memories."""


class ApproveMemoryResponse(BaseModel):
    """Response for approving a proposed memory."""

    ok: bool
    """Whether approval succeeded."""

    memory_id: str
    """Approved memory ID."""

    key: str
    """Memory key."""

    value: str
    """Memory value."""

    superseded_claim_id: str | None = None
    """ID of claim that was superseded, if any."""


class RejectMemoryResponse(BaseModel):
    """Response for rejecting a proposed memory."""

    ok: bool
    """Whether rejection succeeded."""

    memory_id: str
    """Rejected memory ID."""


# --- Chat Tool Models ---


class FeedbackResponse(BaseModel):
    """Response for memory feedback submission."""

    feedback_id: str
    """Feedback ID."""

    message: str
    """Confirmation message."""


class MemoryToolResponse(BaseModel):
    """Response for memory tool operations."""

    success: bool
    """Whether operation succeeded."""

    action: str
    """Action performed (remember, forget, update)."""

    message: str
    """Status message."""

    claim_id: str | None = None
    """Affected claim ID, if any."""

    error: str | None = None
    """Error message, if any."""


class ToolParameter(BaseModel):
    """A parameter definition for a memory tool."""

    name: str
    """Parameter name."""

    type: str
    """Parameter type."""

    description: str
    """Parameter description."""

    required: bool = False
    """Whether parameter is required."""

    enum: list[str] | None = None
    """Allowed values, if restricted."""


class ToolDefinition(BaseModel):
    """Definition of a memory tool for LLM function calling."""

    name: str
    """Tool name."""

    description: str
    """Tool description."""

    parameters: list[ToolParameter]
    """Tool parameters."""


class MemoryToolsSchemaResponse(BaseModel):
    """Response for memory tools schema."""

    tools: list[ToolDefinition]
    """Available tool definitions."""

    enabled: bool
    """Whether memory tools are enabled."""
