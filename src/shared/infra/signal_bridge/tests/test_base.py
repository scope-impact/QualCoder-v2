"""Tests for BaseSignalBridge class."""

from dataclasses import dataclass
from typing import Any

import allure
import pytest

from src.shared.infra.signal_bridge.base import BaseSignalBridge
from src.shared.infra.signal_bridge.payloads import ActivityStatus, SignalPayload
from src.shared.infra.signal_bridge.tests.conftest import MockDomainEvent, MockEventBus

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-000 Shared Infrastructure"),
]


# Test payload type
@dataclass(frozen=True)
class TestPayload(SignalPayload):
    """Test payload with additional field."""

    data: str = ""


# Test converter
class TestConverter:
    """Test converter implementation."""

    def convert(self, event: MockDomainEvent) -> TestPayload:
        return TestPayload(
            timestamp=event.occurred_at,
            session_id="local",
            is_ai_action=False,
            event_type=event.event_type,
            data=event.data,
        )


# Concrete test bridge implementation
class TestSignalBridge(BaseSignalBridge):
    """Concrete implementation for testing."""

    # Mock signals (without PySide6)
    test_event_signal: Any = None
    _emitted_payloads: list

    def __init__(self, event_bus: Any) -> None:
        self._emitted_payloads = []
        # Create mock signals
        self.test_event_signal = MockSignal()
        self.activity_logged = MockSignal()  # Override class-level Signal
        super().__init__(event_bus)

    def _get_context_name(self) -> str:
        return "test"

    def _register_converters(self) -> None:
        self.register_converter(
            "test.sample_event",
            TestConverter(),
            "test_event_signal",
        )

    def _build_signal_registry(self) -> None:
        """Override to add our mock signal."""
        self._signals = {
            "test_event_signal": self.test_event_signal,
            "activity_logged": self.activity_logged,
        }


class MockSignal:
    """Mock PyQt signal for testing without Qt."""

    def __init__(self) -> None:
        self.emissions: list = []

    def emit(self, payload: Any) -> None:
        self.emissions.append(payload)

    def __call__(self, *args: Any) -> "MockSignal":
        return self


@allure.story("QC-000.01 Signal Bridge")
class TestBaseSignalBridgeSingleton:
    """Tests for BaseSignalBridge singleton, lifecycle, and context manager."""

    @allure.title("Singleton pattern, start/stop lifecycle, and context manager")
    def test_singleton_lifecycle_and_context_manager(
        self, mock_event_bus: MockEventBus
    ) -> None:
        TestSignalBridge.clear_instance()

        # Singleton requires event_bus on first call
        with pytest.raises(ValueError, match="requires event_bus"):
            TestSignalBridge.instance()

        bridge1 = TestSignalBridge.instance(mock_event_bus)
        bridge2 = TestSignalBridge.instance()
        assert bridge1 is bridge2
        TestSignalBridge.clear_instance()

        # Start/stop lifecycle
        bridge = TestSignalBridge(mock_event_bus)
        assert mock_event_bus.get_handler_count("test.sample_event") == 0

        bridge.start()
        assert mock_event_bus.get_handler_count("test.sample_event") == 1
        assert bridge.is_running() is True

        # Double start is safe
        bridge.start()
        assert mock_event_bus.get_handler_count("test.sample_event") == 1

        bridge.stop()
        assert bridge.is_running() is False
        assert mock_event_bus.get_handler_count("test.sample_event") == 0

        # Double stop is safe
        bridge.stop()
        assert bridge.is_running() is False

        # Context manager
        bridge2 = TestSignalBridge(mock_event_bus)
        with bridge2:
            assert bridge2.is_running() is True
        assert bridge2.is_running() is False


@allure.story("QC-000.01 Signal Bridge")
class TestBaseSignalBridgeDispatch:
    """Tests for event dispatch, activity logging, and converter validation."""

    @allure.title(
        "Events converted and emitted; activity logged; converter validates; emit_activity works"
    )
    def test_dispatch_validation_and_activity(
        self,
        mock_event_bus: MockEventBus,
        sample_event: MockDomainEvent,
    ) -> None:
        bridge = TestSignalBridge(mock_event_bus)
        bridge.start()

        mock_event_bus.publish(sample_event)

        # Check signal was emitted with converted payload
        signal = bridge.test_event_signal
        assert len(signal.emissions) == 1
        payload = signal.emissions[0]
        assert isinstance(payload, TestPayload)
        assert payload.data == "sample data"
        assert payload.event_type == "test.sample_event"

        # Check activity was logged
        activity_signal = bridge._signals["activity_logged"]
        assert len(activity_signal.emissions) == 1
        activity = activity_signal.emissions[0]
        assert activity.context == "test"
        assert activity.status == ActivityStatus.COMPLETED

        bridge.stop()

        # register_converter validates signal exists
        bridge2 = TestSignalBridge(mock_event_bus)
        with pytest.raises(ValueError, match="not found"):
            bridge2.register_converter(
                "test.event", TestConverter(), "nonexistent_signal"
            )

        # emit_activity directly emits activity with AI session
        bridge3 = TestSignalBridge(mock_event_bus)
        bridge3.emit_activity(
            description="Test activity",
            entity_type="test",
            entity_id="123",
            status=ActivityStatus.PENDING,
            session_id="ai-session",
        )

        activity_signal = bridge3._signals["activity_logged"]
        assert len(activity_signal.emissions) == 1
        activity = activity_signal.emissions[0]
        assert activity.description == "Test activity"
        assert activity.status == ActivityStatus.PENDING
        assert activity.is_ai_action is True
