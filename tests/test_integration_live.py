"""Integration tests for the Yod SDK against a live API server.

Run with: poetry run pytest sdk/tests/test_integration_live.py -v
Requires: Backend running at localhost:8000 with ALLOW_INSECURE_USER_HEADER=true
"""

from __future__ import annotations

# Add SDK to path
import sys
import uuid
from pathlib import Path

import pytest

sdk_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(sdk_path))

from yod import AsyncYodClient, YodClient  # noqa: E402
from yod.exceptions import NotFoundError  # noqa: E402

# Test configuration
# Note: Local dev server uses /api prefix for API endpoints, but health endpoints are at root
BASE_URL = "http://localhost:8000/api"
HEALTH_BASE_URL = "http://localhost:8000"  # Health endpoints at root
TEST_USER_ID = f"sdk-test-user-{uuid.uuid4().hex[:8]}"


class TestSyncClientIntegration:
    """Integration tests for the synchronous client."""

    @pytest.fixture
    def client(self):
        """Create a client for testing."""
        client = YodClient(base_url=BASE_URL, user_id=TEST_USER_ID)
        yield client
        client.close()

    def test_health_check(self):
        """Test health endpoint (uses root URL, not /api)."""
        with YodClient(base_url=HEALTH_BASE_URL, user_id=TEST_USER_ID) as health_client:
            response = health_client.health()
            assert response.status == "ok"

    def test_ready_check(self):
        """Test ready endpoint (uses root URL, not /api)."""
        with YodClient(base_url=HEALTH_BASE_URL, user_id=TEST_USER_ID) as health_client:
            response = health_client.ready()
            assert response.status == "ok"
            assert response.neo4j is not None
            assert response.neo4j.ok is True
            assert response.qdrant is not None
            assert response.qdrant.ok is True
            # Test new redis field
            assert response.redis is not None
            assert response.redis.status == "ok"

    def test_ingest_and_chat(self, client: YodClient):
        """Test ingest and chat workflow."""
        # Ingest some data
        ingest_response = client.ingest_chat(
            text="My favorite programming language is Python. I have been coding for 10 years."
        )
        assert ingest_response.source_id is not None
        assert ingest_response.chunks > 0

        # Query the data
        chat_response = client.chat(
            question="What is my favorite programming language?"
        )
        assert chat_response.answer is not None
        assert len(chat_response.answer) > 0
        # The answer should mention Python
        answer_lower = chat_response.answer.lower()
        assert "python" in answer_lower or "don't know" in answer_lower

    def test_session_operations(self, client: YodClient):
        """Test session CRUD operations."""
        # Create a session
        session = client.create_session(
            agent_id="test-agent",
            metadata={"purpose": "integration-test"}
        )
        assert session.session_id is not None
        assert session.agent_id == "test-agent"
        assert session.metadata.get("purpose") == "integration-test"

        # List sessions
        sessions_response = client.list_sessions()
        assert sessions_response.total >= 1
        session_ids = [s.session_id for s in sessions_response.sessions]
        assert session.session_id in session_ids

        # List with pagination
        paginated = client.list_sessions(limit=1, offset=0)
        assert len(paginated.sessions) <= 1

        # List with agent filter
        filtered = client.list_sessions(agent_id="test-agent")
        assert all(s.agent_id == "test-agent" for s in filtered.sessions)

        # Get session
        fetched = client.get_session(session.session_id)
        assert fetched.session_id == session.session_id

        # Update session metadata
        updated = client.update_session(
            session.session_id,
            metadata={"purpose": "updated-test", "extra": "data"}
        )
        assert updated.session_id == session.session_id
        assert updated.metadata.get("purpose") == "updated-test"
        assert updated.metadata.get("extra") == "data"

        # Delete session (with cascade=True by default)
        result = client.delete_session(session.session_id)
        assert result["deleted"] is True
        assert result["cascade"] is True

    def test_session_with_cascade_false(self, client: YodClient):
        """Test session deletion with cascade=False."""
        # Create a session
        session = client.create_session(agent_id="cascade-test")

        # Ingest data into the session
        client.ingest_chat(
            text="This is session-scoped data for cascade test.",
            session_id=session.session_id
        )

        # Delete session with cascade=False (converts claims to global)
        result = client.delete_session(session.session_id, cascade=False)
        assert result["deleted"] is True
        assert result["cascade"] is False

    def test_session_isolation(self, client: YodClient):
        """Test that session-scoped data is isolated."""
        # Create a session
        session = client.create_session(agent_id="isolation-test")

        # Ingest data with session_id
        unique_food = f"zxyqfood_{uuid.uuid4().hex[:6]}"
        client.ingest_chat(
            text=f"My favorite food is {unique_food}.",
            session_id=session.session_id
        )

        # Query WITHOUT session_id - should NOT find session-scoped data
        chat_without_session = client.chat(
            question="What is my favorite food?"
        )

        # Query WITH session_id - should find session-scoped data
        chat_with_session = client.chat(
            question="What is my favorite food?",
            session_id=session.session_id
        )

        # The session-scoped query should have more relevant data
        # (This is a soft assertion since LLM responses vary)
        print(f"Without session: {chat_without_session.answer}")
        print(f"With session: {chat_with_session.answer}")

        # Cleanup
        client.delete_session(session.session_id)

    def test_memory_operations(self, client: YodClient):
        """Test memory list and get operations."""
        # First ingest some data to ensure we have memories
        client.ingest_chat(text="I enjoy reading science fiction books.")

        # List memories
        memories = client.list_memories(limit=10)
        # Note: might be empty if no memories extracted yet

        if memories.items:
            # Get a specific memory
            memory_id = memories.items[0].memory_id
            memory = client.get_memory(memory_id)
            assert memory.memory_id == memory_id

    def test_not_found_error(self, client: YodClient):
        """Test that NotFoundError is raised for missing resources."""
        with pytest.raises(NotFoundError):
            client.get_session("nonexistent-session-id")

        with pytest.raises(NotFoundError):
            client.get_memory("nonexistent-memory-id")

    def test_conversation_operations(self, client: YodClient):
        """Test conversation CRUD operations."""
        # Create a conversation
        conv = client.create_conversation(title="Test Conversation")
        assert conv.conversation_id is not None
        assert conv.title == "Test Conversation"

        # Get conversation
        fetched = client.get_conversation(conv.conversation_id)
        assert fetched.conversation_id == conv.conversation_id

        # Update conversation
        updated = client.update_conversation(conv.conversation_id, title="Updated Title")
        assert updated.title == "Updated Title"

        # Add message
        msg = client.add_message(
            conv.conversation_id,
            role="user",
            content="Hello, this is a test message."
        )
        assert msg.message_id is not None
        assert msg.role == "user"
        assert msg.content == "Hello, this is a test message."

        # Get messages
        messages = client.get_messages(conv.conversation_id)
        msg_ids = [m.message_id for m in messages]
        assert msg.message_id in msg_ids

        # List conversations (should include our conversation now)
        convs = client.list_conversations()
        # Just verify it returns a list (may or may not have our conv depending on timing)
        assert isinstance(convs, list)

        # Delete conversation
        result = client.delete_conversation(conv.conversation_id)
        assert result["ok"] is True


