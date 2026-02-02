"""
Cases Signal Bridge - Domain Events to Qt Signals

Converts domain events from the Cases context into Qt signals
for reactive UI updates.

Usage:
    from src.application.cases.signal_bridge import CasesSignalBridge
    from src.application.event_bus import get_event_bus

    bridge = CasesSignalBridge.instance(get_event_bus())
    bridge.case_created.connect(on_case_created)
    bridge.start()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from PySide6.QtCore import Signal

from src.application.signal_bridge.base import BaseSignalBridge
from src.application.signal_bridge.protocols import EventConverter
from src.contexts.cases.core.events import (
    CaseAttributeRemoved,
    CaseAttributeSet,
    CaseCreated,
    CaseRemoved,
    CaseUpdated,
    SourceLinkedToCase,
    SourceUnlinkedFromCase,
)

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
    name: str = ""
    description: str | None = None
    memo: str | None = None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class CaseAttributePayload:
    """Payload for case attribute-related signals."""

    event_type: str
    case_id: int
    attr_name: str
    attr_type: str = ""
    attr_value: Any = None
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
# Converters - Transform events to payloads
# =============================================================================


class CaseCreatedConverter(EventConverter):
    """Convert CaseCreated event to payload."""

    def convert(self, event: CaseCreated) -> CasePayload:
        return CasePayload(
            event_type="cases.case_created",
            case_id=event.case_id.value,
            name=event.name,
            description=event.description,
            memo=event.memo,
        )


class CaseUpdatedConverter(EventConverter):
    """Convert CaseUpdated event to payload."""

    def convert(self, event: CaseUpdated) -> CasePayload:
        return CasePayload(
            event_type="cases.case_updated",
            case_id=event.case_id.value,
            name=event.name,
            description=event.description,
            memo=event.memo,
        )


class CaseRemovedConverter(EventConverter):
    """Convert CaseRemoved event to payload."""

    def convert(self, event: CaseRemoved) -> CasePayload:
        return CasePayload(
            event_type="cases.case_removed",
            case_id=event.case_id.value,
        )


class CaseAttributeSetConverter(EventConverter):
    """Convert CaseAttributeSet event to payload."""

    def convert(self, event: CaseAttributeSet) -> CaseAttributePayload:
        return CaseAttributePayload(
            event_type="cases.attribute_set",
            case_id=event.case_id.value,
            attr_name=event.attr_name,
            attr_type=event.attr_type,
            attr_value=event.attr_value,
        )


class CaseAttributeRemovedConverter(EventConverter):
    """Convert CaseAttributeRemoved event to payload."""

    def convert(self, event: CaseAttributeRemoved) -> CaseAttributePayload:
        return CaseAttributePayload(
            event_type="cases.attribute_removed",
            case_id=event.case_id.value,
            attr_name=event.attr_name,
        )


class SourceLinkedConverter(EventConverter):
    """Convert SourceLinkedToCase event to payload."""

    def convert(self, event: SourceLinkedToCase) -> SourceLinkPayload:
        return SourceLinkPayload(
            event_type="cases.source_linked",
            case_id=event.case_id.value,
            source_id=event.source_id,
        )


class SourceUnlinkedConverter(EventConverter):
    """Convert SourceUnlinkedFromCase event to payload."""

    def convert(self, event: SourceUnlinkedFromCase) -> SourceLinkPayload:
        return SourceLinkPayload(
            event_type="cases.source_unlinked",
            case_id=event.case_id.value,
            source_id=event.source_id,
        )


# =============================================================================
# Signal Bridge
# =============================================================================


class CasesSignalBridge(BaseSignalBridge):
    """
    Signal bridge for the Cases bounded context.

    Emits Qt signals when domain events occur, enabling reactive UI updates.

    Signals:
        case_created: Emitted when a new case is created
        case_updated: Emitted when a case is updated
        case_removed: Emitted when a case is removed
        attribute_set: Emitted when a case attribute is set
        attribute_removed: Emitted when a case attribute is removed
        source_linked: Emitted when a source is linked to a case
        source_unlinked: Emitted when a source is unlinked from a case

    Usage:
        bridge = CasesSignalBridge.instance(event_bus)
        bridge.case_created.connect(self._on_case_created)
        bridge.start()
    """

    # Case lifecycle signals
    case_created = Signal(object)
    case_updated = Signal(object)
    case_removed = Signal(object)

    # Attribute signals
    attribute_set = Signal(object)
    attribute_removed = Signal(object)

    # Source link signals
    source_linked = Signal(object)
    source_unlinked = Signal(object)

    def _get_context_name(self) -> str:
        """Return the bounded context name."""
        return "cases"

    def _register_converters(self) -> None:
        """Register all event converters."""
        # Case lifecycle events
        self.register_converter(
            "cases.case_created", CaseCreatedConverter(), "case_created"
        )
        self.register_converter(
            "cases.case_updated", CaseUpdatedConverter(), "case_updated"
        )
        self.register_converter(
            "cases.case_removed", CaseRemovedConverter(), "case_removed"
        )

        # Attribute events
        self.register_converter(
            "cases.attribute_set", CaseAttributeSetConverter(), "attribute_set"
        )
        self.register_converter(
            "cases.attribute_removed",
            CaseAttributeRemovedConverter(),
            "attribute_removed",
        )

        # Source link events
        self.register_converter(
            "cases.source_linked", SourceLinkedConverter(), "source_linked"
        )
        self.register_converter(
            "cases.source_unlinked", SourceUnlinkedConverter(), "source_unlinked"
        )
