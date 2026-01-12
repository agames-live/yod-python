"""Asynchronous client for the Yod API."""

from __future__ import annotations

from typing import Any

import httpx

from yod._base_client import BaseClient
from yod._retry import execute_with_retry_async
from yod.exceptions import YodConnectionError, YodTimeoutError
from yod.models import (
    ApproveMemoryResponse,
    AuditSummaryResponse,
    ChatResponse,
    ClaimsGraphResponse,
    ConsolidationResultResponse,
    ConsolidationStatusResponse,
    ConsolidationTriggerResponse,
    ContradictionsResponse,
    Conversation,
    CreateKeyResponse,
    EntitiesResponse,
    EntityDetailsResponse,
    EvolutionKeysResponse,
    EvolutionResponse,
    FeedbackResponse,
    FeedbackType,
    HealthResponse,
    IngestResponse,
    KeyListResponse,
    MemoryAuditTrailResponse,
    MemoryItem,
    MemoryListResponse,
    MemoryToolAction,
    MemoryToolResponse,
    MemoryToolsSchemaResponse,
    MemoryType,
    Message,
    MessageInput,
    ProposedMemoriesResponse,
    QuotaResponse,
    ReadyResponse,
    RecentAuditResponse,
    RejectMemoryResponse,
    Session,
    SessionContradictionsResponse,
    SessionListResponse,
    STTResponse,
    SuspiciousActivityResponse,
    UsageResponse,
)