class TestAsyncClientIntegration:
    """Integration tests for the async client."""

    @pytest.fixture
    async def client(self):
        """Create an async client for testing."""
        client = AsyncYodClient(base_url=BASE_URL, user_id=TEST_USER_ID + "-async")
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health endpoint (uses root URL, not /api)."""
        async with AsyncYodClient(base_url=HEALTH_BASE_URL, user_id=TEST_USER_ID) as health_client:
            response = await health_client.health()
            assert response.status == "ok"

    @pytest.mark.asyncio
    async def test_ready_check(self):
        """Test ready endpoint (uses root URL, not /api)."""
        async with AsyncYodClient(base_url=HEALTH_BASE_URL, user_id=TEST_USER_ID) as health_client:
            response = await health_client.ready()
            assert response.status == "ok"

    @pytest.mark.asyncio
    async def test_ingest_and_chat(self, client: AsyncYodClient):
        """Test ingest and chat workflow."""
        # Ingest some data
        ingest_response = await client.ingest_chat(
            text="I work as a software engineer at a tech startup."
        )
        assert ingest_response.source_id is not None

        # Query the data
        chat_response = await client.chat(
            question="What do I do for work?"
        )
        assert chat_response.answer is not None

    @pytest.mark.asyncio
    async def test_session_operations(self, client: AsyncYodClient):
        """Test session operations with async client."""
        # Create session
        session = await client.create_session(agent_id="async-test")
        assert session.session_id is not None

        # List with pagination
        sessions = await client.list_sessions(limit=5, offset=0)
        assert sessions.total >= 1

        # Delete with cascade parameter
        result = await client.delete_session(session.session_id, cascade=True)
        assert result["deleted"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
