"""
Signal Bridge Payloads - UI-friendly DTOs for signal emission.

These immutable types carry event data from domain events to UI signals.
They are designed for thread-safe emission and UI consumption.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any


class ActivityStatus(Enum):
    """Status for activity feed items."""
    COMPLETED = "completed"
    PENDING = "pending"
    QUEUED = "queued"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(frozen=True)
class SignalPayload:
    """
    Base type for all signal payloads.

    All payloads emitted through the Signal Bridge inherit from this.
    Provides common metadata for UI consumption.

    Attributes:
        timestamp: When the underlying event occurred
        session_id: ID of the session that triggered the event ("local" for human)
        is_ai_action: True if triggered by an AI agent
        event_type: The domain event type string (e.g., "coding.code_created")
    """
    timestamp: datetime
    session_id: str
    is_ai_action: bool
    event_type: str

    @classmethod
    def from_event(
        cls,
        event_type: str,
        occurred_at: datetime,
        session_id: str = "local",
        **kwargs: Any
    ) -> SignalPayload:
        """Create a base payload from event metadata."""
        return cls(
            timestamp=occurred_at,
            session_id=session_id,
            is_ai_action=session_id != "local",
            event_type=event_type,
            **kwargs
        )


@dataclass(frozen=True)
class ActivityItem:
    """
    Activity feed item for logging actions in the UI.

    Used by all Signal Bridges to emit activity updates that
    appear in the Activity Panel.

    Attributes:
        timestamp: When the activity occurred
        session_id: ID of the session that triggered the activity
        description: Human-readable description of what happened
        status: Current status of the activity
        context: Bounded context name (e.g., "coding", "sources")
        entity_type: Type of entity affected (e.g., "code", "segment")
        entity_id: ID of the affected entity (optional)
        is_ai_action: True if triggered by an AI agent
        metadata: Additional context-specific information
    """
    timestamp: datetime
    session_id: str
    description: str
    status: ActivityStatus
    context: str
    entity_type: str
    entity_id: Optional[str] = None
    is_ai_action: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def completed(
        cls,
        description: str,
        context: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        session_id: str = "local",
        metadata: Optional[dict[str, Any]] = None,
    ) -> ActivityItem:
        """Create a completed activity item."""
        return cls(
            timestamp=datetime.utcnow(),
            session_id=session_id,
            description=description,
            status=ActivityStatus.COMPLETED,
            context=context,
            entity_type=entity_type,
            entity_id=entity_id,
            is_ai_action=session_id != "local",
            metadata=metadata or {},
        )

    @classmethod
    def pending(
        cls,
        description: str,
        context: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        session_id: str = "local",
        metadata: Optional[dict[str, Any]] = None,
    ) -> ActivityItem:
        """Create a pending activity item (awaiting approval)."""
        return cls(
            timestamp=datetime.utcnow(),
            session_id=session_id,
            description=description,
            status=ActivityStatus.PENDING,
            context=context,
            entity_type=entity_type,
            entity_id=entity_id,
            is_ai_action=session_id != "local",
            metadata=metadata or {},
        )

    @classmethod
    def failed(
        cls,
        description: str,
        context: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        session_id: str = "local",
        error: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ActivityItem:
        """Create a failed activity item."""
        meta = metadata or {}
        if error:
            meta["error"] = error
        return cls(
            timestamp=datetime.utcnow(),
            session_id=session_id,
            description=description,
            status=ActivityStatus.FAILED,
            context=context,
            entity_type=entity_type,
            entity_id=entity_id,
            is_ai_action=session_id != "local",
            metadata=meta,
        )
