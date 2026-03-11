"""Tests for Signal Bridge payloads."""

from datetime import UTC, datetime

import allure
import pytest

from src.shared.infra.signal_bridge.payloads import (
    ActivityItem,
    ActivityStatus,
    SignalPayload,
)

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("Shared Infrastructure"),
]


@allure.story("QC-000.02 Signal Bridge Payloads")
class TestActivityStatus:
    """Tests for ActivityStatus enum."""

    @allure.title("All status values exist with correct string values")
    def test_status_values(self) -> None:
        assert ActivityStatus.COMPLETED.value == "completed"
        assert ActivityStatus.PENDING.value == "pending"
        assert ActivityStatus.QUEUED.value == "queued"
        assert ActivityStatus.REJECTED.value == "rejected"
        assert ActivityStatus.FAILED.value == "failed"


@allure.story("QC-000.02 Signal Bridge Payloads")
class TestSignalPayload:
    """Tests for SignalPayload base type."""

    @allure.title("Creates payload, is immutable, and from_event handles local/AI sessions")
    def test_create_immutability_and_from_event(self) -> None:
        ts = datetime(2026, 1, 29, 12, 0, 0)

        # Create payload with all fields
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

        # Immutability
        with pytest.raises(AttributeError):
            payload.session_id = "modified"  # type: ignore

        # from_event with local session
        local_payload = SignalPayload.from_event(
            event_type="coding.code_created",
            occurred_at=ts,
        )
        assert local_payload.session_id == "local"
        assert local_payload.is_ai_action is False

        # from_event with AI session
        ai_payload = SignalPayload.from_event(
            event_type="coding.code_created",
            occurred_at=ts,
            session_id="claude-session-123",
        )
        assert ai_payload.session_id == "claude-session-123"
        assert ai_payload.is_ai_action is True


@allure.story("QC-000.02 Signal Bridge Payloads")
class TestActivityItem:
    """Tests for ActivityItem type."""

    @allure.title("Creates activity item with all fields and defaults")
    def test_create_activity_item(self) -> None:
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

    @allure.title("Factory methods (completed, pending, failed) set correct status and metadata")
    def test_factory_methods(self) -> None:
        # completed
        completed = ActivityItem.completed(
            description="Created code",
            context="coding",
            entity_type="code",
            entity_id="456",
        )
        assert completed.status == ActivityStatus.COMPLETED
        assert completed.description == "Created code"
        assert completed.context == "coding"
        assert completed.is_ai_action is False

        # pending with AI session
        pending = ActivityItem.pending(
            description="Waiting for approval",
            context="coding",
            entity_type="code",
            session_id="ai-session",
        )
        assert pending.status == ActivityStatus.PENDING
        assert pending.is_ai_action is True

        # failed with error metadata
        failed = ActivityItem.failed(
            description="Failed to create code",
            context="coding",
            entity_type="code",
            error="Name already exists",
        )
        assert failed.status == ActivityStatus.FAILED
        assert failed.metadata["error"] == "Name already exists"

        # completed with extra metadata
        with_meta = ActivityItem.completed(
            description="Created code",
            context="coding",
            entity_type="code",
            metadata={"color": "#FF0000", "category": "Emotions"},
        )
        assert with_meta.metadata["color"] == "#FF0000"
        assert with_meta.metadata["category"] == "Emotions"
