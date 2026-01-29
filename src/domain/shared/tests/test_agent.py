"""
Tests for agent foundation types - TrustLevel and AgentSession.
TDD RED phase: These tests will fail until agent.py is implemented.
"""

import pytest
from datetime import datetime, timezone
from enum import Enum

from src.domain.shared.agent import TrustLevel, AgentSession


class TestTrustLevel:
    """Tests for TrustLevel enum"""

    def test_trust_level_has_exactly_four_members(self):
        """TrustLevel should have exactly 4 permission levels"""
        assert len(TrustLevel) == 4

    def test_trust_level_values_match_mcp_protocol(self):
        """TrustLevel values should match MCP protocol strings"""
        assert TrustLevel.AUTONOMOUS.value == "auto"
        assert TrustLevel.NOTIFY.value == "notify"
        assert TrustLevel.SUGGEST.value == "suggest"
        assert TrustLevel.REQUIRE.value == "require"

    def test_trust_level_is_enum(self):
        """TrustLevel should be a proper Enum"""
        assert issubclass(TrustLevel, Enum)


class TestAgentSession:
    """Tests for AgentSession base type"""

    def test_sessions_with_same_values_are_equal(self):
        """AgentSessions with identical values should be equal"""
        now = datetime.now(timezone.utc)
        session1 = AgentSession(
            session_id="sess-123",
            agent_id="claude-code",
            trust_level=TrustLevel.SUGGEST,
            created_at=now
        )
        session2 = AgentSession(
            session_id="sess-123",
            agent_id="claude-code",
            trust_level=TrustLevel.SUGGEST,
            created_at=now
        )
        assert session1 == session2

    def test_sessions_are_hashable(self):
        """AgentSession should be usable in sets for tracking"""
        session = AgentSession(
            session_id="sess-1",
            agent_id="agent-1",
            trust_level=TrustLevel.AUTONOMOUS,
            created_at=datetime.now(timezone.utc)
        )
        session_set = {session}
        assert session in session_set

    def test_metadata_defaults_to_none(self):
        """AgentSession metadata should be optional, defaulting to None"""
        session = AgentSession(
            session_id="sess-1",
            agent_id="agent-1",
            trust_level=TrustLevel.NOTIFY,
            created_at=datetime.now(timezone.utc)
        )
        assert session.metadata is None

    def test_session_accepts_metadata_dict(self):
        """AgentSession should accept arbitrary metadata"""
        metadata = {"model": "claude-3", "version": "1.0", "capabilities": ["coding"]}
        session = AgentSession(
            session_id="sess-1",
            agent_id="claude-code",
            trust_level=TrustLevel.SUGGEST,
            created_at=datetime.now(timezone.utc),
            metadata=metadata
        )
        assert session.metadata == metadata
        assert session.metadata["model"] == "claude-3"
