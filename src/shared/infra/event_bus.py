"""
Event Bus - Domain Event Pub/Sub Infrastructure

The backbone of the Functional DDD architecture, enabling decoupled
communication between bounded contexts and reactive UI updates.

Usage:
    from src.shared.infra.event_bus import EventBus, Subscription

    bus = EventBus()

    # Subscribe by event type string
    sub = bus.subscribe("coding.code_created", handle_code_created)

    # Subscribe by event class
    sub = bus.subscribe_type(CodeCreated, handle_code_created)

    # Publish events
    bus.publish(CodeCreated(...))

    # Cleanup
    sub.cancel()
"""

from __future__ import annotations

import contextlib
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import (
    Any,
    TypeVar,
)
from weakref import ReferenceType, ref

E = TypeVar("E")
Handler = Callable[[Any], None]


@dataclass
class Subscription:
    """
    Handle for managing a subscription.

    Use cancel() to remove the subscription, or let it be
    garbage collected if using weak references.
    """

    _event_bus: ReferenceType[EventBus]
    _event_type: str
    _handler: Handler
    _is_active: bool = True

    def cancel(self) -> None:
        """Cancel this subscription."""
        if not self._is_active:
            return

        bus = self._event_bus()
        if bus is not None:
            bus.unsubscribe(self._event_type, self._handler)
        self._is_active = False

    @property
    def is_active(self) -> bool:
        """Check if subscription is still active."""
        return self._is_active

    def __enter__(self) -> Subscription:
        return self

    def __exit__(self, *args: Any) -> None:
        self.cancel()


@dataclass
class EventRecord:
    """Record of a published event for debugging."""

    event: Any
    event_type: str
    timestamp: datetime
    handler_count: int


