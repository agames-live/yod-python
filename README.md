# Yod Python SDK

[![Website](https://img.shields.io/badge/website-yod.agames.live-111827?style=flat-square&labelColor=0b1220&color=111827)](https://yod.agames.live)
[![PyPI](https://img.shields.io/pypi/v/yod?style=flat-square&labelColor=0b1220&color=111827)](https://pypi.org/project/yod/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache_2.0-111827?style=flat-square&labelColor=0b1220&color=111827)](LICENSE)

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
    session_id="sess_abc123",  # Optional: session scoping
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
    session_id="sess_abc123",  # Optional: session scoping
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

### Session Management

Sessions allow you to scope memories to specific contexts (e.g., per-agent or per-conversation):

```python
# Create a new session
session = client.create_session(
    agent_id="support-bot",  # Optional: associate with an agent
    metadata={"context": "customer-support"}  # Optional metadata
)
print(session.session_id)  # "sess_abc123"

# List all sessions
sessions = client.list_sessions()
for s in sessions.sessions:
    print(f"{s.session_id}: agent={s.agent_id}, created={s.created_at}")

# Use session_id in ingest and chat
client.ingest_chat(
    "User prefers formal language",
    session_id=session.session_id
)
response = client.chat(
    "What tone should I use?",
    session_id=session.session_id
)

# Update session metadata
client.update_session(
    session.session_id,
    metadata={"context": "updated-context", "priority": "high"}
)

# Delete a session (also deletes session-scoped memories by default)
client.delete_session(session.session_id)

# Delete session but convert memories to global (cascade=False)
client.delete_session(session.session_id, cascade=False)
```

### Memory Linking (A-MEM)

When `MEMORY_LINKING_ENABLED=true` on the server, the system automatically discovers semantic relationships between memories using the A-MEM algorithm.

**Accessing links in ingest responses:**

```python
response = client.ingest_chat("I love eating steak for dinner")

for memory in response.memories:
    print(f"Memory: {memory.summary}")
    for link in memory.links:
        print(f"  -> {link.type} {link.target} (confidence: {link.confidence})")
        # Example output:
        # -> contradicts clm_vegetarian (confidence: 1.0)
```

**Link types:**
- `supports` - First claim provides evidence for second
- `contradicts` - Claims cannot both be true simultaneously
- `refines` - First is more specific version of second
- `elaborates` - First adds detail/context to second
- `supersedes` - First replaces second (temporal update)

**Accessing contradictions in chat responses:**

```python
response = client.chat("What are my dietary preferences?")

print(response.answer)
# "Your memories show some conflicting information..."

for contradiction in response.contradictions:
    print(f"Conflict: {contradiction.claim_a} vs {contradiction.claim_b}")
    if contradiction.reason:
        print(f"  Reason: {contradiction.reason}")
```

### Memory Consolidation

Memory consolidation is a sleep-like background process that clusters episodic memories into semantic facts.

```python
# Get consolidation status
status = client.get_consolidation_status()
print(status.enabled)           # True if consolidation is enabled
print(status.schedule)          # Cron schedule (e.g., "0 3 * * *")
print(status.stats)             # Memory counts by type and status
print(status.last_consolidation)  # Details of last consolidation run

# Trigger background consolidation (non-blocking)
job = client.trigger_consolidation()
print(job.job_id)  # Use to check results later

# Get background job results
result = client.get_consolidation_result(job.job_id)
print(result.clusters_found)       # Episodic memory clusters identified
print(result.claims_consolidated)  # Memories merged into semantic facts
print(result.claims_archived)      # Decayed memories archived
print(result.claims_boosted)       # Procedural memories strengthened

# Run consolidation synchronously (blocking, for testing)
result = client.run_consolidation()
print(f"Consolidated {result.claims_consolidated} memories")
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
        # Create a session for this conversation
        session = await client.create_session(agent_id="reading-assistant")

        # Ingest with session scoping
        await client.ingest_chat(
            "I enjoy reading science fiction",
            session_id=session.session_id
        )

        # Query within session context
        response = await client.chat(
            "What kind of books do I like?",
            session_id=session.session_id
        )
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
    Contradiction,    # A-MEM: detected conflicts between memories
    IngestResponse,
    MemoryItem,
    MemoryLink,       # A-MEM: semantic link between memories
    MemoryListResponse,
    MemorySupport,
    HealthResponse,
    ReadyResponse,
)
```

### Enums

```python
from yod import MemoryKind, MemoryType, MemoryStatus, EntityType

# Memory kinds (what the memory is about)
MemoryKind.PREFERENCE   # User preferences
MemoryKind.FACT         # General facts
MemoryKind.EVENT        # Events and activities
MemoryKind.RELATIONSHIP # Relationships between entities
MemoryKind.GOAL         # Goals and aspirations
MemoryKind.OPINION      # Opinions and beliefs

# Memory types (cognitive classification, affects decay/ranking)
MemoryType.EPISODIC    # Decays over time (events, experiences)
MemoryType.SEMANTIC    # Stable facts (profile info, knowledge)
MemoryType.PROCEDURAL  # Strengthens with access (habits, skills)
MemoryType.CORE        # Maximum strength (identity-critical)
```

### Cognitive Memory Types

Memories are automatically classified into cognitive types that affect retrieval ranking:

| Type | Behavior | Example |
|------|----------|---------|
| `episodic` | Decays over time (half-life: 30 days) | "Had coffee with Sarah yesterday" |
| `semantic` | Stable, no decay | "Works at Google" |
| `procedural` | Strengthens with repeated access | "Prefers Python for coding" |
| `core` | Maximum strength, never superseded | "Name is Alex" |

Access the `memory_type` field on any `MemoryItem`:

```python
memory = client.get_memory("clm_abc123")
print(memory.memory_type)   # "semantic", "episodic", etc.
print(memory.access_count)  # Number of times retrieved (for procedural boost)
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

Apache 2.0 License
