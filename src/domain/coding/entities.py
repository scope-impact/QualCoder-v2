"""
Coding Context: Entities and Value Objects
Immutable data types representing domain concepts.

This file defines the CONTRACT for data shapes in the Coding context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.shared.types import CategoryId, CodeId, SegmentId, SourceId

# ============================================================
# Value Objects
# ============================================================


@dataclass(frozen=True)
class Color:
    """RGB color value object"""

    red: int
    green: int
    blue: int

    def __post_init__(self):
        for c, name in [(self.red, "red"), (self.green, "green"), (self.blue, "blue")]:
            if not 0 <= c <= 255:
                raise ValueError(f"{name} must be between 0 and 255, got {c}")

    def to_hex(self) -> str:
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}"

    @classmethod
    def from_hex(cls, hex_color: str) -> Color:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color: {hex_color}")
        return cls(
            red=int(hex_color[0:2], 16),
            green=int(hex_color[2:4], 16),
            blue=int(hex_color[4:6], 16),
        )

    def contrast_color(self) -> Color:
        """Return black or white for best contrast"""
        luminance = (0.299 * self.red + 0.587 * self.green + 0.114 * self.blue) / 255
        return Color(0, 0, 0) if luminance > 0.5 else Color(255, 255, 255)


@dataclass(frozen=True)
class TextPosition:
    """Position within a text source"""

    start: int
    end: int

    def __post_init__(self):
        if self.start < 0:
            raise ValueError(f"start must be >= 0, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) must be >= start ({self.start})")

    @property
    def length(self) -> int:
        return self.end - self.start

    def overlaps(self, other: TextPosition) -> bool:
        return self.start < other.end and other.start < self.end

    def contains(self, other: TextPosition) -> bool:
        return self.start <= other.start and self.end >= other.end


@dataclass(frozen=True)
class ImageRegion:
    """Region within an image source"""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")

    @property
    def area(self) -> int:
        return self.width * self.height

    def intersects(self, other: ImageRegion) -> bool:
        return not (
            self.x + self.width <= other.x
            or other.x + other.width <= self.x
            or self.y + self.height <= other.y
            or other.y + other.height <= self.y
        )


@dataclass(frozen=True)
class TimeRange:
    """Time range within an audio/video source"""

    start_ms: int
    end_ms: int

    def __post_init__(self):
        if self.start_ms < 0:
            raise ValueError(f"start_ms must be >= 0, got {self.start_ms}")
        if self.end_ms < self.start_ms:
            raise ValueError(
                f"end_ms ({self.end_ms}) must be >= start_ms ({self.start_ms})"
            )

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    def overlaps(self, other: TimeRange) -> bool:
        return self.start_ms < other.end_ms and other.start_ms < self.end_ms


# ============================================================
# Entities
# ============================================================


@dataclass(frozen=True)
class Code:
    """
    A semantic code used to label segments of qualitative data.
    Immutable entity with identity.

    Aggregate Root for the Code aggregate.
    """

    id: CodeId
    name: str
    color: Color
    memo: str | None = None
    category_id: CategoryId | None = None
    owner: str | None = None  # CoderId as string for now
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_name(self, new_name: str) -> Code:
        """Return new Code with updated name"""
        return Code(
            id=self.id,
            name=new_name,
            color=self.color,
            memo=self.memo,
            category_id=self.category_id,
            owner=self.owner,
            created_at=self.created_at,
        )

    def with_color(self, new_color: Color) -> Code:
        """Return new Code with updated color"""
        return Code(
            id=self.id,
            name=self.name,
            color=new_color,
            memo=self.memo,
            category_id=self.category_id,
            owner=self.owner,
            created_at=self.created_at,
        )

    def with_memo(self, new_memo: str | None) -> Code:
        """Return new Code with updated memo"""
        return Code(
            id=self.id,
            name=self.name,
            color=self.color,
            memo=new_memo,
            category_id=self.category_id,
            owner=self.owner,
            created_at=self.created_at,
        )

    def with_category(self, new_category_id: CategoryId | None) -> Code:
        """Return new Code with updated category"""
        return Code(
            id=self.id,
            name=self.name,
            color=self.color,
            memo=self.memo,
            category_id=new_category_id,
            owner=self.owner,
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class Category:
    """
    A hierarchical grouping of codes.
    Aggregate Root for the Category aggregate.
    """

    id: CategoryId
    name: str
    parent_id: CategoryId | None = None
    memo: str | None = None
    owner: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_name(self, new_name: str) -> Category:
        return Category(
            id=self.id,
            name=new_name,
            parent_id=self.parent_id,
            memo=self.memo,
            owner=self.owner,
            created_at=self.created_at,
        )

    def with_parent(self, new_parent_id: CategoryId | None) -> Category:
        return Category(
            id=self.id,
            name=self.name,
            parent_id=new_parent_id,
            memo=self.memo,
            owner=self.owner,
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class TextSegment:
    """
    A coded segment of text within a source document.
    Links a Code to a specific position in a Source.

    Aggregate Root for the Segment aggregate.
    """

    id: SegmentId
    source_id: SourceId
    code_id: CodeId
    position: TextPosition
    selected_text: str
    memo: str | None = None
    importance: int = 0  # 0=normal, 1=important, 2=very important
    owner: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_memo(self, new_memo: str | None) -> TextSegment:
        return TextSegment(
            id=self.id,
            source_id=self.source_id,
            code_id=self.code_id,
            position=self.position,
            selected_text=self.selected_text,
            memo=new_memo,
            importance=self.importance,
            owner=self.owner,
            created_at=self.created_at,
        )

    def with_importance(self, new_importance: int) -> TextSegment:
        return TextSegment(
            id=self.id,
            source_id=self.source_id,
            code_id=self.code_id,
            position=self.position,
            selected_text=self.selected_text,
            memo=self.memo,
            importance=new_importance,
            owner=self.owner,
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class ImageSegment:
    """A coded region within an image source"""

    id: SegmentId
    source_id: SourceId
    code_id: CodeId
    region: ImageRegion
    memo: str | None = None
    importance: int = 0
    owner: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class AVSegment:
    """A coded time range within an audio/video source"""

    id: SegmentId
    source_id: SourceId
    code_id: CodeId
    time_range: TimeRange
    transcript: str | None = None
    memo: str | None = None
    importance: int = 0
    owner: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# Type alias for all segment types
Segment = TextSegment | ImageSegment | AVSegment
