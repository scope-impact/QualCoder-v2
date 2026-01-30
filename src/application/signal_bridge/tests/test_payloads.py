"""Tests for Signal Bridge payloads."""

from datetime import datetime

import pytest

from src.application.signal_bridge.payloads import (
    ActivityItem,
    ActivityStatus,
    SignalPayload,
)


class TestActivityStatus:
    """Tests for ActivityStatus enum."""

    def test_status_values(self) -> None:
        """Verify all status values exist."""
        assert ActivityStatus.COMPLETED.value == "completed"
        assert ActivityStatus.PENDING.value == "pending"
        assert ActivityStatus.QUEUED.value == "queued"
        assert ActivityStatus.REJECTED.value == "rejected"
        assert ActivityStatus.FAILED.value == "failed"


class TestSignalPayload:
    """Tests for SignalPayload base type."""

    def test_create_payload(self) -> None:
        """Test creating a signal payload."""
        ts = datetime(2026, 1, 29, 12, 0, 0)
        payload = SignalPayload(
            timestamp=ts,
            session_id="local",
            is_ai_action=False,
            event_type="coding.code_created",
        )
        assert payload.timestamp == ts
        assert payload.session_id == "local"
        assert payload.is_ai_action is False
        assert payload.event_type == "coding.code_created"

    def test_payload_immutability(self) -> None:
        """Test that payload is immutable."""
        payload = SignalPayload(
            timestamp=datetime.utcnow(),
            session_id="local",
            is_ai_action=False,
            event_type="test",
        )
        with pytest.raises(AttributeError):  # FrozenInstanceError
            payload.session_id = "modified"  # type: ignore

    def test_from_event_local_session(self) -> None:
        """Test from_event with local session."""
        ts = datetime(2026, 1, 29, 12, 0, 0)
        payload = SignalPayload.from_event(
            event_type="coding.code_created",
            occurred_at=ts,
        )
        assert payload.session_id == "local"
        assert payload.is_ai_action is False

    def test_from_event_ai_session(self) -> None:
        """Test from_event with AI session."""
        ts = datetime(2026, 1, 29, 12, 0, 0)
        payload = SignalPayload.from_event(
            event_type="coding.code_created",
            occurred_at=ts,
            session_id="claude-session-123",
        )
        assert payload.session_id == "claude-session-123"
        assert payload.is_ai_action is True


class TestActivityItem:
    """Tests for ActivityItem type."""

    def test_create_activity_item(self) -> None:
        """Test creating an activity item."""
        ts = datetime(2026, 1, 29, 12, 0, 0)
        item = ActivityItem(
            timestamp=ts,
            session_id="local",
            description="Created code 'Anxiety'",
            status=ActivityStatus.COMPLETED,
            context="coding",
            entity_type="code",
            entity_id="123",
        )
        assert item.timestamp == ts
        assert item.session_id == "local"
        assert item.description == "Created code 'Anxiety'"
        assert item.status == ActivityStatus.COMPLETED
        assert item.context == "coding"
        assert item.entity_type == "code"
        assert item.entity_id == "123"
        assert item.is_ai_action is False
        assert item.metadata == {}

    def test_completed_factory(self) -> None:
        """Test ActivityItem.completed factory method."""
        item = ActivityItem.completed(
            description="Created code",
            context="coding",
            entity_type="code",
            entity_id="456",
        )
        assert item.status == ActivityStatus.COMPLETED
        assert item.description == "Created code"
        assert item.context == "coding"
        assert item.is_ai_action is False

    def test_pending_factory(self) -> None:
        """Test ActivityItem.pending factory method."""
        item = ActivityItem.pending(
            description="Waiting for approval",
            context="coding",
            entity_type="code",
            session_id="ai-session",
        )
        assert item.status == ActivityStatus.PENDING
        assert item.is_ai_action is True

    def test_failed_factory(self) -> None:
        """Test ActivityItem.failed factory method."""
        item = ActivityItem.failed(
            description="Failed to create code",
            context="coding",
            entity_type="code",
            error="Name already exists",
        )
        assert item.status == ActivityStatus.FAILED
        assert item.metadata["error"] == "Name already exists"

    def test_activity_with_metadata(self) -> None:
        """Test activity item with additional metadata."""
        item = ActivityItem.completed(
            description="Created code",
            context="coding",
            entity_type="code",
            metadata={"color": "#FF0000", "category": "Emotions"},
        )
        assert item.metadata["color"] == "#FF0000"
        assert item.metadata["category"] == "Emotions"
