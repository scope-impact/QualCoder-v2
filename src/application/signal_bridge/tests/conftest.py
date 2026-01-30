"""Test fixtures for Signal Bridge tests."""

import pytest
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List


@dataclass(frozen=True)
class MockDomainEvent:
    """Mock domain event for testing."""
    event_id: str
    occurred_at: datetime
    event_type: str = "test.event"
    data: str = "test data"


class MockEventBus:
    """Mock event bus for testing signal bridge subscriptions."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._all_handlers: List[Callable] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to events of a specific type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: Callable) -> None:
        """Subscribe to all events."""
        self._all_handlers.append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from events of a specific type."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass

    def publish(self, event: Any) -> None:
        """Publish an event to subscribers."""
        event_type = getattr(event, 'event_type', type(event).__name__)
        # Notify type-specific handlers
        for handler in self._handlers.get(event_type, []):
            handler(event)
        # Notify all-handlers
        for handler in self._all_handlers:
            handler(event)

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._handlers.clear()
        self._all_handlers.clear()

    def get_handler_count(self, event_type: str) -> int:
        """Get number of handlers for an event type."""
        return len(self._handlers.get(event_type, []))


@pytest.fixture
def mock_event_bus() -> MockEventBus:
    """Provide a mock event bus for testing."""
    return MockEventBus()


@pytest.fixture
def sample_event() -> MockDomainEvent:
    """Provide a sample domain event."""
    return MockDomainEvent(
        event_id="test-123",
        occurred_at=datetime(2026, 1, 29, 12, 0, 0),
        event_type="test.sample_event",
        data="sample data",
    )
