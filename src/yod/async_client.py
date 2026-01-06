"""Asynchronous client for the Yod API."""

from __future__ import annotations

from typing import Any

import httpx

from yod._base_client import BaseClient
from yod._retry import execute_with_retry_async
from yod.exceptions import YodConnectionError, YodTimeoutError
from yod.models import (
    ChatResponse,
    HealthResponse,
    IngestResponse,
    MemoryItem,
    MemoryListResponse,
    ReadyResponse,
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

    async def __aenter__(self) -> "AsyncYodClient":
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
                return await client.request(method, url, files=files, headers=headers, params=params)
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
    ) -> IngestResponse:
        """
        Ingest text or conversation data into memory.

        Args:
            text: The text content to ingest (1-100,000 chars)
            source_id: Optional identifier for the source
            timestamp: Optional ISO8601 timestamp

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

        data = await self._request("POST", "/ingest/chat", json=payload)
        return IngestResponse.model_validate(data)

    # --- Chat Operations ---

    async def chat(
        self,
        question: str,
        *,
        language: str | None = None,
        as_of: str | None = None,
    ) -> ChatResponse:
        """
        Query memories with a question.

        Args:
            question: The question to ask (1-10,000 chars)
            language: Optional language code for response (e.g., "en", "fa")
            as_of: Optional ISO8601 timestamp for temporal queries

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
            params["include_inactive"] = "true"
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

        result: dict[str, Any] = await self._request("PATCH", f"/memories/{memory_id}", json=payload)
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

    # --- Health Operations ---

    async def health(self) -> HealthResponse:
        """Check API health status."""
        data = await self._request("GET", "/health")
        return HealthResponse.model_validate(data)

    async def ready(self) -> ReadyResponse:
        """Check API readiness (includes backend checks)."""
        data = await self._request("GET", "/ready")
        return ReadyResponse.model_validate(data)
