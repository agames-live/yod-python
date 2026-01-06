# Yod Python SDK Documentation

Official Python SDK for the Yod personal memory API.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Client Configuration](#client-configuration)
- [API Reference](#api-reference)
  - [Ingestion](#ingestion)
  - [Chat/Query](#chatquery)
  - [Memory Management](#memory-management)
  - [Health Checks](#health-checks)
- [Response Models](#response-models)
- [Error Handling](#error-handling)
- [Async Client](#async-client)
- [Best Practices](#best-practices)

---

## Installation

```bash
pip install yod
```

**Requirements:** Python 3.9+

---

## Quick Start

```python
from yod import YodClient

# Initialize client
client = YodClient(api_key="sk-yod-your-api-key")

# Ingest information
client.ingest_chat("My favorite color is blue and I'm allergic to shellfish")

# Query memories
response = client.chat("What is my favorite color?")
print(response.answer)  # "Your favorite color is blue."

# Clean up
client.close()
```

### Using Context Manager (Recommended)

```python
from yod import YodClient

with YodClient(api_key="sk-yod-your-api-key") as client:
    response = client.chat("What are my dietary restrictions?")
    print(response.answer)
# Connection automatically closed
```

---

## Authentication

The SDK supports three authentication methods:

### 1. API Key (Recommended for Production)

```python
client = YodClient(api_key="sk-yod-your-api-key")
```

### 2. JWT Bearer Token

```python
client = YodClient(bearer_token="eyJhbGciOiJIUzI1NiIs...")
```

### 3. User ID Header (Development Only)

For local development when the server has `ALLOW_INSECURE_USER_HEADER=true`:

```python
client = YodClient(
    base_url="http://localhost:8000",
    user_id="dev-user-123"
)
```

> **Note:** If both `api_key` and `bearer_token` are provided, `api_key` takes priority.

---

## Client Configuration

```python
client = YodClient(
    api_key="sk-yod-your-api-key",
    base_url="https://api.yod.agames.ai",  # API endpoint (default)
    timeout=30.0,                      # Request timeout in seconds (default: 30)
    connect_timeout=10.0,              # Connection timeout in seconds (default: 10)
    max_retries=3,                     # Retry attempts for transient errors (default: 3)
)
```

### Retry Behavior

The client automatically retries on:
- `429` Rate Limit (respects `Retry-After` header)
- `500` Internal Server Error
- `502` Bad Gateway
- `503` Service Unavailable
- `504` Gateway Timeout

Retries use exponential backoff with jitter.

---

## API Reference

### Ingestion

#### `ingest_chat(text, source_id=None, timestamp=None)`

Ingest text data and extract memories.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `text` | `str` | Yes | Text to ingest (1-50,000 characters) |
| `source_id` | `str` | No | Custom identifier for the source |
| `timestamp` | `str` | No | ISO 8601 timestamp for the content |

**Returns:** `IngestResponse`

**Example:**

```python
result = client.ingest_chat(
    text="I have a meeting with Sarah tomorrow at 3pm",
    source_id="calendar-sync",
    timestamp="2024-01-15T10:00:00Z"
)

print(f"Source: {result.source_id}")
print(f"Chunks processed: {result.chunks}")
print(f"Entities found: {len(result.entities)}")
print(f"Memories extracted: {len(result.memories)}")

for memory in result.memories:
    print(f"  - [{memory.kind}] {memory.summary}")
```

---

### Chat/Query

#### `chat(question, language=None, as_of=None)`

Query memories with natural language.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `question` | `str` | Yes | Natural language question |
| `language` | `str` | No | Response language code (e.g., "en", "fa") |
| `as_of` | `str` | No | ISO 8601 timestamp for point-in-time query |

**Returns:** `ChatResponse`

**Example:**

```python
# Basic query
response = client.chat("What is my favorite color?")
print(response.answer)

# Query with language preference
response = client.chat("What are my hobbies?", language="fa")

# Point-in-time query (what did I know last month?)
response = client.chat(
    "What meetings did I have?",
    as_of="2024-01-01T00:00:00Z"
)

# Access citations
for citation in response.citations:
    print(f"Source: {citation.source_id}")
    if citation.quote:
        print(f"Quote: {citation.quote}")

# Access memory IDs used
print(f"Used memories: {response.used_memory_ids}")
```

---

### Memory Management

#### `list_memories(kind=None, search=None, entity_id=None, limit=None, offset=None, include_inactive=None)`

List memories with optional filters.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `kind` | `str` | No | Filter by memory type |
| `search` | `str` | No | Full-text search term |
| `entity_id` | `str` | No | Filter by entity ID |
| `limit` | `int` | No | Maximum results (default: 50) |
| `offset` | `int` | No | Pagination offset |
| `include_inactive` | `bool` | No | Include superseded memories |

**Returns:** `MemoryListResponse`

**Example:**

```python
# List all memories
memories = client.list_memories()
for mem in memories.items:
    print(f"[{mem.kind}] {mem.summary} (confidence: {mem.confidence})")

# Filter by type
preferences = client.list_memories(kind="preference")

# Search
results = client.list_memories(search="coffee", limit=10)

# Include historical versions
all_memories = client.list_memories(include_inactive=True)
```

---

#### `get_memory(memory_id)`

Get a specific memory by ID.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `memory_id` | `str` | Yes | Memory ID |

**Returns:** `MemoryItem`

**Example:**

```python
memory = client.get_memory("mem_abc123")

print(f"ID: {memory.memory_id}")
print(f"Kind: {memory.kind}")
print(f"Summary: {memory.summary}")
print(f"Confidence: {memory.confidence}")
print(f"Status: {memory.status}")
print(f"Updated: {memory.updated_at}")

# Access supporting evidence
for support in memory.support:
    print(f"Source: {support.source_id}")
    for quote in support.quotes:
        print(f"  Quote: {quote}")
```

---

#### `update_memory(memory_id, confidence=None, kind=None, summary=None, status=None)`

Update a memory's properties.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `memory_id` | `str` | Yes | Memory ID |
| `confidence` | `float` | No | New confidence (0.0-1.0) |
| `kind` | `str` | No | New memory type |
| `summary` | `str` | No | New summary text |
| `status` | `str` | No | New status ("active" or "inactive") |

**Returns:** `MemoryItem`

**Example:**

```python
# Update confidence
updated = client.update_memory("mem_abc123", confidence=0.95)

# Mark as inactive (soft delete)
client.update_memory("mem_abc123", status="inactive")

# Update summary
client.update_memory("mem_abc123", summary="User prefers dark roast coffee")
```

---

#### `delete_memory(memory_id)`

Permanently delete a memory.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `memory_id` | `str` | Yes | Memory ID |

**Returns:** `dict` with `ok` and `qdrant_deleted` count

**Example:**

```python
result = client.delete_memory("mem_abc123")
if result["ok"]:
    print(f"Deleted {result['qdrant_deleted']} vector embeddings")
```

---

#### `get_memory_history(memory_id)`

Get temporal versions of a memory (how it changed over time).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `memory_id` | `str` | Yes | Memory ID |

**Returns:** `MemoryListResponse`

**Example:**

```python
history = client.get_memory_history("mem_abc123")

for version in history.items:
    print(f"[{version.valid_from}] {version.summary}")
    print(f"  Confidence: {version.confidence}")
    print(f"  Valid until: {version.valid_to or 'current'}")
```

---

### Health Checks

#### `health()`

Basic health check.

**Returns:** `HealthResponse`

```python
health = client.health()
print(f"Status: {health.status}")  # "ok"
```

#### `ready()`

Detailed readiness check with backend service status.

**Returns:** `ReadyResponse`

```python
ready = client.ready()
print(f"Status: {ready.status}")

if ready.neo4j:
    print(f"Neo4j: {'OK' if ready.neo4j.ok else ready.neo4j.error}")

if ready.qdrant:
    print(f"Qdrant: {'OK' if ready.qdrant.ok else ready.qdrant.error}")
```

---

## Response Models

All responses are typed Pydantic models with full IDE autocomplete support.

### ChatResponse

```python
class ChatResponse:
    answer: str                    # The answer text
    citations: list[Citation]      # Source citations
    used_memory_ids: list[str]     # IDs of memories used
```

### MemoryItem

```python
class MemoryItem:
    memory_id: str                 # Unique identifier
    kind: str                      # Memory type
    summary: str                   # Human-readable summary
    confidence: float              # Confidence score (0.0-1.0)
    updated_at: str | None         # Last update timestamp
    entity_ids: list[str]          # Related entity IDs
    support: list[MemorySupport]   # Supporting evidence
    status: str | None             # "active" or "inactive"
    key: str | None                # Deduplication key
    valid_from: str | None         # Temporal validity start
    valid_to: str | None           # Temporal validity end
```

### IngestResponse

```python
class IngestResponse:
    source_id: str                      # Source identifier
    chunks: int                         # Number of chunks processed
    entities: list[ExtractedEntity]     # Extracted entities
    memories: list[ExtractedMemory]     # Extracted memories
```

### Memory Kinds

| Kind | Description | Example |
|------|-------------|---------|
| `preference` | User preferences | "Favorite color is blue" |
| `event` | Events/appointments | "Meeting with Sarah at 3pm" |
| `profile_fact` | Profile information | "Works as a software engineer" |
| `task` | Tasks and to-dos | "Need to buy groceries" |
| `relationship` | People relationships | "Sarah is my manager" |
| `fact` | General facts | "The office is in downtown" |

---

## Error Handling

```python
from yod import (
    YodClient,
    YodError,           # Base exception
    YodAPIError,        # API errors (has status_code)
    AuthenticationError,  # 401 - Invalid credentials
    AuthorizationError,   # 403 - Permission denied
    NotFoundError,        # 404 - Resource not found
    ValidationError,      # 422 - Invalid request
    RateLimitError,       # 429 - Rate limited
    ServerError,          # 5xx - Server error
    YodConnectionError, # Network error
    YodTimeoutError,    # Request timeout
)

client = YodClient(api_key="sk-yod-your-api-key")

try:
    response = client.chat("What do I like?")
except AuthenticationError as e:
    print(f"Invalid credentials: {e}")
    print(f"Request ID: {e.request_id}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except NotFoundError:
    print("Memory not found")
except ValidationError as e:
    print(f"Invalid request: {e.response_body}")
except ServerError as e:
    print(f"Server error ({e.status_code}): {e}")
except YodConnectionError:
    print("Network connection failed")
except YodTimeoutError:
    print("Request timed out")
except YodError as e:
    print(f"Unexpected error: {e}")
```

### Exception Hierarchy

```
YodError (base)
├── YodAPIError (API returned error)
│   ├── AuthenticationError (401)
│   ├── AuthorizationError (403)
│   ├── NotFoundError (404)
│   ├── ValidationError (422)
│   ├── RateLimitError (429)
│   └── ServerError (5xx)
├── YodConnectionError (network error)
└── YodTimeoutError (timeout)
```

---

## Async Client

For async/await applications, use `AsyncYodClient`:

```python
import asyncio
from yod import AsyncYodClient

async def main():
    async with AsyncYodClient(api_key="sk-yod-your-api-key") as client:
        # All methods are async
        response = await client.chat("What is my favorite color?")
        print(response.answer)

        # Parallel requests
        responses = await asyncio.gather(
            client.chat("What is my name?"),
            client.chat("What are my hobbies?"),
            client.list_memories(kind="preference"),
        )

        for r in responses[:2]:
            print(r.answer)

        print(f"Found {len(responses[2].items)} preferences")

asyncio.run(main())
```

### Async Methods

All sync methods have async equivalents:

| Sync | Async |
|------|-------|
| `client.chat()` | `await client.chat()` |
| `client.ingest_chat()` | `await client.ingest_chat()` |
| `client.list_memories()` | `await client.list_memories()` |
| `client.get_memory()` | `await client.get_memory()` |
| `client.update_memory()` | `await client.update_memory()` |
| `client.delete_memory()` | `await client.delete_memory()` |
| `client.get_memory_history()` | `await client.get_memory_history()` |
| `client.health()` | `await client.health()` |
| `client.ready()` | `await client.ready()` |

---

## Best Practices

### 1. Use Context Managers

```python
# Good - automatically closes connection
with YodClient(api_key="...") as client:
    client.chat("question")

# Also good for async
async with AsyncYodClient(api_key="...") as client:
    await client.chat("question")
```

### 2. Handle Rate Limits

```python
import time

def chat_with_backoff(client, question, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return client.chat(question)
        except RateLimitError as e:
            if attempt == max_attempts - 1:
                raise
            wait = e.retry_after or (2 ** attempt)
            time.sleep(wait)
```

### 3. Batch Operations for Efficiency

```python
# Async parallel ingestion
async def ingest_many(client, texts):
    tasks = [client.ingest_chat(text) for text in texts]
    return await asyncio.gather(*tasks)
```

### 4. Use Point-in-Time Queries for Historical Data

```python
# What did the user know last week?
response = client.chat(
    "What meetings do I have?",
    as_of="2024-01-08T00:00:00Z"
)
```

### 5. Check Service Health Before Critical Operations

```python
ready = client.ready()
if ready.status != "ok":
    if ready.neo4j and not ready.neo4j.ok:
        print(f"Neo4j issue: {ready.neo4j.error}")
    if ready.qdrant and not ready.qdrant.ok:
        print(f"Qdrant issue: {ready.qdrant.error}")
```

---

## Development

```bash
# Clone and install
git clone https://github.com/yod/yod-python.git
cd yod-python
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/yod

# Linting
ruff check src/yod
```

---

## Support

- [API Documentation](https://docs.yod.agames.ai/api)
- [GitHub Issues](https://github.com/yod/yod-python/issues)
- Email: support@yod.agames.ai
