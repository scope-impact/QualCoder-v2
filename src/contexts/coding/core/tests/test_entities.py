"""
Coding Context: Entity and Value Object Tests

Tests for immutable data types representing domain concepts.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ============================================================
# Color Value Object Tests
# ============================================================


class TestColor:
    """Tests for Color value object."""

    def test_creates_with_valid_rgb(self):
        """Should create color with valid RGB values."""
        from src.contexts.coding.core.entities import Color

        color = Color(red=255, green=128, blue=0)

        assert color.red == 255
        assert color.green == 128
        assert color.blue == 0

    def test_rejects_negative_values(self):
        """Should reject negative RGB values."""
        from src.contexts.coding.core.entities import Color

        with pytest.raises(ValueError, match="must be between 0 and 255"):
            Color(red=-1, green=128, blue=0)

        with pytest.raises(ValueError, match="must be between 0 and 255"):
            Color(red=128, green=-1, blue=0)

        with pytest.raises(ValueError, match="must be between 0 and 255"):
            Color(red=128, green=128, blue=-1)

    def test_rejects_values_over_255(self):
        """Should reject RGB values over 255."""
        from src.contexts.coding.core.entities import Color

        with pytest.raises(ValueError, match="must be between 0 and 255"):
            Color(red=256, green=128, blue=0)

        with pytest.raises(ValueError, match="must be between 0 and 255"):
            Color(red=128, green=256, blue=0)

        with pytest.raises(ValueError, match="must be between 0 and 255"):
            Color(red=128, green=128, blue=256)

    def test_to_hex(self):
        """Should convert to hex string correctly."""
        from src.contexts.coding.core.entities import Color

        assert Color(255, 0, 0).to_hex() == "#ff0000"
        assert Color(0, 255, 0).to_hex() == "#00ff00"
        assert Color(0, 0, 255).to_hex() == "#0000ff"
        assert Color(255, 255, 255).to_hex() == "#ffffff"
        assert Color(0, 0, 0).to_hex() == "#000000"
        assert Color(128, 64, 32).to_hex() == "#804020"

    def test_from_hex(self):
        """Should create color from hex string."""
        from src.contexts.coding.core.entities import Color

        assert Color.from_hex("#ff0000") == Color(255, 0, 0)
        assert Color.from_hex("#00ff00") == Color(0, 255, 0)
        assert Color.from_hex("#0000ff") == Color(0, 0, 255)
        assert Color.from_hex("ffffff") == Color(255, 255, 255)  # Without #

    def test_from_hex_rejects_invalid(self):
        """Should reject invalid hex strings."""
        from src.contexts.coding.core.entities import Color

        with pytest.raises(ValueError, match="Invalid hex color"):
            Color.from_hex("#fff")  # Too short

        with pytest.raises(ValueError, match="Invalid hex color"):
            Color.from_hex("#fffffff")  # Too long

    def test_contrast_color(self):
        """Should return appropriate contrast color."""
        from src.contexts.coding.core.entities import Color

        # Light colors should return black
        assert Color(255, 255, 255).contrast_color() == Color(0, 0, 0)
        assert Color(255, 255, 0).contrast_color() == Color(0, 0, 0)

        # Dark colors should return white
        assert Color(0, 0, 0).contrast_color() == Color(255, 255, 255)
        assert Color(0, 0, 128).contrast_color() == Color(255, 255, 255)

    def test_is_frozen(self):
        """Should be immutable."""
        from src.contexts.coding.core.entities import Color

        color = Color(255, 0, 0)

        with pytest.raises(AttributeError):
            color.red = 128


# ============================================================
# TextPosition Value Object Tests
# ============================================================


class TestTextPosition:
    """Tests for TextPosition value object."""

    def test_creates_with_valid_range(self):
        """Should create position with valid range."""
        from src.contexts.coding.core.entities import TextPosition

        pos = TextPosition(start=10, end=20)

        assert pos.start == 10
        assert pos.end == 20

    def test_rejects_negative_start(self):
        """Should reject negative start value."""
        from src.contexts.coding.core.entities import TextPosition

        with pytest.raises(ValueError, match="start must be >= 0"):
            TextPosition(start=-1, end=10)

    def test_rejects_end_before_start(self):
        """Should reject end before start."""
        from src.contexts.coding.core.entities import TextPosition

        with pytest.raises(ValueError, match="end .* must be >= start"):
            TextPosition(start=20, end=10)

    def test_allows_empty_range(self):
        """Should allow start == end (zero-length range)."""
        from src.contexts.coding.core.entities import TextPosition

        pos = TextPosition(start=10, end=10)
        assert pos.length == 0

    def test_length_property(self):
        """Should calculate length correctly."""
        from src.contexts.coding.core.entities import TextPosition

        assert TextPosition(start=0, end=10).length == 10
        assert TextPosition(start=5, end=15).length == 10
        assert TextPosition(start=10, end=10).length == 0

    def test_overlaps(self):
        """Should detect overlapping positions."""
        from src.contexts.coding.core.entities import TextPosition

        pos1 = TextPosition(start=10, end=20)

        # Overlapping cases
        assert pos1.overlaps(TextPosition(start=15, end=25)) is True
        assert pos1.overlaps(TextPosition(start=5, end=15)) is True
        assert pos1.overlaps(TextPosition(start=12, end=18)) is True  # Contained
        assert pos1.overlaps(TextPosition(start=5, end=25)) is True  # Contains

        # Non-overlapping cases
        assert pos1.overlaps(TextPosition(start=0, end=10)) is False  # Adjacent before
        assert pos1.overlaps(TextPosition(start=20, end=30)) is False  # Adjacent after
        assert pos1.overlaps(TextPosition(start=0, end=5)) is False  # Before
        assert pos1.overlaps(TextPosition(start=25, end=30)) is False  # After

    def test_contains(self):
        """Should detect contained positions."""
        from src.contexts.coding.core.entities import TextPosition

        pos1 = TextPosition(start=10, end=30)

        # Contained cases
        assert pos1.contains(TextPosition(start=10, end=30)) is True  # Same
        assert pos1.contains(TextPosition(start=15, end=25)) is True  # Inside
        assert pos1.contains(TextPosition(start=10, end=20)) is True  # From start

        # Not contained cases
        assert pos1.contains(TextPosition(start=5, end=15)) is False  # Overlaps start
        assert pos1.contains(TextPosition(start=25, end=35)) is False  # Overlaps end


# ============================================================
# ImageRegion Value Object Tests
# ============================================================


class TestImageRegion:
    """Tests for ImageRegion value object."""

    def test_creates_with_valid_region(self):
        """Should create region with valid dimensions."""
        from src.contexts.coding.core.entities import ImageRegion

        region = ImageRegion(x=10, y=20, width=100, height=50)

        assert region.x == 10
        assert region.y == 20
        assert region.width == 100
        assert region.height == 50

    def test_rejects_zero_width(self):
        """Should reject zero width."""
        from src.contexts.coding.core.entities import ImageRegion

        with pytest.raises(ValueError, match="width and height must be positive"):
            ImageRegion(x=0, y=0, width=0, height=50)

    def test_rejects_zero_height(self):
        """Should reject zero height."""
        from src.contexts.coding.core.entities import ImageRegion

        with pytest.raises(ValueError, match="width and height must be positive"):
            ImageRegion(x=0, y=0, width=50, height=0)

    def test_rejects_negative_dimensions(self):
        """Should reject negative dimensions."""
        from src.contexts.coding.core.entities import ImageRegion

        with pytest.raises(ValueError, match="width and height must be positive"):
            ImageRegion(x=0, y=0, width=-50, height=50)

        with pytest.raises(ValueError, match="width and height must be positive"):
            ImageRegion(x=0, y=0, width=50, height=-50)

    def test_area_property(self):
        """Should calculate area correctly."""
        from src.contexts.coding.core.entities import ImageRegion

        region = ImageRegion(x=0, y=0, width=10, height=20)
        assert region.area == 200

    def test_intersects(self):
        """Should detect intersecting regions."""
        from src.contexts.coding.core.entities import ImageRegion

        region1 = ImageRegion(x=10, y=10, width=20, height=20)

        # Intersecting cases
        assert region1.intersects(ImageRegion(x=20, y=20, width=20, height=20)) is True
        assert region1.intersects(ImageRegion(x=5, y=5, width=10, height=10)) is True
        assert region1.intersects(ImageRegion(x=15, y=15, width=10, height=10)) is True

        # Non-intersecting cases
        assert (
            region1.intersects(ImageRegion(x=30, y=10, width=10, height=10)) is False
        )  # Right
        assert (
            region1.intersects(ImageRegion(x=0, y=10, width=10, height=10)) is False
        )  # Left
        assert (
            region1.intersects(ImageRegion(x=10, y=30, width=10, height=10)) is False
        )  # Below
        assert (
            region1.intersects(ImageRegion(x=10, y=0, width=10, height=10)) is False
        )  # Above


# ============================================================
# TimeRange Value Object Tests
# ============================================================


class TestTimeRange:
    """Tests for TimeRange value object."""

    def test_creates_with_valid_range(self):
        """Should create range with valid times."""
        from src.contexts.coding.core.entities import TimeRange

        time_range = TimeRange(start_ms=1000, end_ms=5000)

        assert time_range.start_ms == 1000
        assert time_range.end_ms == 5000

    def test_rejects_negative_start(self):
        """Should reject negative start time."""
        from src.contexts.coding.core.entities import TimeRange

        with pytest.raises(ValueError, match="start_ms must be >= 0"):
            TimeRange(start_ms=-1, end_ms=5000)

    def test_rejects_end_before_start(self):
        """Should reject end before start."""
        from src.contexts.coding.core.entities import TimeRange

        with pytest.raises(ValueError, match="end_ms .* must be >= start_ms"):
            TimeRange(start_ms=5000, end_ms=1000)

    def test_duration_property(self):
        """Should calculate duration correctly."""
        from src.contexts.coding.core.entities import TimeRange

        assert TimeRange(start_ms=1000, end_ms=5000).duration_ms == 4000
        assert TimeRange(start_ms=0, end_ms=10000).duration_ms == 10000
        assert TimeRange(start_ms=5000, end_ms=5000).duration_ms == 0

    def test_overlaps(self):
        """Should detect overlapping ranges."""
        from src.contexts.coding.core.entities import TimeRange

        range1 = TimeRange(start_ms=1000, end_ms=3000)

        # Overlapping cases
        assert range1.overlaps(TimeRange(start_ms=2000, end_ms=4000)) is True
        assert range1.overlaps(TimeRange(start_ms=0, end_ms=2000)) is True
        assert range1.overlaps(TimeRange(start_ms=1500, end_ms=2500)) is True

        # Non-overlapping cases
        assert (
            range1.overlaps(TimeRange(start_ms=0, end_ms=1000)) is False
        )  # Adjacent before
        assert (
            range1.overlaps(TimeRange(start_ms=3000, end_ms=5000)) is False
        )  # Adjacent after
        assert range1.overlaps(TimeRange(start_ms=4000, end_ms=5000)) is False  # After


# ============================================================
# Code Entity Tests
# ============================================================


class TestCode:
    """Tests for Code entity."""

    def test_creates_with_required_fields(self):
        """Should create code with required fields."""
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code = Code(
            id=CodeId(value=1),
            name="Theme",
            color=Color(255, 0, 0),
        )

        assert code.id == CodeId(value=1)
        assert code.name == "Theme"
        assert code.color == Color(255, 0, 0)
        assert code.memo is None
        assert code.category_id is None

    def test_with_name_returns_new_code(self):
        """Should return new code with updated name."""
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        original = Code(id=CodeId(value=1), name="Old", color=Color(255, 0, 0))
        updated = original.with_name("New")

        assert updated.name == "New"
        assert updated.id == original.id
        assert original.name == "Old"  # Original unchanged

    def test_with_color_returns_new_code(self):
        """Should return new code with updated color."""
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        original = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))
        updated = original.with_color(Color(0, 255, 0))

        assert updated.color == Color(0, 255, 0)
        assert original.color == Color(255, 0, 0)

    def test_with_memo_returns_new_code(self):
        """Should return new code with updated memo."""
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        original = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))
        updated = original.with_memo("New memo")

        assert updated.memo == "New memo"
        assert original.memo is None

    def test_with_category_returns_new_code(self):
        """Should return new code with updated category."""
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CategoryId, CodeId

        original = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))
        updated = original.with_category(CategoryId(value=5))

        assert updated.category_id == CategoryId(value=5)
        assert original.category_id is None

    def test_is_frozen(self):
        """Should be immutable."""
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))

        with pytest.raises(AttributeError):
            code.name = "Changed"


# ============================================================
# Category Entity Tests
# ============================================================


class TestCategory:
    """Tests for Category entity."""

    def test_creates_with_required_fields(self):
        """Should create category with required fields."""
        from src.contexts.coding.core.entities import Category
        from src.shared import CategoryId

        category = Category(
            id=CategoryId(value=1),
            name="Themes",
        )

        assert category.id == CategoryId(value=1)
        assert category.name == "Themes"
        assert category.parent_id is None
        assert category.memo is None

    def test_with_name_returns_new_category(self):
        """Should return new category with updated name."""
        from src.contexts.coding.core.entities import Category
        from src.shared import CategoryId

        original = Category(id=CategoryId(value=1), name="Old")
        updated = original.with_name("New")

        assert updated.name == "New"
        assert original.name == "Old"

    def test_with_parent_returns_new_category(self):
        """Should return new category with updated parent."""
        from src.contexts.coding.core.entities import Category
        from src.shared import CategoryId

        original = Category(id=CategoryId(value=1), name="Child")
        updated = original.with_parent(CategoryId(value=5))

        assert updated.parent_id == CategoryId(value=5)
        assert original.parent_id is None


# ============================================================
# TextSegment Entity Tests
# ============================================================


class TestTextSegment:
    """Tests for TextSegment entity."""

    def test_creates_with_required_fields(self):
        """Should create segment with required fields."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.shared import CodeId, SegmentId, SourceId

        segment = TextSegment(
            id=SegmentId(value=1),
            source_id=SourceId(value=10),
            code_id=CodeId(value=5),
            position=TextPosition(start=0, end=100),
            selected_text="Sample text",
        )

        assert segment.id == SegmentId(value=1)
        assert segment.source_id == SourceId(value=10)
        assert segment.code_id == CodeId(value=5)
        assert segment.position.start == 0
        assert segment.position.end == 100
        assert segment.selected_text == "Sample text"
        assert segment.memo is None
        assert segment.importance == 0

    def test_with_memo_returns_new_segment(self):
        """Should return new segment with updated memo."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.shared import CodeId, SegmentId, SourceId

        original = TextSegment(
            id=SegmentId(value=1),
            source_id=SourceId(value=10),
            code_id=CodeId(value=5),
            position=TextPosition(start=0, end=100),
            selected_text="Sample text",
        )
        updated = original.with_memo("New memo")

        assert updated.memo == "New memo"
        assert original.memo is None

    def test_with_importance_returns_new_segment(self):
        """Should return new segment with updated importance."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.shared import CodeId, SegmentId, SourceId

        original = TextSegment(
            id=SegmentId(value=1),
            source_id=SourceId(value=10),
            code_id=CodeId(value=5),
            position=TextPosition(start=0, end=100),
            selected_text="Sample text",
        )
        updated = original.with_importance(2)

        assert updated.importance == 2
        assert original.importance == 0


