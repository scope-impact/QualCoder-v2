"""
Coding Context: Entity and Value Object Tests

Tests for immutable data types representing domain concepts.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-028 Code Management"),
]


# ============================================================
# Color Value Object Tests
# ============================================================


@allure.story("QC-028.00 Color Value Object")
class TestColor:
    """Tests for Color value object."""

    @allure.title("Creates color with valid RGB and computes contrast color")
    def test_creates_with_valid_rgb_and_contrast(self):
        """Should create color with valid RGB values and return correct contrast."""
        from src.contexts.coding.core.entities import Color

        color = Color(red=255, green=128, blue=0)

        assert color.red == 255
        assert color.green == 128
        assert color.blue == 0

        # Light colors should return black
        assert Color(255, 255, 255).contrast_color() == Color(0, 0, 0)
        assert Color(255, 255, 0).contrast_color() == Color(0, 0, 0)

        # Dark colors should return white
        assert Color(0, 0, 0).contrast_color() == Color(255, 255, 255)
        assert Color(0, 0, 128).contrast_color() == Color(255, 255, 255)

    @pytest.mark.parametrize(
        "r, g, b",
        [
            (-1, 128, 0),
            (128, -1, 0),
            (128, 128, -1),
            (256, 128, 0),
            (128, 256, 0),
            (128, 128, 256),
        ],
        ids=[
            "negative-red",
            "negative-green",
            "negative-blue",
            "over255-red",
            "over255-green",
            "over255-blue",
        ],
    )
    @allure.title("Rejects RGB values outside 0-255")
    def test_rejects_out_of_range_values(self, r, g, b):
        """Should reject RGB values outside 0-255."""
        from src.contexts.coding.core.entities import Color

        with pytest.raises(ValueError, match="must be between 0 and 255"):
            Color(red=r, green=g, blue=b)

    @pytest.mark.parametrize(
        "r, g, b, expected_hex",
        [
            (255, 0, 0, "#ff0000"),
            (0, 255, 0, "#00ff00"),
            (0, 0, 255, "#0000ff"),
            (255, 255, 255, "#ffffff"),
            (0, 0, 0, "#000000"),
            (128, 64, 32, "#804020"),
        ],
    )
    @allure.title("Converts to hex string correctly")
    def test_to_hex(self, r, g, b, expected_hex):
        """Should convert to hex string correctly."""
        from src.contexts.coding.core.entities import Color

        assert Color(r, g, b).to_hex() == expected_hex

    @pytest.mark.parametrize(
        "hex_str, expected_rgb, should_fail",
        [
            ("#ff0000", (255, 0, 0), False),
            ("#00ff00", (0, 255, 0), False),
            ("#0000ff", (0, 0, 255), False),
            ("ffffff", (255, 255, 255), False),
            ("#fff", (255, 255, 255), False),
            ("#f00", (255, 0, 0), False),
            ("#fffffff", None, True),
            ("#ff", None, True),
        ],
        ids=["red", "green", "blue", "no-hash", "shorthand-white", "shorthand-red", "too-long", "too-short"],
    )
    @allure.title("Creates color from hex string or rejects invalid hex")
    def test_from_hex_valid_and_invalid(self, hex_str, expected_rgb, should_fail):
        """Should create color from valid hex and reject invalid hex strings."""
        from src.contexts.coding.core.entities import Color

        if should_fail:
            with pytest.raises(ValueError, match="Invalid hex color"):
                Color.from_hex(hex_str)
        else:
            result = Color.from_hex(hex_str)
            assert result == Color(*expected_rgb)


# ============================================================
# TextPosition Value Object Tests
# ============================================================


@allure.story("QC-028.00 TextPosition Value Object")
class TestTextPosition:
    """Tests for TextPosition value object."""

    @allure.title("Creates position, computes length, detects overlaps and containment")
    def test_creates_and_checks_overlaps_and_contains(self):
        """Should create position with valid range, compute length, detect overlaps and containment."""
        from src.contexts.coding.core.entities import TextPosition

        pos = TextPosition(start=10, end=20)
        assert pos.start == 10
        assert pos.end == 20
        assert pos.length == 10
        assert TextPosition(start=10, end=10).length == 0

        # Overlapping cases
        pos1 = TextPosition(start=10, end=20)
        assert pos1.overlaps(TextPosition(start=15, end=25)) is True
        assert pos1.overlaps(TextPosition(start=5, end=15)) is True
        assert pos1.overlaps(TextPosition(start=12, end=18)) is True
        assert pos1.overlaps(TextPosition(start=5, end=25)) is True

        # Non-overlapping cases
        assert pos1.overlaps(TextPosition(start=0, end=10)) is False
        assert pos1.overlaps(TextPosition(start=20, end=30)) is False
        assert pos1.overlaps(TextPosition(start=0, end=5)) is False
        assert pos1.overlaps(TextPosition(start=25, end=30)) is False

        # Contains cases
        pos2 = TextPosition(start=10, end=30)
        assert pos2.contains(TextPosition(start=10, end=30)) is True
        assert pos2.contains(TextPosition(start=15, end=25)) is True
        assert pos2.contains(TextPosition(start=10, end=20)) is True
        assert pos2.contains(TextPosition(start=5, end=15)) is False
        assert pos2.contains(TextPosition(start=25, end=35)) is False

    @pytest.mark.parametrize(
        "start, end, match",
        [
            (-1, 10, "start must be >= 0"),
            (20, 10, "end .* must be >= start"),
        ],
        ids=["negative-start", "end-before-start"],
    )
    @allure.title("Rejects invalid start/end combinations")
    def test_rejects_invalid_range(self, start, end, match):
        """Should reject invalid start/end combinations."""
        from src.contexts.coding.core.entities import TextPosition

        with pytest.raises(ValueError, match=match):
            TextPosition(start=start, end=end)


# ============================================================
# ImageRegion Value Object Tests
# ============================================================


@allure.story("QC-028.00 ImageRegion Value Object")
class TestImageRegion:
    """Tests for ImageRegion value object."""

    @allure.title("Creates region, computes area, and detects intersections")
    def test_creates_and_detects_intersections(self):
        """Should create region with valid dimensions, compute area, and detect intersections."""
        from src.contexts.coding.core.entities import ImageRegion

        region = ImageRegion(x=10, y=20, width=100, height=50)
        assert region.x == 10
        assert region.y == 20
        assert region.width == 100
        assert region.height == 50
        assert region.area == 5000

        region1 = ImageRegion(x=10, y=10, width=20, height=20)
        # Intersecting cases
        assert region1.intersects(ImageRegion(x=20, y=20, width=20, height=20)) is True
        assert region1.intersects(ImageRegion(x=5, y=5, width=10, height=10)) is True
        assert region1.intersects(ImageRegion(x=15, y=15, width=10, height=10)) is True
        # Non-intersecting cases
        assert region1.intersects(ImageRegion(x=30, y=10, width=10, height=10)) is False
        assert region1.intersects(ImageRegion(x=0, y=10, width=10, height=10)) is False
        assert region1.intersects(ImageRegion(x=10, y=30, width=10, height=10)) is False
        assert region1.intersects(ImageRegion(x=10, y=0, width=10, height=10)) is False

    @pytest.mark.parametrize(
        "w, h",
        [(0, 50), (50, 0), (-50, 50), (50, -50)],
        ids=["zero-width", "zero-height", "negative-width", "negative-height"],
    )
    @allure.title("Rejects non-positive dimensions")
    def test_rejects_non_positive_dimensions(self, w, h):
        """Should reject zero or negative dimensions."""
        from src.contexts.coding.core.entities import ImageRegion

        with pytest.raises(ValueError, match="width and height must be positive"):
            ImageRegion(x=0, y=0, width=w, height=h)


# ============================================================
# TimeRange Value Object Tests
# ============================================================


@allure.story("QC-028.00 TimeRange Value Object")
class TestTimeRange:
    """Tests for TimeRange value object."""

    @allure.title("Creates range, computes duration, and detects overlaps")
    def test_creates_and_detects_overlaps(self):
        """Should create range with valid times, compute duration, and detect overlaps."""
        from src.contexts.coding.core.entities import TimeRange

        time_range = TimeRange(start_ms=1000, end_ms=5000)
        assert time_range.start_ms == 1000
        assert time_range.end_ms == 5000
        assert time_range.duration_ms == 4000
        assert TimeRange(start_ms=5000, end_ms=5000).duration_ms == 0

        range1 = TimeRange(start_ms=1000, end_ms=3000)
        # Overlapping cases
        assert range1.overlaps(TimeRange(start_ms=2000, end_ms=4000)) is True
        assert range1.overlaps(TimeRange(start_ms=0, end_ms=2000)) is True
        assert range1.overlaps(TimeRange(start_ms=1500, end_ms=2500)) is True
        # Non-overlapping cases
        assert range1.overlaps(TimeRange(start_ms=0, end_ms=1000)) is False
        assert range1.overlaps(TimeRange(start_ms=3000, end_ms=5000)) is False
        assert range1.overlaps(TimeRange(start_ms=4000, end_ms=5000)) is False

    @pytest.mark.parametrize(
        "start, end, match",
        [
            (-1, 5000, "start_ms must be >= 0"),
            (5000, 1000, "end_ms .* must be >= start_ms"),
        ],
        ids=["negative-start", "end-before-start"],
    )
    @allure.title("Rejects invalid time ranges")
    def test_rejects_invalid_range(self, start, end, match):
        """Should reject invalid time ranges."""
        from src.contexts.coding.core.entities import TimeRange

        with pytest.raises(ValueError, match=match):
            TimeRange(start_ms=start, end_ms=end)


# ============================================================
# Code Entity Tests
# ============================================================


@allure.story("QC-028.01 Create New Code")
class TestCode:
    """Tests for Code entity."""

    @allure.title("Creates code with defaults and returns updated copies via with_ methods")
    def test_creates_with_defaults_and_with_methods(self):
        """Should create code with defaults and return new instances with updated fields."""
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CategoryId, CodeId

        code = Code(
            id=CodeId(value="1"),
            name="Theme",
            color=Color(255, 0, 0),
        )

        assert code.id == CodeId(value="1")
        assert code.name == "Theme"
        assert code.color == Color(255, 0, 0)
        assert code.memo is None
        assert code.category_id is None

        original = Code(id=CodeId(value="1"), name="Old", color=Color(255, 0, 0))

        renamed = original.with_name("New")
        assert renamed.name == "New"
        assert original.name == "Old"

        recolored = original.with_color(Color(0, 255, 0))
        assert recolored.color == Color(0, 255, 0)
        assert original.color == Color(255, 0, 0)

        with_memo = original.with_memo("New memo")
        assert with_memo.memo == "New memo"
        assert original.memo is None

        with_cat = original.with_category(CategoryId(value="5"))
        assert with_cat.category_id == CategoryId(value="5")
        assert original.category_id is None


# ============================================================
# Category Entity Tests
# ============================================================


@allure.story("QC-028.02 Organize Codes into Categories")
class TestCategory:
    """Tests for Category entity."""

    @allure.title("Creates category with defaults and returns updated copies via with_ methods")
    def test_creates_with_defaults_and_with_methods(self):
        """Should create category with defaults and return new instances with updated fields."""
        from src.contexts.coding.core.entities import Category
        from src.shared import CategoryId

        category = Category(
            id=CategoryId(value="1"),
            name="Themes",
        )

        assert category.id == CategoryId(value="1")
        assert category.name == "Themes"
        assert category.parent_id is None
        assert category.memo is None

        original = Category(id=CategoryId(value="1"), name="Old")

        renamed = original.with_name("New")
        assert renamed.name == "New"
        assert original.name == "Old"

        with_parent = original.with_parent(CategoryId(value="5"))
        assert with_parent.parent_id == CategoryId(value="5")
        assert original.parent_id is None


# ============================================================
# TextSegment Entity Tests
# ============================================================


@allure.story("QC-029.01 Apply Code to Text")
class TestTextSegment:
    """Tests for TextSegment entity."""

    @allure.title("Creates segment with defaults and returns updated copies via with_ methods")
    def test_creates_with_defaults_and_with_methods(self):
        """Should create segment with defaults and return new instances with updated fields."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.shared import CodeId, SegmentId, SourceId

        segment = TextSegment(
            id=SegmentId(value="1"),
            source_id=SourceId(value="10"),
            code_id=CodeId(value="5"),
            position=TextPosition(start=0, end=100),
            selected_text="Sample text",
        )

        assert segment.id == SegmentId(value="1")
        assert segment.source_id == SourceId(value="10")
        assert segment.code_id == CodeId(value="5")
        assert segment.position.start == 0
        assert segment.position.end == 100
        assert segment.selected_text == "Sample text"
        assert segment.memo is None
        assert segment.importance == 0

        with_memo = segment.with_memo("New memo")
        assert with_memo.memo == "New memo"
        assert segment.memo is None

        with_importance = segment.with_importance(2)
        assert with_importance.importance == 2
        assert segment.importance == 0


