# Changelog

All notable changes to the Yod Python SDK will be documented in this file.

## [Unreleased]

## [0.2.1] - 2026-01-08

### Added

- `session_id` and `agent_id` parameters for `ingest_chat()` method
- `session_id` parameter for `chat()` method
- Full session scoping support for memory isolation across different contexts

### Documentation

- Updated docstrings with session scoping parameter descriptions

## [0.2.0] - 2026-01-08

### Changed

- Version bump to align with backend session scoping security fixes

## [0.1.9] - 2026-01-08

### Fixed

- Backend session scoping bug fixes (SDK version sync)

## [0.1.8] - 2025-01-08

### Fixed

- Fixed Homepage URL to correct domain (yod.agames.live)
- Removed non-existent Documentation URL from PyPI metadata

## [0.1.7] - 2025-01-08

### Changed

- Updated repository URLs to public repo (agames-live/yod-python)
- Added Website, PyPI, and License badges to README

### Removed

- Removed internal bug tracking file

## [0.1.5] - 2025-01-08

### Added

- **Session Management** - Full support for memory isolation across agents/contexts
  - `create_session(agent_id, metadata)` - Create a new session
  - `list_sessions()` - List all sessions for the current user
  - `delete_session(session_id)` - Delete a session and its associated memories
  - `session_id` parameter on `ingest_chat()` for session-scoped ingestion
  - `session_id` parameter on `chat()` for session-scoped queries
  - `session_id` parameter on `list_memories()` for filtering memories by session

- **LLM-Based Memory Decisions** - Intelligent conflict resolution when new claims conflict with existing ones
  - Supports decision types: ADD, UPDATE, DELETE, KEEP, MERGE
  - Configurable via `MEMORY_DECISION_ENABLED` and `MEMORY_DECISION_THRESHOLD`

### Documentation

- Added session management examples to README
- Updated API reference with session parameters

## [0.1.3] - 2025-01-06

### Added

- Initial public release
- Sync (`YodClient`) and async (`AsyncYodClient`) clients
- Memory CRUD operations (`list_memories`, `get_memory`, `update_memory`, `delete_memory`)
- Chat and ingestion endpoints (`chat`, `ingest_chat`)
- Health check endpoints
- Retry logic with exponential backoff
- Comprehensive error handling with `YodError`, `YodAPIError`, `YodConnectionError`
