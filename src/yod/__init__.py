"""
Yod Python SDK
==============

Official Python client for the Yod personal memory assistant API.

Quick Start (Sync):
    >>> from yod import YodClient
    >>>
    >>> client = YodClient(bearer_token="your-token")
    >>>
    >>> # Ingest some data
    >>> client.ingest_chat("My favorite color is blue")
    >>>
    >>> # Query memories
    >>> response = client.chat("What is my favorite color?")
    >>> print(response.answer)  # "Your favorite color is blue."

Quick Start (Async):
    >>> from yod import AsyncYodClient
    >>>
    >>> async with AsyncYodClient(bearer_token="your-token") as client:
    ...     response = await client.chat("What is my favorite color?")
    ...     print(response.answer)

For more information, see https://docs.yod.agames.ai/sdk/python
"""

from yod._version import __version__
from yod.async_client import AsyncYodClient
from yod.client import YodClient
from yod.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    YodAPIError,
    YodConnectionError,
    YodError,
    YodTimeoutError,
)
from yod.models import (
    # Responses - Proposed Memories
    ApproveMemoryResponse,
    # Responses - Audit
    AuditEvent,
    AuditSummaryResponse,
    # Requests
    ChatRequest,
    # Responses - Core
    ChatResponse,
    Citation,
    # Responses - Graph
    ClaimsGraphResponse,
    Contradiction,
    # Responses - Contradictions
    ContradictionPair,
    ContradictionsResponse,
    # Responses - Evolution/Drift
    DriftScore,
    # Responses - Entities
    EntitiesResponse,
    EntityDetailsResponse,
    EntityLink,
    EntitySummary,
    # Enums
    EntityType,
    EvolutionKeysResponse,
    EvolutionPoint,
    EvolutionResponse,
    ExtractedEntity,
    ExtractedMemory,
    FeedbackRequest,
    # Responses - Chat Tools
    FeedbackResponse,
    # Request Types
    FeedbackType,
    GraphLink,
    GraphNode,
    HealthResponse,
    IngestChatRequest,
    IngestResponse,
    MemoryAuditTrailResponse,
    MemoryItem,
    MemoryKind,
    MemoryLink,
    MemoryListResponse,
    MemoryStatus,
    MemorySupport,
    MemoryToolAction,
    MemoryToolRequest,
    MemoryToolResponse,
    MemoryToolsSchemaResponse,
    MemoryType,
    MemoryUpdateRequest,
    MergeInfo,
    ProposedMemoriesResponse,
    ReadyResponse,
    RecentAuditResponse,
    RejectMemoryResponse,
    ServiceStatus,
    Session,
    SessionContradictionsResponse,
    SessionListResponse,
    SuspiciousActivityResponse,
    SuspiciousPattern,
    ToolDefinition,
    ToolParameter,
)

__all__ = [
    # Version
    "__version__",
    # Clients
    "YodClient",
    "AsyncYodClient",
    # Exceptions
    "YodError",
    "YodAPIError",
    "YodConnectionError",
    "YodTimeoutError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    # Enums
    "EntityType",
    "MemoryKind",
    "MemoryStatus",
    "MemoryType",
    # Request Types
    "FeedbackType",
    "MemoryToolAction",
    # Request Models
    "IngestChatRequest",
    "ChatRequest",
    "MemoryUpdateRequest",
    "FeedbackRequest",
    "MemoryToolRequest",
    # Response Models - Core
    "ChatResponse",
    "Citation",
    "Contradiction",
    "MemoryItem",
    "MemoryLink",
    "MemorySupport",
    "MemoryListResponse",
    "ExtractedEntity",
    "ExtractedMemory",
    "IngestResponse",
    "HealthResponse",
    "MergeInfo",
    "ReadyResponse",
    "ServiceStatus",
    "Session",
    "SessionListResponse",
    # Response Models - Evolution/Drift
    "DriftScore",
    "EvolutionPoint",
    "EvolutionResponse",
    "EvolutionKeysResponse",
    # Response Models - Entities
    "EntityLink",
    "EntitySummary",
    "EntitiesResponse",
    "EntityDetailsResponse",
    # Response Models - Graph
    "GraphNode",
    "GraphLink",
    "ClaimsGraphResponse",
    # Response Models - Contradictions
    "ContradictionPair",
    "ContradictionsResponse",
    "SessionContradictionsResponse",
    # Response Models - Audit
    "AuditSummaryResponse",
    "AuditEvent",
    "RecentAuditResponse",
    "SuspiciousPattern",
    "SuspiciousActivityResponse",
    "MemoryAuditTrailResponse",
    # Response Models - Proposed Memories
    "ProposedMemoriesResponse",
    "ApproveMemoryResponse",
    "RejectMemoryResponse",
    # Response Models - Chat Tools
    "FeedbackResponse",
    "MemoryToolResponse",
    "ToolParameter",
    "ToolDefinition",
    "MemoryToolsSchemaResponse",
]
