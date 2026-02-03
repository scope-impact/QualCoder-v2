"""
Cases Signal Bridge - Domain Events to Qt Signals

Converts domain events from the Cases context into Qt signals
for reactive UI updates.

Usage:
    from src.contexts.cases.interface.signal_bridge import CasesSignalBridge
    from src.shared.infra.event_bus import get_event_bus

    bridge = CasesSignalBridge.instance(get_event_bus())
    bridge.case_created.connect(on_case_created)
    bridge.start()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from PySide6.QtCore import Signal

from src.contexts.cases.core.events import (
    CaseAttributeRemoved,
    CaseAttributeSet,
    CaseCreated,
    CaseRemoved,
    CaseUpdated,
    SourceLinkedToCase,
    SourceUnlinkedFromCase,
)
from src.shared.infra.signal_bridge.base import BaseSignalBridge, EventConverter

# =============================================================================
# Payloads - Data transferred via signals
# =============================================================================


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class CasePayload:
    """Payload for case-related signals."""

    event_type: str
    case_id: int
    name: str
    description: str | None = None
    memo: str | None = None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class CaseAttributePayload:
    """Payload for case attribute signals."""

    event_type: str
    case_id: int
    attribute_name: str
    attribute_type: str
    value: str | int | float | bool | None = None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class SourceLinkPayload:
    """Payload for source link/unlink signals."""

    event_type: str
    case_id: int
    source_id: int
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


# =============================================================================
# Event Converters
# =============================================================================


class CaseCreatedConverter(EventConverter[CaseCreated, CasePayload]):
    """Convert CaseCreated event to CasePayload."""

    def convert(self, event: CaseCreated) -> CasePayload:
        return CasePayload(
            event_type="case_created",
            case_id=event.case_id.value
            if hasattr(event.case_id, "value")
            else int(event.case_id),
            name=event.name,
            description=getattr(event, "description", None),
            memo=getattr(event, "memo", None),
        )


class CaseUpdatedConverter(EventConverter[CaseUpdated, CasePayload]):
    """Convert CaseUpdated event to CasePayload."""

    def convert(self, event: CaseUpdated) -> CasePayload:
        return CasePayload(
            event_type="case_updated",
            case_id=event.case_id.value
            if hasattr(event.case_id, "value")
            else int(event.case_id),
            name=getattr(event, "name", ""),
            description=getattr(event, "new_description", None),
            memo=getattr(event, "new_memo", None),
        )


class CaseRemovedConverter(EventConverter[CaseRemoved, CasePayload]):
    """Convert CaseRemoved event to CasePayload."""

    def convert(self, event: CaseRemoved) -> CasePayload:
        return CasePayload(
            event_type="case_removed",
            case_id=event.case_id.value
            if hasattr(event.case_id, "value")
            else int(event.case_id),
            name="",
        )


class CaseAttributeSetConverter(EventConverter[CaseAttributeSet, CaseAttributePayload]):
    """Convert CaseAttributeSet event to CaseAttributePayload."""

    def convert(self, event: CaseAttributeSet) -> CaseAttributePayload:
        return CaseAttributePayload(
            event_type="case_attribute_set",
            case_id=event.case_id.value
            if hasattr(event.case_id, "value")
            else int(event.case_id),
            attribute_name=event.attr_name,
            attribute_type=str(event.attr_type),
            value=event.attr_value,
        )


class CaseAttributeRemovedConverter(
    EventConverter[CaseAttributeRemoved, CaseAttributePayload]
):
    """Convert CaseAttributeRemoved event to CaseAttributePayload."""

    def convert(self, event: CaseAttributeRemoved) -> CaseAttributePayload:
        return CaseAttributePayload(
            event_type="case_attribute_removed",
            case_id=event.case_id.value
            if hasattr(event.case_id, "value")
            else int(event.case_id),
            attribute_name=event.attr_name,
            attribute_type="",
        )


class SourceLinkedConverter(EventConverter[SourceLinkedToCase, SourceLinkPayload]):
    """Convert SourceLinkedToCase event to SourceLinkPayload."""

    def convert(self, event: SourceLinkedToCase) -> SourceLinkPayload:
        return SourceLinkPayload(
            event_type="source_linked",
            case_id=event.case_id.value
            if hasattr(event.case_id, "value")
            else int(event.case_id),
            source_id=event.source_id.value
            if hasattr(event.source_id, "value")
            else int(event.source_id),
        )


class SourceUnlinkedConverter(
    EventConverter[SourceUnlinkedFromCase, SourceLinkPayload]
):
    """Convert SourceUnlinkedFromCase event to SourceLinkPayload."""

    def convert(self, event: SourceUnlinkedFromCase) -> SourceLinkPayload:
        return SourceLinkPayload(
            event_type="source_unlinked",
            case_id=event.case_id.value
            if hasattr(event.case_id, "value")
            else int(event.case_id),
            source_id=event.source_id.value
            if hasattr(event.source_id, "value")
            else int(event.source_id),
        )


# =============================================================================
# Cases Signal Bridge
# =============================================================================


class CasesSignalBridge(BaseSignalBridge):
    """
    Signal bridge for the Cases context.

    Converts cases domain events into Qt signals for UI updates.
    """

    # Case signals
    case_created = Signal(object)
    case_updated = Signal(object)
    case_removed = Signal(object)

    # Attribute signals
    case_attribute_set = Signal(object)
    case_attribute_removed = Signal(object)

    # Link signals
    source_linked = Signal(object)
    source_unlinked = Signal(object)

    def _get_context_name(self) -> str:
        """Return the context name for activity logging."""
        return "cases"

    def _register_converters(self) -> None:
        """Register event converters for cases domain events."""
        # Case events
        self.register_converter(
            "cases.case_created",
            CaseCreatedConverter(),
            "case_created",
        )
        self.register_converter(
            "cases.case_updated",
            CaseUpdatedConverter(),
            "case_updated",
        )
        self.register_converter(
            "cases.case_removed",
            CaseRemovedConverter(),
            "case_removed",
        )

        # Attribute events
        self.register_converter(
            "cases.attribute_set",
            CaseAttributeSetConverter(),
            "case_attribute_set",
        )
        self.register_converter(
            "cases.attribute_removed",
            CaseAttributeRemovedConverter(),
            "case_attribute_removed",
        )

        # Link events
        self.register_converter(
            "cases.source_linked",
            SourceLinkedConverter(),
            "source_linked",
        )
        self.register_converter(
            "cases.source_unlinked",
            SourceUnlinkedConverter(),
            "source_unlinked",
        )
