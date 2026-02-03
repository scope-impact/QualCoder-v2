"""
Tests for FailureEvent - base class for publishable failure events.

Key business logic tested:
- Event type parsing (operation and reason extraction)
- Message generation from event_type
"""

from datetime import UTC, datetime

import pytest

from src.shared.common.failure_events import FailureEvent


class TestFailureEventProperties:
    """Test property extraction from event_type."""

    def test_operation_extracts_before_slash(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
        )

        assert event.operation == "CODE_NOT_CREATED"

    def test_reason_extracts_after_slash(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
        )

        assert event.reason == "DUPLICATE_NAME"

    def test_reason_returns_empty_when_no_slash(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="UNKNOWN_ERROR",
        )

        assert event.reason == ""

    def test_operation_returns_full_type_when_no_slash(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="UNKNOWN_ERROR",
        )

        assert event.operation == "UNKNOWN_ERROR"


class TestFailureEventMessage:
    """Test message generation."""

    def test_message_formats_event_type_as_title_case(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
        )

        # Underscores become spaces, slash becomes colon
        assert "Code Not Created" in event.message
        assert "Duplicate Name" in event.message

    def test_message_handles_simple_event_type(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="ERROR",
        )

        assert event.message == "Error"


class TestFailureEventIsFailure:
    """Test is_failure property."""

    def test_is_failure_always_true(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="ANY_TYPE",
        )

        assert event.is_failure is True


class TestFailureEventHelpers:
    """Test class helper methods."""

    def test_generate_id_creates_unique_ids(self):
        id1 = FailureEvent._generate_id()
        id2 = FailureEvent._generate_id()

        assert id1 != id2
        assert isinstance(id1, str)

    def test_now_returns_utc_datetime(self):
        ts = FailureEvent._now()

        assert ts.tzinfo == UTC
        assert isinstance(ts, datetime)


class TestFailureEventImmutability:
    """Test that FailureEvent is frozen."""

    def test_cannot_modify_event_type(self):
        event = FailureEvent(
            event_id="evt-1",
            occurred_at=datetime.now(UTC),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
        )

        with pytest.raises(AttributeError):
            event.event_type = "NEW_TYPE"
