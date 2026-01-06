# Yod Python SDK

Official Python client for the Yod personal memory assistant API.

## Installation

```bash
pip install yod
```

## Quick Start

```python
from yod import YodClient

# Initialize with your API key (get one from the dashboard)
client = YodClient(api_key="sk-yod-...")

# Ingest information
client.ingest_chat("My favorite color is blue and I love hiking on weekends")

# Query your memories
response = client.chat("What are my hobbies?")
print(response.answer)
# Output: "You love hiking on weekends."

print(response.citations)
# Output: [Citation(source_id='...', quote='I love hiking on weekends')]
```

## Authentication

The SDK supports multiple authentication methods:

### API Key (Recommended)

```python
client = YodClient(api_key="sk-yod-...")
```

### JWT Bearer Token

```python
client = YodClient(bearer_token="eyJ...")
```

### Development Mode (X-User-Id header)

```python
client = YodClient(
    base_url="http://localhost:8000",
    user_id="test-user-123"
)
```

## API Reference

### Client Initialization

```python
from yod import YodClient, AsyncYodClient

# Sync client
client = YodClient(
    api_key="sk-yod-...",           # API key
    base_url="https://api.yod.agames.ai",  # API base URL (optional)
    timeout=30.0,                      # Request timeout in seconds
    max_retries=3,                     # Max retry attempts
)

# Async client
async_client = AsyncYodClient(api_key="sk-yod-...")
```

### Ingest Text

Store text and extract memories:

```python
response = client.ingest_chat(
    text="I started learning piano last month. My teacher is Sarah.",
    source_id="conversation-123",  # Optional: track the source
    timestamp="2024-01-15T10:30:00Z",  # Optional: set timestamp
)

print(response.source_id)  # Source identifier
print(response.chunks)     # Number of chunks processed
print(response.entities)   # Extracted entities (people, places, etc.)
print(response.memories)   # Extracted memories
```

### Chat / Query

Query your memories with natural language:

```python
response = client.chat(
    question="Who is my piano teacher?",
    language="en",  # Optional: response language
    as_of="2024-06-01T00:00:00Z",  # Optional: temporal query
)

print(response.answer)          # "Your piano teacher is Sarah."
print(response.citations)       # Source citations with quotes
print(response.used_memory_ids) # Memory IDs used to generate answer
```

### List Memories

```python
memories = client.list_memories(
    limit=50,              # Max memories to return
    kind="preference",     # Filter by type (preference, event, fact, etc.)
    search="piano",        # Search term
    include_inactive=False # Include superseded memories
)

for memory in memories.memories:
    print(f"[{memory.kind}] {memory.summary} (confidence: {memory.confidence})")
```

### Get Single Memory

```python
memory = client.get_memory("mem_abc123")
print(memory.summary)
print(memory.entity_ids)  # Related entities
print(memory.support)     # Supporting sources with quotes
```

### Update Memory

```python
client.update_memory(
    "mem_abc123",
    summary="Updated summary text",
    confidence=0.95,
    kind="fact"
)
```

### Delete Memory

```python
client.delete_memory("mem_abc123")
```

### Memory History

Get temporal versions of a memory:

```python
history = client.get_memory_history("mem_abc123")
for version in history.memories:
    print(f"{version.updated_at}: {version.summary}")
```

### Health Checks

```python
# Basic health check
health = client.health()
print(health.status)  # "ok"

# Detailed readiness check
ready = client.ready()
print(ready.status)      # "ok" or "degraded"
print(ready.neo4j.ok)    # Neo4j status
print(ready.qdrant.ok)   # Qdrant status
```

## Async Usage

All methods are available as async:

```python
from yod import AsyncYodClient

async def main():
    async with AsyncYodClient(api_key="sk-yod-...") as client:
        # Ingest
        await client.ingest_chat("I enjoy reading science fiction")

        # Query
        response = await client.chat("What kind of books do I like?")
        print(response.answer)

        # List memories
        memories = await client.list_memories()
        for m in memories.memories:
            print(m.summary)

import asyncio
asyncio.run(main())
```

## Error Handling

The SDK provides specific exception types:

```python
from yod import (
    YodError,           # Base exception
    YodAPIError,        # API returned an error
    AuthenticationError,  # 401 - Invalid credentials
    AuthorizationError,   # 403 - Insufficient permissions
    NotFoundError,        # 404 - Resource not found
    ValidationError,      # 422 - Invalid request
    RateLimitError,       # 429 - Rate limit exceeded
    ServerError,          # 5xx - Server error
    YodConnectionError, # Network error
    YodTimeoutError,    # Request timeout
)

try:
    response = client.chat("What's my name?")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except YodAPIError as e:
    print(f"API error {e.status_code}: {e}")
except YodError as e:
    print(f"SDK error: {e}")
```

## Models

### Response Models

```python
from yod import (
    ChatResponse,
    Citation,
    IngestResponse,
    MemoryItem,
    MemoryListResponse,
    MemorySupport,
    HealthResponse,
    ReadyResponse,
)
```

### Enums

```python
from yod import MemoryKind, MemoryStatus, EntityType

# Memory kinds
MemoryKind.PREFERENCE   # User preferences
MemoryKind.FACT         # General facts
MemoryKind.EVENT        # Events and activities
MemoryKind.RELATIONSHIP # Relationships between entities
MemoryKind.GOAL         # Goals and aspirations
MemoryKind.OPINION      # Opinions and beliefs
```

## Configuration

### Custom Base URL

```python
# Self-hosted instance
client = YodClient(
    api_key="sk-yod-...",
    base_url="https://yod.yourcompany.com"
)

# Local development
client = YodClient(
    base_url="http://localhost:8000",
    user_id="dev-user"
)
```

### Timeouts

```python
client = YodClient(
    api_key="sk-yod-...",
    timeout=60.0,        # Request timeout
    connect_timeout=10.0 # Connection timeout
)
```

### Retry Configuration

The SDK automatically retries failed requests with exponential backoff:

```python
client = YodClient(
    api_key="sk-yod-...",
    max_retries=5  # Default: 3
)
```

Retries are performed for:
- 429 Too Many Requests (respects Retry-After header)
- 500, 502, 503, 504 Server Errors
- Connection errors

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Type Checking

```bash
mypy src/yod
```

## License

MIT License