# ============================================================
# BatchId Value Object Tests
# ============================================================


@allure.story("QC-029.01 Apply Code to Text")
class TestBatchId:
    """Tests for BatchId value object."""

    @allure.title("Creates batch ID with value and generates unique IDs")
    def test_creates_and_generates_unique_ids(self):
        """Should create batch ID with value and generate unique IDs."""
        from src.contexts.coding.core.entities import BatchId

        batch_id = BatchId(value="batch_123abc")
        assert batch_id.value == "batch_123abc"

        id1 = BatchId.new()
        id2 = BatchId.new()
        assert id1.value != id2.value
        assert id1.value.startswith("batch_")
        assert id2.value.startswith("batch_")


# ============================================================
# AutoCodeBatch Entity Tests
# ============================================================


@allure.story("QC-029.01 Apply Code to Text")
class TestAutoCodeBatch:
    """Tests for AutoCodeBatch entity."""

    @allure.title("Creates batch and reports can_undo and segment_count")
    def test_creates_and_reports_undo_status(self):
        """Should create batch and report can_undo based on segments and correct count."""
        from src.contexts.coding.core.entities import AutoCodeBatch, BatchId
        from src.shared import CodeId, SegmentId

        batch = AutoCodeBatch(
            id=BatchId(value="batch_123"),
            code_id=CodeId(value="5"),
            pattern="test pattern",
            segment_ids=(SegmentId(value="1"), SegmentId(value="2")),
        )

        assert batch.id.value == "batch_123"
        assert batch.code_id == CodeId(value="5")
        assert batch.pattern == "test pattern"
        assert len(batch.segment_ids) == 2

        batch_with = AutoCodeBatch(
            id=BatchId(value="batch_123"),
            code_id=CodeId(value="5"),
            pattern="test pattern",
            segment_ids=(
                SegmentId(value="1"),
                SegmentId(value="2"),
                SegmentId(value="3"),
            ),
        )
        assert batch_with.can_undo() is True
        assert batch_with.segment_count == 3

        batch_empty = AutoCodeBatch(
            id=BatchId(value="batch_456"),
            code_id=CodeId(value="5"),
            pattern="test pattern",
            segment_ids=(),
        )
        assert batch_empty.can_undo() is False
        assert batch_empty.segment_count == 0
