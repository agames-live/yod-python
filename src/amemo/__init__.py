"""
Amemo Python SDK
================

Official Python client for the Amemo personal memory assistant API.

Quick Start (Sync):
    >>> from amemo import AmemoClient
    >>>
    >>> client = AmemoClient(bearer_token="your-token")
    >>>
    >>> # Ingest some data
    >>> client.ingest_chat("My favorite color is blue")
    >>>
    >>> # Query memories
    >>> response = client.chat("What is my favorite color?")
    >>> print(response.answer)  # "Your favorite color is blue."

Quick Start (Async):
    >>> from amemo import AsyncAmemoClient
    >>>
    >>> async with AsyncAmemoClient(bearer_token="your-token") as client:
    ...     response = await client.chat("What is my favorite color?")
    ...     print(response.answer)

For more information, see https://docs.amemo.ai/sdk/python
"""

from amemo._version import __version__
from amemo.async_client import AsyncAmemoClient
from amemo.client import AmemoClient
from amemo.exceptions import (
    AmemoAPIError,
    AmemoConnectionError,
    AmemoError,
    AmemoTimeoutError,
    AuthenticationError,
    AuthorizationError,
    ConnectionError,  # Deprecated alias for AmemoConnectionError
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,  # Deprecated alias for AmemoTimeoutError
    ValidationError,
)
from amemo.models import (
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
    "AmemoClient",
    "AsyncAmemoClient",
    # Exceptions
    "AmemoError",
    "AmemoAPIError",
    "AmemoConnectionError",
    "AmemoTimeoutError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "ConnectionError",  # Deprecated alias
    "TimeoutError",  # Deprecated alias
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
