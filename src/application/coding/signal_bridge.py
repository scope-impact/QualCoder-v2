"""
Coding Signal Bridge - Domain Events to Qt Signals

Converts domain events from the Coding context into Qt signals
for reactive UI updates.

Usage:
    from src.application.coding.signal_bridge import CodingSignalBridge
    from src.application.event_bus import get_event_bus

    bridge = CodingSignalBridge.instance(get_event_bus())
    bridge.code_created.connect(on_code_created)
    bridge.start()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from PySide6.QtCore import Signal

from src.application.signal_bridge.base import BaseSignalBridge
from src.application.signal_bridge.protocols import EventConverter
from src.domain.coding.events import (
    CategoryCreated,
    CategoryDeleted,
    CategoryRenamed,
    CodeColorChanged,
    CodeCreated,
    CodeDeleted,
    CodeMemoUpdated,
    CodeMovedToCategory,
    CodeRenamed,
    CodesMerged,
    SegmentCoded,
    SegmentMemoUpdated,
    SegmentUncoded,
)

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
    code_name: str
    color: str | None = None
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
    category_name: str
    parent_id: int | None = None
    memo: str | None = None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class SegmentPayload:
    """Payload for segment-related signals."""

    event_type: str
    segment_id: int
    code_id: int
    code_name: str
    source_id: int
    source_name: str
    start: int
    end: int
    selected_text: str
    memo: str | None = None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class CodeMergePayload:
    """Payload for code merge signals."""

    event_type: str
    source_code_id: int
    source_code_name: str
    target_code_id: int
    target_code_name: str
    segments_moved: int
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


# =============================================================================
# Converters - Transform events to payloads
# =============================================================================


class CodeCreatedConverter(EventConverter):
    """Convert CodeCreated event to payload."""

    def convert(self, event: CodeCreated) -> CodePayload:
        return CodePayload(
            event_type="coding.code_created",
            code_id=event.code_id.value,
            code_name=event.name,
            color=event.color.to_hex(),
            memo=event.memo,
            category_id=event.category_id.value if event.category_id else None,
        )


class CodeRenamedConverter(EventConverter):
    """Convert CodeRenamed event to payload."""

    def convert(self, event: CodeRenamed) -> CodePayload:
        return CodePayload(
            event_type="coding.code_renamed",
            code_id=event.code_id.value,
            code_name=event.new_name,
        )


class CodeColorChangedConverter(EventConverter):
    """Convert CodeColorChanged event to payload."""

    def convert(self, event: CodeColorChanged) -> CodePayload:
        return CodePayload(
            event_type="coding.code_color_changed",
            code_id=event.code_id.value,
            code_name="",  # Not included in event
            color=event.new_color.to_hex(),
        )


class CodeDeletedConverter(EventConverter):
    """Convert CodeDeleted event to payload."""

    def convert(self, event: CodeDeleted) -> CodePayload:
        return CodePayload(
            event_type="coding.code_deleted",
            code_id=event.code_id.value,
            code_name=event.name,
        )


class CodeMemoUpdatedConverter(EventConverter):
    """Convert CodeMemoUpdated event to payload."""

    def convert(self, event: CodeMemoUpdated) -> CodePayload:
        return CodePayload(
            event_type="coding.code_memo_updated",
            code_id=event.code_id.value,
            code_name="",
            memo=event.new_memo,
        )


class CodeMovedToCategoryConverter(EventConverter):
    """Convert CodeMovedToCategory event to payload."""

    def convert(self, event: CodeMovedToCategory) -> CodePayload:
        return CodePayload(
            event_type="coding.code_moved_to_category",
            code_id=event.code_id.value,
            code_name="",
            category_id=event.new_category_id.value if event.new_category_id else None,
        )


class CodesMergedConverter(EventConverter):
    """Convert CodesMerged event to payload."""

    def convert(self, event: CodesMerged) -> CodeMergePayload:
        return CodeMergePayload(
            event_type="coding.codes_merged",
            source_code_id=event.source_code_id.value,
            source_code_name=event.source_code_name,
            target_code_id=event.target_code_id.value,
            target_code_name=event.target_code_name,
            segments_moved=event.segments_moved,
        )


class CategoryCreatedConverter(EventConverter):
    """Convert CategoryCreated event to payload."""

    def convert(self, event: CategoryCreated) -> CategoryPayload:
        return CategoryPayload(
            event_type="coding.category_created",
            category_id=event.category_id.value,
            category_name=event.name,
            parent_id=event.parent_id.value if event.parent_id else None,
            memo=event.memo,
        )


class CategoryRenamedConverter(EventConverter):
    """Convert CategoryRenamed event to payload."""

    def convert(self, event: CategoryRenamed) -> CategoryPayload:
        return CategoryPayload(
            event_type="coding.category_renamed",
            category_id=event.category_id.value,
            category_name=event.new_name,
        )


class CategoryDeletedConverter(EventConverter):
    """Convert CategoryDeleted event to payload."""

    def convert(self, event: CategoryDeleted) -> CategoryPayload:
        return CategoryPayload(
            event_type="coding.category_deleted",
            category_id=event.category_id.value,
            category_name=event.name,
        )


class SegmentCodedConverter(EventConverter):
    """Convert SegmentCoded event to payload."""

    def convert(self, event: SegmentCoded) -> SegmentPayload:
        return SegmentPayload(
            event_type="coding.segment_coded",
            segment_id=event.segment_id.value,
            code_id=event.code_id.value,
            code_name=event.code_name,
            source_id=event.source_id.value,
            source_name=event.source_name,
            start=event.position.start,
            end=event.position.end,
            selected_text=event.selected_text,
            memo=event.memo,
        )


class SegmentUncodedConverter(EventConverter):
    """Convert SegmentUncoded event to payload."""

    def convert(self, event: SegmentUncoded) -> SegmentPayload:
        return SegmentPayload(
            event_type="coding.segment_uncoded",
            segment_id=event.segment_id.value,
            code_id=event.code_id.value,
            code_name="",
            source_id=event.source_id.value,
            source_name="",
            start=0,
            end=0,
            selected_text="",
        )


class SegmentMemoUpdatedConverter(EventConverter):
    """Convert SegmentMemoUpdated event to payload."""

    def convert(self, event: SegmentMemoUpdated) -> SegmentPayload:
        return SegmentPayload(
            event_type="coding.segment_memo_updated",
            segment_id=event.segment_id.value,
            code_id=0,
            code_name="",
            source_id=0,
            source_name="",
            start=0,
            end=0,
            selected_text="",
            memo=event.new_memo,
        )


# =============================================================================
# Signal Bridge
# =============================================================================


class CodingSignalBridge(BaseSignalBridge):
    """
    Signal bridge for the Coding bounded context.

    Emits Qt signals when domain events occur, enabling reactive UI updates.

    Signals:
        code_created: Emitted when a new code is created
        code_renamed: Emitted when a code is renamed
        code_color_changed: Emitted when a code's color changes
        code_deleted: Emitted when a code is deleted
        code_memo_updated: Emitted when a code's memo changes
        code_moved: Emitted when a code moves to a different category
        codes_merged: Emitted when codes are merged
        category_created: Emitted when a category is created
        category_renamed: Emitted when a category is renamed
        category_deleted: Emitted when a category is deleted
        segment_coded: Emitted when a segment is coded
        segment_uncoded: Emitted when coding is removed from a segment
        segment_memo_updated: Emitted when a segment's memo changes

    Usage:
        bridge = CodingSignalBridge.instance(event_bus)
        bridge.code_created.connect(self._on_code_created)
        bridge.start()
    """

    # Code signals
    code_created = Signal(object)
    code_renamed = Signal(object)
    code_color_changed = Signal(object)
    code_deleted = Signal(object)
    code_memo_updated = Signal(object)
    code_moved = Signal(object)
    codes_merged = Signal(object)

    # Category signals
    category_created = Signal(object)
    category_renamed = Signal(object)
    category_deleted = Signal(object)

    # Segment signals
    segment_coded = Signal(object)
    segment_uncoded = Signal(object)
    segment_memo_updated = Signal(object)

    def _get_context_name(self) -> str:
        """Return the bounded context name."""
        return "coding"

    def _register_converters(self) -> None:
        """Register all event converters."""
        # Code events
        self.register_converter(
            "coding.code_created", CodeCreatedConverter(), "code_created"
        )
        self.register_converter(
            "coding.code_renamed", CodeRenamedConverter(), "code_renamed"
        )
        self.register_converter(
            "coding.code_color_changed",
            CodeColorChangedConverter(),
            "code_color_changed",
        )
        self.register_converter(
            "coding.code_deleted", CodeDeletedConverter(), "code_deleted"
        )
        self.register_converter(
            "coding.code_memo_updated", CodeMemoUpdatedConverter(), "code_memo_updated"
        )
        self.register_converter(
            "coding.code_moved_to_category",
            CodeMovedToCategoryConverter(),
            "code_moved",
        )
        self.register_converter(
            "coding.codes_merged", CodesMergedConverter(), "codes_merged"
        )

        # Category events
        self.register_converter(
            "coding.category_created", CategoryCreatedConverter(), "category_created"
        )
        self.register_converter(
            "coding.category_renamed", CategoryRenamedConverter(), "category_renamed"
        )
        self.register_converter(
            "coding.category_deleted", CategoryDeletedConverter(), "category_deleted"
        )

        # Segment events
        self.register_converter(
            "coding.segment_coded", SegmentCodedConverter(), "segment_coded"
        )
        self.register_converter(
            "coding.segment_uncoded", SegmentUncodedConverter(), "segment_uncoded"
        )
        self.register_converter(
            "coding.segment_memo_updated",
            SegmentMemoUpdatedConverter(),
            "segment_memo_updated",
        )
