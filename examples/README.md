# Yod SDK Test Application

An interactive CLI application to test the full Yod SDK functionality. Tests memory ingestion, LLM-powered chat with memory retrieval, and complete memory CRUD operations.

## Prerequisites

1. **Python 3.9+**
2. **Yod SDK** (install from parent directory)
3. **Rich library** for terminal UI

## Installation

```bash
# From the sdk directory
cd sdk

# Install SDK in development mode
pip install -e .

# Install rich for the test app
pip install rich
```

## Usage

### Local Development (with backend running on localhost)

```bash
# Using X-User-Id header (dev mode - requires ALLOW_INSECURE_USER_HEADER=true on backend)
python examples/test_app.py --base-url http://localhost:8000 --user-id test-user
```

### Production (with API key)

```bash
python examples/test_app.py --api-key sk-yod-xxxx
```

### Using Environment Variables

```bash
export YOD_BASE_URL=http://localhost:8000
export YOD_USER_ID=test-user
# or
export YOD_API_KEY=sk-yod-xxxx

python examples/test_app.py
```

### Run Automated Tests

```bash
python examples/test_app.py --base-url http://localhost:8000 --user-id test-user --test
```

## Features

### Interactive Menu

```
╭──────┬────────────────────────────────╮
│ 1    │ Ingest Text (add to memory)    │
│ 2    │ Chat (query memories with LLM) │
│ 3    │ List Memories                  │
│ 4    │ Get Memory Details             │
│ 5    │ Update Memory                  │
│ 6    │ Delete Memory                  │
│ 7    │ View Memory History            │
│ 8    │ Health Check                   │
│ 9    │ Run Test Suite                 │
│ 0    │ Exit                           │
╰──────┴────────────────────────────────╯
```

### 1. Ingest Text
- Add personal facts, preferences, or conversations to memory
- View extracted entities (people, organizations, topics)
- See extracted memories with confidence scores

### 2. Chat with Memory
- Ask questions in natural language
- LLM retrieves relevant memories to answer
- View citations and source references
- Supports temporal queries (as_of parameter)
- Supports multiple languages

### 3-7. Memory Management
- **List**: Browse memories with filters (kind, search term, limit)
- **Get**: View detailed memory information including supporting evidence
- **Update**: Modify memory summary, kind, or confidence
- **Delete**: Remove memories with confirmation
- **History**: View temporal versions of a memory

### 8. Health Check
- Verify API connectivity
- Check backend services (Neo4j, Qdrant)

### 9. Automated Test Suite
Runs comprehensive tests:
- Health check
- Text ingestion
- Memory listing
- Chat queries with context verification
- Memory retrieval and updates
- History tracking

## Example Session

```
$ python examples/test_app.py --base-url http://localhost:8000 --user-id demo

╔════════════════════════════════════════╗
║       Yod Memory Test App              ║
║     Interactive SDK Testing Tool       ║
╚════════════════════════════════════════╝

Select option: 1

Ingest Text
Enter text to store in memory (facts, preferences, conversations)

Text to ingest: My name is Alice and I work at Acme Corp as a software engineer.
Source ID (optional):
Timestamp ISO8601 (optional):

✓ Text ingested successfully!
Source ID: 550e8400-e29b-41d4-a716-446655440000
Chunks created: 1

Extracted Entities:
┌──────────────┬───────────┬──────────────┐
│ ID           │ Name      │ Type         │
├──────────────┼───────────┼──────────────┤
│ ent_self     │ self      │ self         │
│ ent_12345... │ Acme Corp │ organization │
└──────────────┴───────────┴──────────────┘

Extracted Memories:
┌──────────────┬──────────────┬─────────────────────────────┬────────┐
│ ID           │ Kind         │ Summary                     │ Conf   │
├──────────────┼──────────────┼─────────────────────────────┼────────┤
│ mem_abc12... │ profile_fact │ Alice                       │ 0.95   │
│ mem_def34... │ profile_fact │ works at Acme Corp          │ 0.90   │
│ mem_ghi56... │ profile_fact │ software engineer           │ 0.88   │
└──────────────┴──────────────┴─────────────────────────────┴────────┘

Select option: 2

Chat with Memory
Ask a question - the LLM will use your memories to answer

Your question: Where do I work?

╭─────────────────────── Answer ───────────────────────╮
│ Based on your memories, you work at Acme Corp as a   │
│ software engineer.                                   │
╰──────────────────────────────────────────────────────╯

Citations:
  [1] Source: 550e8400-e2...
      Quote: "I work at Acme Corp as a software engineer"
```

## Authentication Options

| Option | Flag | Environment Variable | Description |
|--------|------|---------------------|-------------|
| API Key | `--api-key` | `YOD_API_KEY` | Production API key (sk-yod-*) |
| Bearer Token | `--token` | `YOD_TOKEN` | JWT bearer token |
| User ID | `--user-id` | `YOD_USER_ID` | Dev mode only (requires backend config) |
| Base URL | `--base-url` | `YOD_BASE_URL` | API endpoint (default: http://localhost:8000) |

## Troubleshooting

### Connection Error
```
✗ Connection error: Failed to connect to http://localhost:8000
Is the server running?
```
**Solution**: Start the backend with `docker-compose up` or `uvicorn app.main:app`

### Authentication Error
```
✗ Authentication failed: 401
Check your API key or token
```
**Solution**: Verify your API key or enable dev mode (`ALLOW_INSECURE_USER_HEADER=true`)

### Not Found Error
```
✗ Not found: Memory mem_xxx not found
```
**Solution**: The memory ID doesn't exist. Use "List Memories" to find valid IDs.
