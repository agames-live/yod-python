"""Models for the Amemo SDK."""

from amemo.models.enums import EntityType, MemoryKind, MemoryStatus
from amemo.models.requests import (
    ChatRequest,
    IngestChatRequest,
    MemoryUpdateRequest,
)
from amemo.models.responses import (
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
)

__all__ = [
    # Enums
    "EntityType",
    "MemoryKind",
    "MemoryStatus",
    # Requests
    "IngestChatRequest",
    "ChatRequest",
    "MemoryUpdateRequest",
    # Responses
    "Citation",
    "MemorySupport",
    "MemoryItem",
    "MemoryListResponse",
    "ChatResponse",
    "ExtractedEntity",
    "ExtractedMemory",
    "IngestResponse",
    "HealthResponse",
    "ReadyResponse",
    "ServiceStatus",
]
