"""
Tests for FailureEvent - base class for publishable failure events.

Key business logic tested:
- Event type parsing (operation and reason extraction)
- Message generation from event_type
- is_failure property
- Helper methods (_generate_id, _now)
- Immutability (frozen dataclass)
"""

from datetime import UTC, datetime

import allure
import pytest

from src.shared.common.failure_events import FailureEvent

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("Shared Common"),
]


def _make_event(event_type: str = "CODE_NOT_CREATED/DUPLICATE_NAME") -> FailureEvent:
    return FailureEvent(
        event_id="evt-1",
        occurred_at=datetime.now(UTC),
        event_type=event_type,
    )


@allure.story("QC-000.04 Failure Events")
class TestFailureEventProperties:
    """Test property extraction from event_type."""

    @allure.title(
        "Extracts operation and reason from event_type with and without slash"
    )
    @pytest.mark.parametrize(
        "event_type, expected_operation, expected_reason",
        [
            pytest.param(
                "CODE_NOT_CREATED/DUPLICATE_NAME",
                "CODE_NOT_CREATED",
                "DUPLICATE_NAME",
                id="with-slash",
            ),
            pytest.param(
                "UNKNOWN_ERROR",
                "UNKNOWN_ERROR",
                "",
                id="no-slash",
            ),
        ],
    )
    def test_operation_and_reason_extraction(
        self, event_type, expected_operation, expected_reason
    ):
        event = _make_event(event_type)
        assert event.operation == expected_operation
        assert event.reason == expected_reason


@allure.story("QC-000.04 Failure Events")
class TestFailureEventMessage:
    """Test message generation."""

    @allure.title("Formats event_type as human-readable message")
    @pytest.mark.parametrize(
        "event_type, expected_fragments",
        [
            pytest.param(
                "CODE_NOT_CREATED/DUPLICATE_NAME",
                ["Code Not Created", "Duplicate Name"],
                id="compound",
            ),
            pytest.param("ERROR", ["Error"], id="simple"),
        ],
    )
    def test_message_formatting(self, event_type, expected_fragments):
        event = _make_event(event_type)
        for fragment in expected_fragments:
            assert fragment in event.message


@allure.story("QC-000.04 Failure Events")
class TestFailureEventBehavior:
    """Test is_failure, helpers, and immutability."""

    @allure.title("is_failure is always True, helpers work, and event is immutable")
    def test_is_failure_helpers_and_immutability(self):
        event = _make_event()

        # is_failure
        assert event.is_failure is True

        # _generate_id creates unique IDs
        id1 = FailureEvent._generate_id()
        id2 = FailureEvent._generate_id()
        assert id1 != id2
        assert isinstance(id1, str)

        # _now returns UTC datetime
        ts = FailureEvent._now()
        assert ts.tzinfo == UTC
        assert isinstance(ts, datetime)

        # Immutability
        with pytest.raises(AttributeError):
            event.event_type = "NEW_TYPE"