class AsyncYodClient(BaseClient):
    """
    Asynchronous client for the Yod API.

    Example:
        >>> async with AsyncYodClient(bearer_token="your-jwt-token") as client:
        ...     response = await client.chat("What do I know about Python?")
        ...     print(response.answer)

    All methods are coroutines and must be awaited.
    For synchronous usage, see YodClient.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        bearer_token: str | None = None,
        user_id: str | None = None,
        timeout: float = 30.0,
        connect_timeout: float = 5.0,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """
        Initialize asynchronous client.

        Args:
            api_key: Yod API key (starts with sk-yod-)
            base_url: API base URL (default: https://api.yod.agames.ai)
            bearer_token: JWT bearer token (alternative to api_key)
            user_id: User ID for X-User-Id header (dev mode)
            timeout: Request timeout in seconds
            connect_timeout: Connection timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            bearer_token=bearer_token,
            user_id=user_id,
            timeout=timeout,
            connect_timeout=connect_timeout,
            max_retries=max_retries,
            **kwargs,
        )
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout, connect=self.config.connect_timeout),
                headers=self._build_headers(),
            )
        return self._client

    async def __aenter__(self) -> AsyncYodClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit - closes HTTP session."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        raw_response: bool = False,
    ) -> Any:
        """Make an async HTTP request with retry logic."""
        url = self._build_url(path)
        client = self._get_client()

        # Filter out None params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        async def make_request() -> httpx.Response:
            if files:
                # For file uploads, don't use JSON content type
                headers = self._build_headers()
                headers.pop("Content-Type", None)
                return await client.request(
                    method, url, files=files, headers=headers, params=params
                )
            return await client.request(method, url, json=json, params=params)

        try:
            response = await execute_with_retry_async(make_request, self.retry_config)
        except httpx.ConnectError as e:
            raise YodConnectionError(f"Failed to connect to {url}: {e}") from e
        except httpx.TimeoutException as e:
            raise YodTimeoutError(f"Request to {url} timed out: {e}") from e

        request_id = response.headers.get("X-Request-Id")
        headers = dict(response.headers)

        if raw_response:
            if response.status_code >= 400:
                body = self._parse_response_body(response.content)
                self._handle_error_response(response.status_code, body, request_id, headers)
            return response.content

        body = self._parse_response_body(response.content)

        if response.status_code >= 400:
            self._handle_error_response(response.status_code, body, request_id, headers)

        return body

    # --- Ingest Operations ---

    async def ingest_chat(
        self,
        text: str,
        *,
        source_id: str | None = None,
        timestamp: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> IngestResponse:
        """
        Ingest text or conversation data into memory.

        Args:
            text: The text content to ingest (1-100,000 chars)
            source_id: Optional identifier for the source
            timestamp: Optional ISO8601 timestamp
            session_id: Optional session ID for memory isolation across contexts.
                       When provided, memories are scoped to this session.
            agent_id: Optional agent identifier within a session.

        Returns:
            IngestResponse with source_id, chunks count, and extracted entities/memories

        Raises:
            ValidationError: If text is empty or too long
            RateLimitError: If rate limit exceeded
        """
        payload = {"text": text}
        if source_id is not None:
            payload["source_id"] = source_id
        if timestamp is not None:
            payload["timestamp"] = timestamp
        if session_id is not None:
            payload["session_id"] = session_id
        if agent_id is not None:
            payload["agent_id"] = agent_id

        data = await self._request("POST", "/ingest/chat", json=payload)
        return IngestResponse.model_validate(data)

    # --- Chat Operations ---

    async def chat(
        self,
        question: str,
        *,
        language: str | None = None,
        as_of: str | None = None,
        session_id: str | None = None,
    ) -> ChatResponse:
        """
        Query memories with a question.

        Args:
            question: The question to ask (1-10,000 chars)
            language: Optional language code for response (e.g., "en", "fa")
            as_of: Optional ISO8601 timestamp for temporal queries
            session_id: Optional session ID for scoped retrieval.
                       When provided, includes both session-scoped and global memories.

        Returns:
            ChatResponse with answer, citations, and used_memory_ids

        Raises:
            ValidationError: If question is empty or too long
            RateLimitError: If rate limit exceeded
        """
        payload: dict[str, Any] = {"question": question}
        if language is not None:
            payload["language"] = language
        if as_of is not None:
            payload["as_of"] = as_of
        if session_id is not None:
            payload["session_id"] = session_id

        data = await self._request("POST", "/chat", json=payload)
        return ChatResponse.model_validate(data)

    # --- Memory Operations ---

    async def list_memories(
        self,
        *,
        limit: int = 50,
        kind: str | None = None,
        search: str | None = None,
        include_inactive: bool = False,
        as_of: str | None = None,
    ) -> MemoryListResponse:
        """
        List memories with optional filtering.

        Args:
            limit: Maximum number of memories to return (default: 50)
            kind: Filter by memory kind (preference, event, etc.)
            search: Search term to filter memories
            include_inactive: Include superseded/inactive memories
            as_of: ISO8601 timestamp for temporal filtering

        Returns:
            MemoryListResponse with list of MemoryItem
        """
        params: dict[str, Any] = {"limit": limit}
        if kind is not None:
            params["kind"] = kind
        if search is not None:
            params["search"] = search
        if include_inactive:
            params["include_inactive"] = include_inactive
        if as_of is not None:
            params["as_of"] = as_of

        data = await self._request("GET", "/memories", params=params)
        return MemoryListResponse.model_validate(data)

    async def get_memory(self, memory_id: str) -> MemoryItem:
        """
        Get a single memory by ID.

        Args:
            memory_id: The memory ID to retrieve

        Returns:
            MemoryItem with full memory details

        Raises:
            NotFoundError: If memory does not exist
        """
        data = await self._request("GET", f"/memories/{memory_id}")
        return MemoryItem.model_validate(data)

    async def update_memory(
        self,
        memory_id: str,
        *,
        kind: str | None = None,
        summary: str | None = None,
        confidence: float | None = None,
    ) -> dict[str, Any]:
        """
        Update a memory's fields.

        Args:
            memory_id: The memory ID to update
            kind: New kind value
            summary: New summary text
            confidence: New confidence score (0.0-1.0)

        Returns:
            Dict with ok: True on success

        Raises:
            NotFoundError: If memory does not exist
            ValidationError: If confidence out of range
        """
        payload: dict[str, Any] = {}
        if kind is not None:
            payload["kind"] = kind
        if summary is not None:
            payload["summary"] = summary
        if confidence is not None:
            payload["confidence"] = confidence

        result: dict[str, Any] = await self._request(
            "PATCH", f"/memories/{memory_id}", json=payload
        )
        return result

    async def delete_memory(self, memory_id: str) -> dict[str, Any]:
        """
        Delete a memory.

        Args:
            memory_id: The memory ID to delete

        Returns:
            Dict with ok and qdrant_deleted count

        Raises:
            NotFoundError: If memory does not exist
        """
        result: dict[str, Any] = await self._request("DELETE", f"/memories/{memory_id}")
        return result

    async def get_memory_history(self, memory_id: str) -> MemoryListResponse:
        """
        Get temporal history of a memory.

        Returns all versions across time including superseded versions.

        Args:
            memory_id: The memory ID to get history for

        Returns:
            MemoryListResponse with historical versions

        Raises:
            NotFoundError: If memory not found or has no history
        """
        data = await self._request("GET", f"/memories/{memory_id}/history")
        return MemoryListResponse.model_validate(data)

    # --- Session Operations ---

    async def create_session(
        self,
        *,
        agent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """
        Create a new session for memory scoping.

        Args:
            agent_id: Optional agent identifier for this session
            metadata: Optional metadata to attach to the session

        Returns:
            Session with session_id, user_id, agent_id, created_at, metadata
        """
        payload: dict[str, Any] = {}
        if agent_id is not None:
            payload["agent_id"] = agent_id
        if metadata is not None:
            payload["metadata"] = metadata

        data = await self._request("POST", "/sessions", json=payload)
        return Session.model_validate(data)

    async def list_sessions(
        self,
        *,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        """
        List sessions for the current user.

        Args:
            agent_id: Optional filter by agent ID
            limit: Maximum number of sessions to return (default: 50)
            offset: Number of sessions to skip for pagination (default: 0)

        Returns:
            SessionListResponse with sessions list and total count
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if agent_id is not None:
            params["agent_id"] = agent_id

        data = await self._request("GET", "/sessions", params=params)
        return SessionListResponse.model_validate(data)

    async def get_session(self, session_id: str) -> Session:
        """
        Get a session by ID.

        Args:
            session_id: The session ID to retrieve

        Returns:
            Session with full details

        Raises:
            NotFoundError: If session does not exist
        """
        data = await self._request("GET", f"/sessions/{session_id}")
        return Session.model_validate(data)

    async def update_session(
        self,
        session_id: str,
        *,
        metadata: dict[str, Any],
    ) -> Session:
        """
        Update session metadata.

        Args:
            session_id: The session ID to update
            metadata: New metadata to set for the session

        Returns:
            Session with updated details

        Raises:
            NotFoundError: If session does not exist
        """
        data = await self._request("PATCH", f"/sessions/{session_id}", json={"metadata": metadata})
        return Session.model_validate(data)

    async def delete_session(
        self,
        session_id: str,
        *,
        cascade: bool = True,
    ) -> dict[str, Any]:
        """
        Delete a session.

        Args:
            session_id: The session ID to delete
            cascade: If True (default), delete all claims associated with the session.
                    If False, convert session-scoped claims to global claims.

        Returns:
            Dict with deleted: True, session_id, and cascade value

        Raises:
            NotFoundError: If session does not exist
        """
        params = {"cascade": cascade}
        result: dict[str, Any] = await self._request(
            "DELETE", f"/sessions/{session_id}", params=params
        )
        return result

    # --- Health Operations ---

    async def health(self) -> HealthResponse:
        """Check API health status."""
        data = await self._request("GET", "/health")
        return HealthResponse.model_validate(data)

    async def ready(self) -> ReadyResponse:
        """Check API readiness (includes backend checks)."""
        data = await self._request("GET", "/ready")
        return ReadyResponse.model_validate(data)

    # --- API Key Operations ---

    async def create_api_key(
        self,
        name: str,
        *,
        scopes: list[str] | None = None,
        expires_in_days: int | None = None,
    ) -> CreateKeyResponse:
        """
        Create a new API key.

        Args:
            name: Human-readable name for the key
            scopes: Optional list of scopes (e.g., ["chat", "ingest"])
            expires_in_days: Optional expiration in days

        Returns:
            CreateKeyResponse with key_id and secret_key (shown only once!)
        """
        payload: dict[str, Any] = {"name": name}
        if scopes is not None:
            payload["scopes"] = scopes
        if expires_in_days is not None:
            payload["expires_in_days"] = expires_in_days

        data = await self._request("POST", "/keys", json=payload)
        return CreateKeyResponse.model_validate(data)

    async def list_api_keys(self) -> KeyListResponse:
        """
        List all API keys for the current user.

        Returns:
            KeyListResponse with list of APIKeyItem (secrets not included)
        """
        data = await self._request("GET", "/keys")
        return KeyListResponse.model_validate(data)

    async def revoke_api_key(self, key_id: str) -> dict[str, Any]:
        """
        Revoke an API key.

        Args:
            key_id: The key ID to revoke

        Returns:
            Dict with ok: True on success

        Raises:
            NotFoundError: If key does not exist
        """
        result: dict[str, Any] = await self._request("DELETE", f"/keys/{key_id}")
        return result

    async def get_usage(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> UsageResponse:
        """
        Get API usage statistics.

        Args:
            start_date: Optional start date (ISO8601)
            end_date: Optional end date (ISO8601)

        Returns:
            UsageResponse with summary and per-endpoint breakdown
        """
        params: dict[str, Any] = {}
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date

        data = await self._request("GET", "/keys/usage", params=params)
        return UsageResponse.model_validate(data)

    async def get_quota(self) -> QuotaResponse:
        """
        Get current quota status.

        Returns:
            QuotaResponse with plan info and quota limits
        """
        data = await self._request("GET", "/keys/quota")
        return QuotaResponse.model_validate(data)

    # --- Conversation Operations ---

    async def create_conversation(
        self,
        *,
        title: str | None = None,
        conversation_id: str | None = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            title: Optional title for the conversation
            conversation_id: Optional custom conversation ID

        Returns:
            Conversation with conversation_id, title, created_at, etc.
        """
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id

        data = await self._request("POST", "/conversations", json=payload)
        return Conversation.model_validate(data)

    async def list_conversations(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """
        List all conversations for the current user.

        Args:
            limit: Maximum number of conversations to return (default: 50)
            offset: Number of conversations to skip for pagination (default: 0)

        Returns:
            List of Conversation objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._request("GET", "/conversations", params=params)
        if data is None:
            return []
        return [Conversation.model_validate(c) for c in data]

    async def get_conversation(self, conversation_id: str) -> Conversation:
        """
        Get a conversation by ID.

        Args:
            conversation_id: The conversation ID to retrieve

        Returns:
            Conversation with full details

        Raises:
            NotFoundError: If conversation does not exist
        """
        data = await self._request("GET", f"/conversations/{conversation_id}")
        return Conversation.model_validate(data)

    async def update_conversation(
        self,
        conversation_id: str,
        *,
        title: str,
    ) -> Conversation:
        """
        Update a conversation's title.

        Args:
            conversation_id: The conversation ID to update
            title: New title for the conversation

        Returns:
            Conversation with updated details

        Raises:
            NotFoundError: If conversation does not exist
        """
        data = await self._request(
            "PATCH", f"/conversations/{conversation_id}", json={"title": title}
        )
        return Conversation.model_validate(data)

    async def delete_conversation(self, conversation_id: str) -> dict[str, Any]:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: The conversation ID to delete

        Returns:
            Dict with ok: True on success

        Raises:
            NotFoundError: If conversation does not exist
        """
        result: dict[str, Any] = await self._request(
            "DELETE", f"/conversations/{conversation_id}"
        )
        return result

    async def delete_all_conversations(self) -> dict[str, Any]:
        """
        Delete all conversations and messages for the current user.

        Returns:
            Dict with ok: True and deletion counts
        """
        result: dict[str, Any] = await self._request("DELETE", "/conversations")
        return result

    async def get_messages(
        self,
        conversation_id: str,
        *,
        limit: int = 100,
        before_id: str | None = None,
    ) -> list[Message]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: The conversation ID
            limit: Maximum number of messages to return (default: 100)
            before_id: Optional message ID for pagination (get messages before this)

        Returns:
            List of Message objects
        """
        params: dict[str, Any] = {"limit": limit}
        if before_id is not None:
            params["before_id"] = before_id

        data = await self._request(
            "GET", f"/conversations/{conversation_id}/messages", params=params
        )
        if data is None:
            return []
        return [Message.model_validate(m) for m in data]

    async def add_message(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        citations: list[dict[str, Any]] | None = None,
    ) -> Message:
        """
        Add a message to a conversation.

        Args:
            conversation_id: The conversation ID
            role: Message role ("user" or "assistant")
            content: Message content
            citations: Optional list of citations

        Returns:
            Message with message_id, created_at, etc.
        """
        payload: dict[str, Any] = {"role": role, "content": content}
        if citations is not None:
            payload["citations"] = citations

        data = await self._request(
            "POST", f"/conversations/{conversation_id}/messages", json=payload
        )
        return Message.model_validate(data)

    async def sync_messages(
        self,
        conversation_id: str,
        messages: list[MessageInput],
    ) -> dict[str, Any]:
        """
        Sync messages from frontend to backend.

        Used for initial sync when user has local messages not yet persisted.

        Args:
            conversation_id: The conversation ID
            messages: List of MessageInput objects to sync

        Returns:
            Dict with ok: True and saved count
        """
        payload = {"messages": [m.model_dump() for m in messages]}
        result: dict[str, Any] = await self._request(
            "POST", f"/conversations/{conversation_id}/sync", json=payload
        )
        return result

    # --- Speech Operations ---

    async def speech_to_text(
        self,
        audio_file: bytes,
        *,
        filename: str = "audio.webm",
    ) -> STTResponse:
        """
        Convert speech audio to text using OpenAI Whisper.

        Args:
            audio_file: Audio file bytes (webm, mp3, wav, etc.)
            filename: Filename with extension to help identify format

        Returns:
            STTResponse with transcribed text and detected language
        """
        files = {"audio": (filename, audio_file)}
        data = await self._request("POST", "/speech/stt", files=files)
        return STTResponse.model_validate(data)

    async def text_to_speech(
        self,
        text: str,
        *,
        voice_id: str | None = None,
    ) -> bytes:
        """
        Convert text to speech audio using ElevenLabs.

        Args:
            text: Text to convert to speech
            voice_id: Optional ElevenLabs voice ID (uses server default if not specified)

        Returns:
            MP3 audio bytes
        """
        payload: dict[str, Any] = {"text": text}
        if voice_id is not None:
            payload["voice_id"] = voice_id

        return await self._request("POST", "/speech/tts", json=payload, raw_response=True)

    # --- Consolidation Operations ---

    async def get_consolidation_status(self) -> ConsolidationStatusResponse:
        """
        Get memory consolidation status and statistics.

        Returns configuration, statistics, and details of the last consolidation run.

        Returns:
            ConsolidationStatusResponse with enabled, schedule, stats, and last_consolidation
        """
        data = await self._request("GET", "/consolidation/status")
        return ConsolidationStatusResponse.model_validate(data)

    async def run_consolidation(self) -> ConsolidationResultResponse:
        """
        Run synchronous memory consolidation.

        Executes memory consolidation immediately and waits for completion.
        This includes clustering episodic memories, abstracting patterns to
        semantic facts, pruning decayed memories, and detecting contradictions.

        Returns:
            ConsolidationResultResponse with detailed results including:
            - clusters_found: Number of episodic memory clusters discovered
            - clusters_abstracted: Number of clusters converted to semantic memories
            - claims_consolidated: Number of episodic claims marked as consolidated
            - claims_archived: Number of decayed memories archived
            - contradictions_found: Number of contradictions detected

        Note:
            For long-running consolidation, consider using trigger_consolidation()
            for async execution.
        """
        data = await self._request("POST", "/consolidation/run")
        return ConsolidationResultResponse.model_validate(data)

    async def trigger_consolidation(self) -> ConsolidationTriggerResponse:
        """
        Trigger asynchronous memory consolidation.

        Starts consolidation as a background job and returns immediately.
        Use get_consolidation_result() to check job status and retrieve results.

        Returns:
            ConsolidationTriggerResponse with:
            - started: Whether the job was started successfully
            - message: Human-readable status message
            - job_id: ID for tracking the background job (use with get_consolidation_result)
        """
        data = await self._request("POST", "/consolidation/trigger")
        return ConsolidationTriggerResponse.model_validate(data)

    async def get_consolidation_result(self, job_id: str) -> ConsolidationResultResponse:
        """
        Get the result of an async consolidation job.

        Args:
            job_id: The job ID returned from trigger_consolidation()

        Returns:
            ConsolidationResultResponse with detailed results.
            If still running, completed_at will be None.

        Raises:
            NotFoundError: If job_id does not exist
        """
        data = await self._request("GET", f"/consolidation/result/{job_id}")
        return ConsolidationResultResponse.model_validate(data)

    # --- Evolution/Drift Operations ---

    async def get_memory_evolution(
        self,
        key: str,
        *,
        time_windows: list[str] | None = None,
    ) -> EvolutionResponse:
        """
        Get evolution timeline for a memory key.

        Tracks how a memory's meaning has changed over time, detecting semantic drift.

        Args:
            key: Memory key to analyze (e.g., 'pref_favorite_color')
            time_windows: Optional time windows for analysis (default: ['1y', '6m', '3m', '1m'])

        Returns:
            EvolutionResponse with timeline, drift scores, pattern, and interpretation
        """
        params: dict[str, Any] = {}
        if time_windows is not None:
            params["time_windows"] = time_windows

        data = await self._request("GET", f"/memories/evolution/{key}", params=params)
        return EvolutionResponse.model_validate(data)

    async def list_evolution_keys(self, *, limit: int = 20) -> EvolutionKeysResponse:
        """
        List memory keys with drift potential.

        Returns keys that have multiple claims over time and may show semantic drift.

        Args:
            limit: Maximum number of keys to return (default: 20, max: 100)

        Returns:
            EvolutionKeysResponse with list of keys and count
        """
        data = await self._request("GET", "/memories/evolution", params={"limit": limit})
        return EvolutionKeysResponse.model_validate(data)

    # --- Entity Operations ---

    async def list_entities(self, *, limit: int = 200) -> EntitiesResponse:
        """
        List entities with co-occurrence links.

        Returns all entities in the knowledge graph with their connections.

        Args:
            limit: Maximum number of entities to return (default: 200)

        Returns:
            EntitiesResponse with entities list and co-occurrence links
        """
        data = await self._request("GET", "/entities", params={"limit": limit})
        return EntitiesResponse.model_validate(data)

    async def get_entity_details(self, entity_id: str) -> EntityDetailsResponse:
        """
        Get detailed entity information.

        Args:
            entity_id: The entity ID to retrieve

        Returns:
            EntityDetailsResponse with full details, related entities, and claims

        Raises:
            NotFoundError: If entity does not exist
        """
        data = await self._request("GET", f"/entities/{entity_id}/details")
        return EntityDetailsResponse.model_validate(data)

    # --- Graph Operations ---

    async def get_claims_graph(
        self,
        *,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> ClaimsGraphResponse:
        """
        Get claims graph for visualization.

        Returns claims and RELATES_TO edges optimized for graph rendering.

        Args:
            limit: Maximum number of claims to return (default: 100)
            include_inactive: Include superseded/inactive claims (default: False)

        Returns:
            ClaimsGraphResponse with nodes and links
        """
        params = {"limit": limit, "include_inactive": include_inactive}
        data = await self._request("GET", "/memories/graph", params=params)
        return ClaimsGraphResponse.model_validate(data)

    # --- Contradiction Operations ---

    async def get_contradictions(self) -> ContradictionsResponse:
        """
        Get summary of cross-session contradictions.

        Returns conflicts detected between memories from different sessions.

        Returns:
            ContradictionsResponse with total conflicts, samples, and session count
        """
        data = await self._request("GET", "/memories/contradictions")
        return ContradictionsResponse.model_validate(data)

    async def get_session_contradictions(
        self,
        session_id: str,
        *,
        limit: int = 20,
    ) -> SessionContradictionsResponse:
        """
        Get contradictions for a specific session.

        Args:
            session_id: The session ID to check
            limit: Maximum number of contradictions to return (default: 20)

        Returns:
            SessionContradictionsResponse with contradiction pairs
        """
        data = await self._request(
            "GET",
            f"/memories/contradictions/session/{session_id}",
            params={"limit": limit},
        )
        return SessionContradictionsResponse.model_validate(data)

    # --- Audit Operations ---

    async def get_audit_summary(self, *, days: int = 30) -> AuditSummaryResponse:
        """
        Get memory audit activity summary.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            AuditSummaryResponse with total events and breakdown by action
        """
        data = await self._request("GET", "/memories/audit/summary", params={"days": days})
        return AuditSummaryResponse.model_validate(data)

    async def get_recent_audit(
        self,
        *,
        limit: int = 20,
        action: str | None = None,
    ) -> RecentAuditResponse:
        """
        Get recent memory modifications.

        Args:
            limit: Maximum number of events to return (default: 20)
            action: Optional filter by action type (create, update, delete, etc.)

        Returns:
            RecentAuditResponse with list of audit events
        """
        params: dict[str, Any] = {"limit": limit}
        if action is not None:
            params["action"] = action

        data = await self._request("GET", "/memories/audit/recent", params=params)
        return RecentAuditResponse.model_validate(data)

    async def get_suspicious_activity(self, *, hours: int = 24) -> SuspiciousActivityResponse:
        """
        Detect suspicious modification patterns.

        Analyzes recent activity for anomalies like rapid changes or bulk deletions.

        Args:
            hours: Number of hours to analyze (default: 24)

        Returns:
            SuspiciousActivityResponse with detected patterns
        """
        data = await self._request("GET", "/memories/audit/suspicious", params={"hours": hours})
        return SuspiciousActivityResponse.model_validate(data)

    async def get_memory_audit_trail(
        self,
        memory_id: str,
        *,
        limit: int = 50,
    ) -> MemoryAuditTrailResponse:
        """
        Get audit trail for a specific memory.

        Args:
            memory_id: The memory ID to get audit trail for
            limit: Maximum number of events to return (default: 50)

        Returns:
            MemoryAuditTrailResponse with audit events for this memory

        Raises:
            NotFoundError: If memory does not exist
        """
        data = await self._request(
            "GET",
            f"/memories/{memory_id}/audit",
            params={"limit": limit},
        )
        return MemoryAuditTrailResponse.model_validate(data)

    # --- Proposed Memory Operations ---

    async def list_proposed_memories(self, *, limit: int = 50) -> ProposedMemoriesResponse:
        """
        List proposed memories awaiting review.

        Returns memories with 'proposed' status that need user approval.

        Args:
            limit: Maximum number of proposals to return (default: 50)

        Returns:
            ProposedMemoriesResponse with list of proposed memories
        """
        data = await self._request("GET", "/memories/proposed", params={"limit": limit})
        return ProposedMemoriesResponse.model_validate(data)

    async def approve_memory(self, memory_id: str) -> ApproveMemoryResponse:
        """
        Approve a proposed memory.

        Activates the memory and supersedes any existing claim with the same key.

        Args:
            memory_id: The proposed memory ID to approve

        Returns:
            ApproveMemoryResponse with approval details

        Raises:
            NotFoundError: If memory does not exist
            ValidationError: If memory is not in proposed status
        """
        data = await self._request("POST", f"/memories/{memory_id}/approve")
        return ApproveMemoryResponse.model_validate(data)

    async def reject_memory(self, memory_id: str) -> RejectMemoryResponse:
        """
        Reject a proposed memory.

        Marks the memory as 'rejected' and removes it from active consideration.

        Args:
            memory_id: The proposed memory ID to reject

        Returns:
            RejectMemoryResponse with rejection confirmation

        Raises:
            NotFoundError: If memory does not exist
            ValidationError: If memory is not in proposed status
        """
        data = await self._request("POST", f"/memories/{memory_id}/reject")
        return RejectMemoryResponse.model_validate(data)

    # --- Memory Tool Operations ---

    async def submit_feedback(
        self,
        feedback_type: FeedbackType,
        memory_ids: list[str],
        *,
        conversation_id: str | None = None,
        session_id: str | None = None,
    ) -> FeedbackResponse:
        """
        Submit feedback on memories for reinforcement learning.

        Provides positive, negative, or neutral feedback to improve memory retrieval.

        Args:
            feedback_type: Type of feedback ('positive', 'negative', 'neutral')
            memory_ids: List of memory IDs to provide feedback on
            conversation_id: Optional conversation context
            session_id: Optional session context

        Returns:
            FeedbackResponse with feedback ID and confirmation
        """
        payload: dict[str, Any] = {
            "feedback_type": feedback_type,
            "memory_ids": memory_ids,
        }
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id
        if session_id is not None:
            payload["session_id"] = session_id

        data = await self._request("POST", "/chat/feedback", json=payload)
        return FeedbackResponse.model_validate(data)

    async def execute_memory_tool(
        self,
        action: MemoryToolAction,
        content: str,
        *,
        key: str | None = None,
        memory_type: MemoryType = "semantic",
        confidence: float = 0.8,
        entity_names: list[str] | None = None,
        reason: str | None = None,
        session_id: str | None = None,
    ) -> MemoryToolResponse:
        """
        Execute a memory tool operation.

        Programmatically remember, forget, or update memories.

        Args:
            action: Action to perform ('remember', 'forget', 'update')
            content: Memory content
            key: Optional memory key
            memory_type: Memory type (default: 'semantic')
            confidence: Confidence score 0.0-1.0 (default: 0.8)
            entity_names: Optional list of entity names
            reason: Optional reason for the action
            session_id: Optional session ID for scoping

        Returns:
            MemoryToolResponse with success status and details
        """
        payload: dict[str, Any] = {
            "action": action,
            "content": content,
            "memory_type": memory_type,
            "confidence": confidence,
        }
        if key is not None:
            payload["key"] = key
        if entity_names is not None:
            payload["entity_names"] = entity_names
        if reason is not None:
            payload["reason"] = reason
        if session_id is not None:
            payload["session_id"] = session_id

        data = await self._request("POST", "/chat/memory-tool", json=payload)
        return MemoryToolResponse.model_validate(data)

    async def get_memory_tools_schema(self) -> MemoryToolsSchemaResponse:
        """
        Get memory tools schema for LLM function calling.

        Returns tool definitions that can be used with LLM function calling APIs.

        Returns:
            MemoryToolsSchemaResponse with tool definitions and enabled status
        """
        data = await self._request("GET", "/chat/memory-tools/schema")
        return MemoryToolsSchemaResponse.model_validate(data)