# ============================================================
# BatchId Value Object Tests
# ============================================================


class TestBatchId:
    """Tests for BatchId value object."""

    def test_creates_with_value(self):
        """Should create batch ID with value."""
        from src.contexts.coding.core.entities import BatchId

        batch_id = BatchId(value="batch_123abc")
        assert batch_id.value == "batch_123abc"

    def test_new_generates_unique_id(self):
        """Should generate unique ID."""
        from src.contexts.coding.core.entities import BatchId

        id1 = BatchId.new()
        id2 = BatchId.new()

        assert id1.value != id2.value
        assert id1.value.startswith("batch_")
        assert id2.value.startswith("batch_")


# ============================================================
# AutoCodeBatch Entity Tests
# ============================================================


class TestAutoCodeBatch:
    """Tests for AutoCodeBatch entity."""

    def test_creates_with_required_fields(self):
        """Should create batch with required fields."""
        from src.contexts.coding.core.entities import AutoCodeBatch, BatchId
        from src.shared import CodeId, SegmentId

        batch = AutoCodeBatch(
            id=BatchId(value="batch_123"),
            code_id=CodeId(value=5),
            pattern="test pattern",
            segment_ids=(SegmentId(value=1), SegmentId(value=2)),
        )

        assert batch.id.value == "batch_123"
        assert batch.code_id == CodeId(value=5)
        assert batch.pattern == "test pattern"
        assert len(batch.segment_ids) == 2

    def test_can_undo_with_segments(self):
        """Should return True for can_undo when batch has segments."""
        from src.contexts.coding.core.entities import AutoCodeBatch, BatchId
        from src.shared import CodeId, SegmentId

        batch = AutoCodeBatch(
            id=BatchId(value="batch_123"),
            code_id=CodeId(value=5),
            pattern="test pattern",
            segment_ids=(SegmentId(value=1),),
        )

        assert batch.can_undo() is True

    def test_cannot_undo_without_segments(self):
        """Should return False for can_undo when batch has no segments."""
        from src.contexts.coding.core.entities import AutoCodeBatch, BatchId
        from src.shared import CodeId

        batch = AutoCodeBatch(
            id=BatchId(value="batch_123"),
            code_id=CodeId(value=5),
            pattern="test pattern",
            segment_ids=(),
        )

        assert batch.can_undo() is False

    def test_segment_count_property(self):
        """Should return correct segment count."""
        from src.contexts.coding.core.entities import AutoCodeBatch, BatchId
        from src.shared import CodeId, SegmentId

        batch = AutoCodeBatch(
            id=BatchId(value="batch_123"),
            code_id=CodeId(value=5),
            pattern="test pattern",
            segment_ids=(SegmentId(value=1), SegmentId(value=2), SegmentId(value=3)),
        )

        assert batch.segment_count == 3