class EventBus:
    """
    Simple synchronous event bus for domain events.

    Thread-safe for publishing from background threads.
    Handlers are invoked synchronously in the publishing thread.

    Features:
    - Subscribe by string type or event class
    - Subscribe to all events
    - Optional event history for debugging
    - Subscription handles for easy cleanup
    """

    def __init__(self, history_size: int = 0) -> None:
        """
        Initialize the event bus.

        Args:
            history_size: Number of recent events to keep (0 to disable)
        """
        self._lock = RLock()

        # Handlers by event type string
        self._handlers: dict[str, list[Handler]] = {}

        # Handlers for all events
        self._all_handlers: list[Handler] = []

        # Class to string mapping cache
        self._type_cache: dict[type, str] = {}

        # Event history (circular buffer)
        self._history_size = history_size
        self._history: list[EventRecord] = []

    def subscribe(
        self,
        event_type: str,
        handler: Handler,
    ) -> Subscription:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Event type string (e.g., "coding.code_created")
            handler: Callback function to invoke

        Returns:
            Subscription handle for cancellation
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []

            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)

        return Subscription(
            _event_bus=ref(self),
            _event_type=event_type,
            _handler=handler,
        )

    def subscribe_type(
        self,
        event_class: type[E],
        handler: Callable[[E], None],
    ) -> Subscription:
        """
        Subscribe to events by their class type.

        The event type string is derived from the class:
        - If class has 'event_type' attribute, use that
        - Otherwise, use "{module}.{class_name}" format

        Args:
            event_class: The event class to subscribe to
            handler: Callback function to invoke

        Returns:
            Subscription handle for cancellation
        """
        event_type = self._get_type_string(event_class)
        return self.subscribe(event_type, handler)

    def subscribe_all(self, handler: Handler) -> Subscription:
        """
        Subscribe to all events.

        Args:
            handler: Callback function to invoke for every event

        Returns:
            Subscription handle for cancellation
        """
        with self._lock:
            if handler not in self._all_handlers:
                self._all_handlers.append(handler)

        return Subscription(
            _event_bus=ref(self),
            _event_type="*",
            _handler=handler,
        )

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        """
        Remove a subscription.

        Args:
            event_type: Event type string (use "*" for all-handlers)
            handler: The handler to remove
        """
        with self._lock:
            if event_type == "*":
                with contextlib.suppress(ValueError):
                    self._all_handlers.remove(handler)
            elif event_type in self._handlers:
                with contextlib.suppress(ValueError):
                    self._handlers[event_type].remove(handler)

    def publish(self, event: Any) -> None:
        """
        Publish an event to all matching subscribers.

        Thread-safe. Handlers are invoked synchronously.

        Args:
            event: The domain event to publish
        """
        event_type = self._get_event_type(event)

        with self._lock:
            # Get copies of handler lists to avoid modification during iteration
            type_handlers = list(self._handlers.get(event_type, []))
            all_handlers = list(self._all_handlers)

        handler_count = len(type_handlers) + len(all_handlers)

        # Record in history if enabled
        if self._history_size > 0:
            self._record_event(event, event_type, handler_count)

        # Invoke type-specific handlers
        for handler in type_handlers:
            try:
                handler(event)
            except Exception as e:
                warnings.warn(
                    f"Handler error for {event_type}: {e}",
                    RuntimeWarning,
                    stacklevel=2,
                )

        # Invoke all-handlers
        for handler in all_handlers:
            try:
                handler(event)
            except Exception as e:
                warnings.warn(
                    f"All-handler error for {event_type}: {e}",
                    RuntimeWarning,
                    stacklevel=2,
                )

    def clear(self) -> None:
        """Remove all subscriptions."""
        with self._lock:
            self._handlers.clear()
            self._all_handlers.clear()

    def clear_for_handler(self, handler: Handler) -> int:
        """
        Remove all subscriptions for a specific handler.

        Args:
            handler: The handler to remove

        Returns:
            Number of subscriptions removed
        """
        count = 0
        with self._lock:
            # Remove from type-specific handlers
            for handlers in self._handlers.values():
                while handler in handlers:
                    handlers.remove(handler)
                    count += 1

            # Remove from all-handlers
            while handler in self._all_handlers:
                self._all_handlers.remove(handler)
                count += 1

        return count

    def handler_count(self, event_type: str | None = None) -> int:
        """
        Get the number of handlers.

        Args:
            event_type: Specific event type, or None for total count

        Returns:
            Number of handlers
        """
        with self._lock:
            if event_type is None:
                return sum(len(h) for h in self._handlers.values()) + len(
                    self._all_handlers
                )
            elif event_type == "*":
                return len(self._all_handlers)
            else:
                return len(self._handlers.get(event_type, []))

    def event_types(self) -> list[str]:
        """
        Get list of event types with active subscriptions.

        Returns:
            List of event type strings
        """
        with self._lock:
            return [t for t, h in self._handlers.items() if h]

    def get_history(self) -> list[EventRecord]:
        """
        Get the event history.

        Returns:
            List of recent event records (newest last)
        """
        with self._lock:
            return list(self._history)

    def clear_history(self) -> None:
        """Clear the event history."""
        with self._lock:
            self._history.clear()

    def _get_event_type(self, event: Any) -> str:
        """Get the event type string from an event instance."""
        # Check for event_type attribute
        if hasattr(event, "event_type"):
            return event.event_type

        # Fall back to class-based type
        return self._get_type_string(type(event))

    def _get_type_string(self, event_class: type) -> str:
        """Get the event type string from an event class."""
        # Check cache
        if event_class in self._type_cache:
            return self._type_cache[event_class]

        # Check for class-level event_type
        if hasattr(event_class, "event_type"):
            type_str = event_class.event_type
            if isinstance(type_str, str):
                self._type_cache[event_class] = type_str
                return type_str

        # Deprecation warning for missing explicit event_type
        warnings.warn(
            f"Event class '{event_class.__name__}' is missing an explicit "
            f"event_type ClassVar. Auto-generating event type is deprecated. "
            f"Add: event_type: ClassVar[str] = 'context.{event_class.__name__.lower()}'",
            DeprecationWarning,
            stacklevel=3,
        )

        # Generate from module and class name (deprecated fallback)
        module = event_class.__module__
        # Extract context from module path
        # Handles both old (domain.coding.events) and new (contexts.coding.core.events)
        parts = module.split(".")
        if "contexts" in parts:
            # New structure: src.contexts.coding.core.events -> "coding"
            idx = parts.index("contexts")
            context = parts[idx + 1] if idx + 1 < len(parts) else parts[-1]
        elif "domain" in parts:
            # Old structure: src.domain.coding.events -> "coding"
            idx = parts.index("domain")
            context = parts[idx + 1] if idx + 1 < len(parts) else parts[-1]
        else:
            context = parts[-1] if parts else "unknown"

        # Convert class name from CamelCase to snake_case
        class_name = event_class.__name__
        snake_name = "".join(
            f"_{c.lower()}" if c.isupper() else c for c in class_name
        ).lstrip("_")

        type_str = f"{context}.{snake_name}"
        self._type_cache[event_class] = type_str
        return type_str

    def _record_event(
        self,
        event: Any,
        event_type: str,
        handler_count: int,
    ) -> None:
        """Record an event in history."""
        with self._lock:
            record = EventRecord(
                event=event,
                event_type=event_type,
                timestamp=datetime.now(UTC),
                handler_count=handler_count,
            )
            self._history.append(record)

            # Trim to size limit
            while len(self._history) > self._history_size:
                self._history.pop(0)


# Singleton instance (optional usage pattern)
_default_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    Get the default event bus instance.

    Creates one if it doesn't exist.
    """
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


def reset_event_bus() -> None:
    """Reset the default event bus (for testing)."""
    global _default_bus
    if _default_bus is not None:
        _default_bus.clear()
    _default_bus = None
