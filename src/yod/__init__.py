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
    # Requests
    ChatRequest,
    # Responses
    ChatResponse,
    Citation,
    Contradiction,
    # Enums
    EntityType,
    ExtractedEntity,
    ExtractedMemory,
    HealthResponse,
    IngestChatRequest,
    IngestResponse,
    MemoryItem,
    MemoryKind,
    MemoryLink,
    MemoryListResponse,
    MemoryStatus,
    MemorySupport,
    MemoryUpdateRequest,
    MergeInfo,
    ReadyResponse,
    ServiceStatus,
    Session,
    SessionListResponse,
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
    # Request Models
    "IngestChatRequest",
    "ChatRequest",
    "MemoryUpdateRequest",
    # Response Models
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
]
