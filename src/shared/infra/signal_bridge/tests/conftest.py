"""Test fixtures for Signal Bridge tests."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest


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
        self._handlers: dict[str, list[Callable]] = {}
        self._all_handlers: list[Callable] = []

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
        import contextlib

        if event_type in self._handlers:
            with contextlib.suppress(ValueError):
                self._handlers[event_type].remove(handler)

    def publish(self, event: Any) -> None:
        """Publish an event to subscribers."""
        event_type = self._get_event_type(event)
        # Notify type-specific handlers
        for handler in self._handlers.get(event_type, []):
            handler(event)
        # Notify all-handlers
        for handler in self._all_handlers:
            handler(event)

    def _get_event_type(self, event: Any) -> str:
        """Get event type string, matching real EventBus logic."""
        # Check for event_type attribute first
        if hasattr(event, "event_type") and event.event_type:
            return event.event_type

        # Generate from module and class name (same as real EventBus)
        event_class = type(event)
        module = event_class.__module__

        # Extract context from module path
        # Handles both old (domain.projects.events) and new (contexts.projects.core.events)
        parts = module.split(".")
        if "contexts" in parts:
            # New structure: src.contexts.projects.core.events -> "projects"
            idx = parts.index("contexts")
            context = parts[idx + 1] if idx + 1 < len(parts) else parts[-1]
        elif "domain" in parts:
            # Old structure: src.domain.projects.events -> "projects"
            idx = parts.index("domain")
            context = parts[idx + 1] if idx + 1 < len(parts) else parts[-1]
        else:
            context = parts[-1] if parts else "unknown"

        # Convert class name from CamelCase to snake_case
        class_name = event_class.__name__
        snake_name = "".join(
            f"_{c.lower()}" if c.isupper() else c for c in class_name
        ).lstrip("_")

        return f"{context}.{snake_name}"

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
