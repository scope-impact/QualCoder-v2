"""
Simplified EventBus for Flet POC.

This is a minimal version of the QualCoder EventBus to demonstrate
how domain events integrate with Flet UI updates.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Coding Domain Events
@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    """Event emitted when a new code is created."""

    code_id: int = 0
    name: str = ""
    color: str = "#3d7a63"


@dataclass(frozen=True)
class CodeDeleted(DomainEvent):
    """Event emitted when a code is deleted."""

    code_id: int = 0
    name: str = ""


@dataclass(frozen=True)
class SegmentCoded(DomainEvent):
    """Event emitted when text is coded."""

    segment_id: int = 0
    code_id: int = 0
    code_name: str = ""
    source_name: str = ""
    text_preview: str = ""


@dataclass(frozen=True)
class SourceImported(DomainEvent):
    """Event emitted when a source file is imported."""

    source_id: int = 0
    name: str = ""
    word_count: int = 0


class Subscription:
    """Handle for unsubscribing from events."""

    def __init__(self, event_bus: "EventBus", event_type: str, handler: Callable):
        self._event_bus = event_bus
        self._event_type = event_type
        self._handler = handler
        self._active = True

    def cancel(self) -> None:
        """Unsubscribe from the event."""
        if self._active:
            self._event_bus.unsubscribe(self._event_type, self._handler)
            self._active = False


class EventBus:
    """
    Simple pub/sub event bus.

    In the real QualCoder, this is thread-safe with history tracking.
    This is a simplified version for the POC.
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> Subscription:
        """Subscribe to events of a specific type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        return Subscription(self, event_type, handler)

    def subscribe_type(self, event_class: type, handler: Callable) -> Subscription:
        """Subscribe to events by class type."""
        event_type = self._get_event_type(event_class)
        return self.subscribe(event_type, handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass

    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribers."""
        event_type = self._get_event_type(type(event))
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")

    def _get_event_type(self, event_class: type) -> str:
        """Get the event type string for a class."""
        # Convert CamelCase to snake_case
        name = event_class.__name__
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result)
