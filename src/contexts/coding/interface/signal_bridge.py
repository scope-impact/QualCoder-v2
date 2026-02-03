"""
Coding Signal Bridge - Domain Events to Qt Signals

Converts domain events from the Coding context into Qt signals
for reactive UI updates.

Usage:
    from src.contexts.coding.interface.signal_bridge import CodingSignalBridge
    from src.shared.infra.event_bus import get_event_bus

    bridge = CodingSignalBridge.instance(get_event_bus())
    bridge.code_created.connect(on_code_created)
    bridge.start()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from PySide6.QtCore import Signal

from src.contexts.coding.core.events import (
    CategoryCreated,
    CategoryDeleted,
    CodeColorChanged,
    CodeCreated,
    CodeDeleted,
    CodeMemoUpdated,
    CodeRenamed,
    CodesMerged,
    SegmentCoded,
    SegmentUncoded,
)
from src.shared.infra.signal_bridge.base import BaseSignalBridge, EventConverter

# =============================================================================
# Payloads - Data transferred via signals
# =============================================================================


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class CodePayload:
    """Payload for code-related signals."""

    event_type: str
    code_id: int
    name: str
    color: str
    memo: str | None = None
    category_id: int | None = None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class CategoryPayload:
    """Payload for category-related signals."""

    event_type: str
    category_id: int
    name: str
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class SegmentPayload:
    """Payload for segment-related signals."""

    event_type: str
    segment_id: int
    code_id: int
    source_id: int
    start_pos: int
    end_pos: int
    text: str | None = None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


# =============================================================================
# Event Converters
# =============================================================================


class CodeCreatedConverter(EventConverter[CodeCreated, CodePayload]):
    """Convert CodeCreated event to CodePayload."""

    def convert(self, event: CodeCreated) -> CodePayload:
        return CodePayload(
            event_type="code_created",
            code_id=event.code_id,
            name=event.name,
            color=event.color,
            category_id=getattr(event, "category_id", None),
        )


class CodeDeletedConverter(EventConverter[CodeDeleted, CodePayload]):
    """Convert CodeDeleted event to CodePayload."""

    def convert(self, event: CodeDeleted) -> CodePayload:
        return CodePayload(
            event_type="code_deleted",
            code_id=event.code_id,
            name=getattr(event, "name", ""),
            color=getattr(event, "color", ""),
        )


class CodeRenamedConverter(EventConverter[CodeRenamed, CodePayload]):
    """Convert CodeRenamed event to CodePayload."""

    def convert(self, event: CodeRenamed) -> CodePayload:
        return CodePayload(
            event_type="code_renamed",
            code_id=event.code_id,
            name=event.new_name,
            color=getattr(event, "color", ""),
        )


class CodeColorChangedConverter(EventConverter[CodeColorChanged, CodePayload]):
    """Convert CodeColorChanged event to CodePayload."""

    def convert(self, event: CodeColorChanged) -> CodePayload:
        return CodePayload(
            event_type="code_color_changed",
            code_id=event.code_id,
            name=getattr(event, "name", ""),
            color=event.new_color,
        )


class CodeMemoUpdatedConverter(EventConverter[CodeMemoUpdated, CodePayload]):
    """Convert CodeMemoUpdated event to CodePayload."""

    def convert(self, event: CodeMemoUpdated) -> CodePayload:
        return CodePayload(
            event_type="code_memo_updated",
            code_id=event.code_id,
            name=getattr(event, "name", ""),
            color=getattr(event, "color", ""),
            memo=event.new_memo,
        )


@dataclass(frozen=True)
class CodesMergedPayload:
    """Payload for codes merged signal."""

    event_type: str
    source_code_id: int
    target_code_id: int
    segments_moved: int
    timestamp: datetime = field(default_factory=_now)


class CodesMergedConverter(EventConverter[CodesMerged, CodesMergedPayload]):
    """Convert CodesMerged event to CodesMergedPayload."""

    def convert(self, event: CodesMerged) -> CodesMergedPayload:
        return CodesMergedPayload(
            event_type="codes_merged",
            source_code_id=event.source_code_id.value,
            target_code_id=event.target_code_id.value,
            segments_moved=event.segments_moved,
        )


class CategoryCreatedConverter(EventConverter[CategoryCreated, CategoryPayload]):
    """Convert CategoryCreated event to CategoryPayload."""

    def convert(self, event: CategoryCreated) -> CategoryPayload:
        return CategoryPayload(
            event_type="category_created",
            category_id=event.category_id,
            name=event.name,
        )


class CategoryDeletedConverter(EventConverter[CategoryDeleted, CategoryPayload]):
    """Convert CategoryDeleted event to CategoryPayload."""

    def convert(self, event: CategoryDeleted) -> CategoryPayload:
        return CategoryPayload(
            event_type="category_deleted",
            category_id=event.category_id,
            name=getattr(event, "name", ""),
        )


class SegmentCodedConverter(EventConverter[SegmentCoded, SegmentPayload]):
    """Convert SegmentCoded event to SegmentPayload."""

    def convert(self, event: SegmentCoded) -> SegmentPayload:
        return SegmentPayload(
            event_type="segment_coded",
            segment_id=event.segment_id.value
            if hasattr(event.segment_id, "value")
            else int(event.segment_id),
            code_id=event.code_id.value
            if hasattr(event.code_id, "value")
            else int(event.code_id),
            source_id=event.source_id.value
            if hasattr(event.source_id, "value")
            else int(event.source_id),
            start_pos=event.position.start,
            end_pos=event.position.end,
            text=event.selected_text,
        )


class SegmentUncodedConverter(EventConverter[SegmentUncoded, SegmentPayload]):
    """Convert SegmentUncoded event to SegmentPayload."""

    def convert(self, event: SegmentUncoded) -> SegmentPayload:
        return SegmentPayload(
            event_type="segment_uncoded",
            segment_id=event.segment_id.value
            if hasattr(event.segment_id, "value")
            else int(event.segment_id),
            code_id=event.code_id.value
            if hasattr(event.code_id, "value")
            else int(event.code_id),
            source_id=event.source_id.value
            if hasattr(event.source_id, "value")
            else int(event.source_id),
            start_pos=0,
            end_pos=0,
        )


# =============================================================================
# Coding Signal Bridge
# =============================================================================


class CodingSignalBridge(BaseSignalBridge):
    """
    Signal bridge for the Coding context.

    Converts coding domain events into Qt signals for UI updates.
    """

    # Code signals
    code_created = Signal(object)
    code_deleted = Signal(object)
    code_renamed = Signal(object)
    code_color_changed = Signal(object)
    code_memo_updated = Signal(object)
    code_moved = Signal(object)
    codes_merged = Signal(object)

    # Category signals
    category_created = Signal(object)
    category_deleted = Signal(object)

    # Segment signals
    segment_coded = Signal(object)
    segment_uncoded = Signal(object)

    def _get_context_name(self) -> str:
        """Return the context name for activity logging."""
        return "coding"

    def _register_converters(self) -> None:
        """Register event converters for coding domain events."""
        # Code events
        self.register_converter(
            "coding.code_created",
            CodeCreatedConverter(),
            "code_created",
        )
        self.register_converter(
            "coding.code_deleted",
            CodeDeletedConverter(),
            "code_deleted",
        )
        self.register_converter(
            "coding.code_renamed",
            CodeRenamedConverter(),
            "code_renamed",
        )
        self.register_converter(
            "coding.code_color_changed",
            CodeColorChangedConverter(),
            "code_color_changed",
        )
        self.register_converter(
            "coding.code_memo_updated",
            CodeMemoUpdatedConverter(),
            "code_memo_updated",
        )
        self.register_converter(
            "coding.codes_merged",
            CodesMergedConverter(),
            "codes_merged",
        )

        # Category events
        self.register_converter(
            "coding.category_created",
            CategoryCreatedConverter(),
            "category_created",
        )
        self.register_converter(
            "coding.category_deleted",
            CategoryDeletedConverter(),
            "category_deleted",
        )

        # Segment events
        self.register_converter(
            "coding.segment_coded",
            SegmentCodedConverter(),
            "segment_coded",
        )
        self.register_converter(
            "coding.segment_uncoded",
            SegmentUncodedConverter(),
            "segment_uncoded",
        )
