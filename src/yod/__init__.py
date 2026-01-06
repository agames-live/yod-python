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
    YodAPIError,
    YodConnectionError,
    YodError,
    YodTimeoutError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from yod.models import (
    # Enums
    EntityType,
    MemoryKind,
    MemoryStatus,
    # Requests
    ChatRequest,
    IngestChatRequest,
    MemoryUpdateRequest,
    # Responses
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
    "MemoryItem",
    "MemorySupport",
    "MemoryListResponse",
    "ExtractedEntity",
    "ExtractedMemory",
    "IngestResponse",
    "HealthResponse",
    "ReadyResponse",
    "ServiceStatus",
]
