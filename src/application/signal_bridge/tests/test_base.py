"""Tests for BaseSignalBridge class."""

import pytest
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from src.application.signal_bridge.base import BaseSignalBridge
from src.application.signal_bridge.payloads import SignalPayload, ActivityStatus
from src.application.signal_bridge.protocols import EventConverter
from src.application.signal_bridge.tests.conftest import MockEventBus, MockDomainEvent


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

    def __call__(self, *args: Any) -> 'MockSignal':
        return self


class TestBaseSignalBridge:
    """Tests for BaseSignalBridge class."""

    def test_singleton_pattern(self, mock_event_bus: MockEventBus) -> None:
        """Test that instance() returns singleton."""
        # Clear any existing instances
        TestSignalBridge.clear_instance()

        bridge1 = TestSignalBridge.instance(mock_event_bus)
        bridge2 = TestSignalBridge.instance()

        assert bridge1 is bridge2

        # Cleanup
        TestSignalBridge.clear_instance()

    def test_singleton_requires_event_bus_first_call(self) -> None:
        """Test that first instance() call requires event_bus."""
        TestSignalBridge.clear_instance()

        with pytest.raises(ValueError, match="requires event_bus"):
            TestSignalBridge.instance()

    def test_start_subscribes_to_events(self, mock_event_bus: MockEventBus) -> None:
        """Test that start() subscribes to registered event types."""
        bridge = TestSignalBridge(mock_event_bus)

        assert mock_event_bus.get_handler_count("test.sample_event") == 0

        bridge.start()

        assert mock_event_bus.get_handler_count("test.sample_event") == 1
        assert bridge.is_running() is True

    def test_stop_unsubscribes_from_events(self, mock_event_bus: MockEventBus) -> None:
        """Test that stop() unsubscribes from events."""
        bridge = TestSignalBridge(mock_event_bus)
        bridge.start()

        assert bridge.is_running() is True

        bridge.stop()

        assert bridge.is_running() is False
        assert mock_event_bus.get_handler_count("test.sample_event") == 0

    def test_context_manager(self, mock_event_bus: MockEventBus) -> None:
        """Test context manager protocol."""
        bridge = TestSignalBridge(mock_event_bus)

        with bridge:
            assert bridge.is_running() is True

        assert bridge.is_running() is False

    def test_event_dispatch_converts_and_emits(
        self,
        mock_event_bus: MockEventBus,
        sample_event: MockDomainEvent,
    ) -> None:
        """Test that events are converted and emitted."""
        bridge = TestSignalBridge(mock_event_bus)
        bridge.start()

        # Publish event
        mock_event_bus.publish(sample_event)

        # Check signal was emitted
        signal = bridge.test_event_signal
        assert len(signal.emissions) == 1

        payload = signal.emissions[0]
        assert isinstance(payload, TestPayload)
        assert payload.data == "sample data"
        assert payload.event_type == "test.sample_event"

    def test_activity_logged_on_event(
        self,
        mock_event_bus: MockEventBus,
        sample_event: MockDomainEvent,
    ) -> None:
        """Test that activity is logged when events are dispatched."""
        bridge = TestSignalBridge(mock_event_bus)
        bridge.start()

        mock_event_bus.publish(sample_event)

        # Check activity was logged
        activity_signal = bridge._signals["activity_logged"]
        assert len(activity_signal.emissions) == 1

        activity = activity_signal.emissions[0]
        assert activity.context == "test"
        assert activity.status == ActivityStatus.COMPLETED

    def test_register_converter_validates_signal(
        self,
        mock_event_bus: MockEventBus,
    ) -> None:
        """Test that register_converter validates signal exists."""
        bridge = TestSignalBridge(mock_event_bus)

        with pytest.raises(ValueError, match="not found"):
            bridge.register_converter(
                "test.event",
                TestConverter(),
                "nonexistent_signal",
            )

    def test_emit_activity_directly(self, mock_event_bus: MockEventBus) -> None:
        """Test emitting activity directly without event."""
        bridge = TestSignalBridge(mock_event_bus)

        bridge.emit_activity(
            description="Test activity",
            entity_type="test",
            entity_id="123",
            status=ActivityStatus.PENDING,
            session_id="ai-session",
        )

        activity_signal = bridge._signals["activity_logged"]
        assert len(activity_signal.emissions) == 1

        activity = activity_signal.emissions[0]
        assert activity.description == "Test activity"
        assert activity.status == ActivityStatus.PENDING
        assert activity.is_ai_action is True

    def test_double_start_is_safe(self, mock_event_bus: MockEventBus) -> None:
        """Test that calling start() twice is safe."""
        bridge = TestSignalBridge(mock_event_bus)
        bridge.start()
        bridge.start()  # Should not raise or double-subscribe

        assert mock_event_bus.get_handler_count("test.sample_event") == 1

    def test_double_stop_is_safe(self, mock_event_bus: MockEventBus) -> None:
        """Test that calling stop() twice is safe."""
        bridge = TestSignalBridge(mock_event_bus)
        bridge.start()
        bridge.stop()
        bridge.stop()  # Should not raise

        assert bridge.is_running() is False
