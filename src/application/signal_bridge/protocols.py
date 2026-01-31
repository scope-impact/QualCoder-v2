"""
Signal Bridge Protocols - Contracts for event conversion and signal bridging.

These protocols define the interfaces that context-specific bridges implement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from src.application.signal_bridge.payloads import ActivityItem, SignalPayload
    from src.domain.shared.types import DomainEvent


T = TypeVar("T", bound="SignalPayload")
E = TypeVar("E", bound="DomainEvent")


class EventConverter(Protocol[E, T]):
    """
    Protocol for converting domain events to UI payloads.

    Each converter is responsible for transforming a specific domain event
    type into a UI-friendly SignalPayload subclass.

    Type Parameters:
        E: The domain event type to convert from
        T: The signal payload type to convert to

    Example:
        class CodeCreatedConverter:
            def convert(self, event: CodeCreated) -> CodeCreatedPayload:
                return CodeCreatedPayload(
                    timestamp=event.occurred_at,
                    session_id=event.session_id or "local",
                    is_ai_action=event.session_id != "local",
                    event_type="coding.code_created",
                    code_id=event.code_id.value,
                    name=event.name,
                    color=event.color.to_hex(),
                )
    """

    def convert(self, event: E) -> T:
        """
        Convert a domain event to a signal payload.

        Args:
            event: The domain event to convert

        Returns:
            A SignalPayload suitable for UI consumption
        """
        ...


class ActivityFormatter(Protocol):
    """
    Protocol for formatting domain events into activity items.

    Used by bridges to generate human-readable activity feed entries.
    """

    def format(self, event: Any) -> ActivityItem | None:
        """
        Format a domain event into an activity item.

        Args:
            event: The domain event to format

        Returns:
            An ActivityItem for the activity feed, or None if not applicable
        """
        ...


class SignalBridge(Protocol):
    """
    Protocol for signal bridges.

    Signal bridges connect domain events to PySide6 signals,
    enabling reactive UI updates from background operations.
    """

    def start(self) -> None:
        """Start listening to domain events."""
        ...

    def stop(self) -> None:
        """Stop listening and clean up subscriptions."""
        ...

    def is_running(self) -> bool:
        """Check if the bridge is currently listening."""
        ...
