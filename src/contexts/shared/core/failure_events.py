"""
Shared Domain: Base Failure Event

Failure events are publishable domain events that represent failed operations.
Unlike simple error types, failure events can be published to the event bus
and trigger policies/reactions.

Event naming convention: {ENTITY}_NOT_{OPERATION}/{REASON}
Examples:
    - PROJECT_NOT_CREATED/EMPTY_NAME
    - SOURCE_NOT_ADDED/DUPLICATE_NAME
    - CODE_NOT_CREATED/INVALID_COLOR
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True)
class FailureEvent:
    """
    Base class for publishable failure events.

    Failure events differ from simple error types in that:
    1. They have event_id and occurred_at for traceability
    2. They can be published to the event bus
    3. They can trigger policies (e.g., retry, notification)
    4. They follow the same immutable pattern as success events

    The event_type uses format: {ENTITY}_NOT_{OPERATION}/{REASON}
    This allows:
    - Filtering by operation: event_type.startswith("PROJECT_NOT_CREATED")
    - Filtering by reason: event_type.endswith("/EMPTY_NAME")
    - Grouping by entity: event_type.split("_NOT_")[0]
    """

    event_id: str
    occurred_at: datetime
    event_type: str

    @property
    def is_failure(self) -> bool:
        """Always True for failure events."""
        return True

    @property
    def operation(self) -> str:
        """Extract the operation from event_type (e.g., PROJECT_NOT_CREATED)."""
        return self.event_type.split("/")[0]

    @property
    def reason(self) -> str:
        """Extract the reason from event_type (e.g., EMPTY_NAME)."""
        parts = self.event_type.split("/")
        return parts[1] if len(parts) > 1 else ""

    @property
    def message(self) -> str:
        """Human-readable error message. Subclasses should override."""
        return self.event_type.replace("_", " ").replace("/", ": ").title()

    @classmethod
    def _generate_id(cls) -> str:
        """Generate a unique event ID."""
        return str(uuid4())

    @classmethod
    def _now(cls) -> datetime:
        """Get current UTC timestamp."""
        return datetime.now(UTC)


# Type alias for any failure event
AnyFailureEvent = FailureEvent
