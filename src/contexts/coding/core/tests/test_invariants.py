"""
Coding Context: Invariant Tests

Tests for pure predicate functions that validate business rules for Coding.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ============================================================
# Code Invariant Tests
# ============================================================


class TestIsValidCodeName:
    """Tests for is_valid_code_name invariant."""

    def test_accepts_normal_string(self):
        """Normal alphanumeric names should be valid."""
        from src.contexts.coding.core.invariants import is_valid_code_name

        assert is_valid_code_name("Theme") is True
        assert is_valid_code_name("Emerging-Pattern") is True
        assert is_valid_code_name("Code_With_Numbers_123") is True

    def test_rejects_empty_string(self):
        """Empty string should be invalid."""
        from src.contexts.coding.core.invariants import is_valid_code_name

        assert is_valid_code_name("") is False

    def test_rejects_whitespace_only(self):
        """Whitespace-only strings should be invalid."""
        from src.contexts.coding.core.invariants import is_valid_code_name

        assert is_valid_code_name("   ") is False
        assert is_valid_code_name("\t\n") is False

    def test_rejects_too_long(self):
        """Names exceeding 100 characters should be invalid."""
        from src.contexts.coding.core.invariants import is_valid_code_name

        long_name = "a" * 101
        assert is_valid_code_name(long_name) is False

    def test_accepts_max_length(self):
        """Names at exactly 100 characters should be valid."""
        from src.contexts.coding.core.invariants import is_valid_code_name

        max_name = "a" * 100
        assert is_valid_code_name(max_name) is True


class TestIsCodeNameUnique:
    """Tests for is_code_name_unique invariant."""

    def test_unique_in_empty_project(self):
        """Any name is unique in a project with no codes."""
        from src.contexts.coding.core.invariants import is_code_name_unique

        assert is_code_name_unique("Theme", []) is True

    def test_detects_duplicate(self):
        """Duplicate names should be detected (case-insensitive)."""
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.invariants import is_code_name_unique
        from src.shared import CodeId

        existing = [Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))]

        assert is_code_name_unique("Theme", existing) is False
        assert is_code_name_unique("theme", existing) is False
        assert is_code_name_unique("THEME", existing) is False
        assert is_code_name_unique("Different", existing) is True

    def test_excludes_self_on_rename(self):
        """Should exclude the code being renamed."""
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.invariants import is_code_name_unique
        from src.shared import CodeId

        existing = [
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
            Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0)),
        ]

        # Same name is allowed when it's the same code (rename to same name)
        assert (
            is_code_name_unique("Theme", existing, exclude_code_id=CodeId(value=1))
            is True
        )
        # But not if another code has that name
        assert (
            is_code_name_unique("Pattern", existing, exclude_code_id=CodeId(value=1))
            is False
        )


class TestIsValidColor:
    """Tests for is_valid_color invariant."""

    def test_accepts_valid_colors(self):
        """Valid RGB values should be accepted."""
        from src.contexts.coding.core.entities import Color
        from src.contexts.coding.core.invariants import is_valid_color

        assert is_valid_color(Color(0, 0, 0)) is True
        assert is_valid_color(Color(255, 255, 255)) is True
        assert is_valid_color(Color(128, 64, 32)) is True

    def test_accepts_boundary_values(self):
        """Boundary values (0 and 255) should be valid."""
        from src.contexts.coding.core.entities import Color
        from src.contexts.coding.core.invariants import is_valid_color

        assert is_valid_color(Color(0, 128, 255)) is True


class TestCanCodeBeDeleted:
    """Tests for can_code_be_deleted invariant."""

    def test_allows_deletion_without_segments(self):
        """Code without segments can be deleted."""
        from src.contexts.coding.core.invariants import can_code_be_deleted
        from src.shared import CodeId

        assert can_code_be_deleted(CodeId(value=1), []) is True

    def test_prevents_deletion_with_segments(self):
        """Code with segments cannot be deleted by default."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.invariants import can_code_be_deleted
        from src.shared import CodeId, SegmentId, SourceId

        segments = [
            TextSegment(
                id=SegmentId(value=1),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=0, end=10),
                selected_text="test text",
            )
        ]

        assert can_code_be_deleted(CodeId(value=1), segments) is False

    def test_allows_deletion_with_segments_when_forced(self):
        """Code with segments can be deleted when allow_with_segments=True."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.invariants import can_code_be_deleted
        from src.shared import CodeId, SegmentId, SourceId

        segments = [
            TextSegment(
                id=SegmentId(value=1),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=0, end=10),
                selected_text="test text",
            )
        ]

        assert (
            can_code_be_deleted(CodeId(value=1), segments, allow_with_segments=True)
            is True
        )


class TestAreCodesMergeable:
    """Tests for are_codes_mergeable invariant."""

    def test_allows_merge_of_different_codes(self):
        """Two different existing codes can be merged."""
        from src.contexts.coding.core.invariants import are_codes_mergeable
        from src.shared import CodeId

        def code_exists(code_id: CodeId) -> bool:
            return code_id.value in (1, 2)

        assert (
            are_codes_mergeable(CodeId(value=1), CodeId(value=2), code_exists) is True
        )

    def test_prevents_merge_with_self(self):
        """Cannot merge a code with itself."""
        from src.contexts.coding.core.invariants import are_codes_mergeable
        from src.shared import CodeId

        def code_exists(code_id: CodeId) -> bool:
            return code_id.value == 1

        assert (
            are_codes_mergeable(CodeId(value=1), CodeId(value=1), code_exists) is False
        )

    def test_prevents_merge_when_source_not_found(self):
        """Cannot merge if source code doesn't exist."""
        from src.contexts.coding.core.invariants import are_codes_mergeable
        from src.shared import CodeId

        def code_exists(code_id: CodeId) -> bool:
            return code_id.value == 2

        assert (
            are_codes_mergeable(CodeId(value=1), CodeId(value=2), code_exists) is False
        )

    def test_prevents_merge_when_target_not_found(self):
        """Cannot merge if target code doesn't exist."""
        from src.contexts.coding.core.invariants import are_codes_mergeable
        from src.shared import CodeId

        def code_exists(code_id: CodeId) -> bool:
            return code_id.value == 1

        assert (
            are_codes_mergeable(CodeId(value=1), CodeId(value=2), code_exists) is False
        )


# ============================================================
# Category Invariant Tests
# ============================================================


class TestIsValidCategoryName:
    """Tests for is_valid_category_name invariant."""

    def test_accepts_normal_string(self):
        """Normal alphanumeric names should be valid."""
        from src.contexts.coding.core.invariants import is_valid_category_name

        assert is_valid_category_name("Themes") is True
        assert is_valid_category_name("Sub-Category") is True

    def test_rejects_empty_string(self):
        """Empty string should be invalid."""
        from src.contexts.coding.core.invariants import is_valid_category_name

        assert is_valid_category_name("") is False

    def test_rejects_whitespace_only(self):
        """Whitespace-only strings should be invalid."""
        from src.contexts.coding.core.invariants import is_valid_category_name

        assert is_valid_category_name("   ") is False

    def test_rejects_too_long(self):
        """Names exceeding 100 characters should be invalid."""
        from src.contexts.coding.core.invariants import is_valid_category_name

        assert is_valid_category_name("a" * 101) is False

    def test_accepts_max_length(self):
        """Names at exactly 100 characters should be valid."""
        from src.contexts.coding.core.invariants import is_valid_category_name

        assert is_valid_category_name("a" * 100) is True


class TestIsCategoryNameUnique:
    """Tests for is_category_name_unique invariant."""

    def test_unique_in_empty_project(self):
        """Any name is unique with no categories."""
        from src.contexts.coding.core.invariants import is_category_name_unique

        assert is_category_name_unique("Themes", []) is True

    def test_detects_duplicate(self):
        """Duplicate names should be detected (case-insensitive)."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import is_category_name_unique
        from src.shared import CategoryId

        existing = [Category(id=CategoryId(value=1), name="Themes")]

        assert is_category_name_unique("Themes", existing) is False
        assert is_category_name_unique("themes", existing) is False
        assert is_category_name_unique("Patterns", existing) is True


class TestIsCategoryHierarchyValid:
    """Tests for is_category_hierarchy_valid invariant."""

    def test_allows_move_to_root(self):
        """Moving to root (None parent) is always valid."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import is_category_hierarchy_valid
        from src.shared import CategoryId

        categories = [
            Category(id=CategoryId(value=1), name="Parent"),
            Category(
                id=CategoryId(value=2), name="Child", parent_id=CategoryId(value=1)
            ),
        ]

        assert (
            is_category_hierarchy_valid(CategoryId(value=2), None, categories) is True
        )

    def test_prevents_self_parent(self):
        """Cannot be your own parent."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import is_category_hierarchy_valid
        from src.shared import CategoryId

        categories = [Category(id=CategoryId(value=1), name="Category")]

        assert (
            is_category_hierarchy_valid(
                CategoryId(value=1), CategoryId(value=1), categories
            )
            is False
        )

    def test_allows_valid_parent(self):
        """Valid parent relationship should be allowed."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import is_category_hierarchy_valid
        from src.shared import CategoryId

        categories = [
            Category(id=CategoryId(value=1), name="Parent"),
            Category(id=CategoryId(value=2), name="Child"),
        ]

        assert (
            is_category_hierarchy_valid(
                CategoryId(value=2), CategoryId(value=1), categories
            )
            is True
        )


class TestCanCategoryBeDeleted:
    """Tests for can_category_be_deleted invariant."""

    def test_allows_deletion_of_empty_category(self):
        """Category without codes or children can be deleted."""
        from src.contexts.coding.core.invariants import can_category_be_deleted
        from src.shared import CategoryId

        assert can_category_be_deleted(CategoryId(value=1), [], []) is True

    def test_prevents_deletion_with_codes(self):
        """Category with codes cannot be deleted by default."""
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.invariants import can_category_be_deleted
        from src.shared import CategoryId, CodeId

        codes = [
            Code(
                id=CodeId(value=1),
                name="Theme",
                color=Color(255, 0, 0),
                category_id=CategoryId(value=1),
            )
        ]

        assert can_category_be_deleted(CategoryId(value=1), codes, []) is False

    def test_prevents_deletion_with_children(self):
        """Category with child categories cannot be deleted by default."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import can_category_be_deleted
        from src.shared import CategoryId

        categories = [
            Category(
                id=CategoryId(value=2), name="Child", parent_id=CategoryId(value=1)
            )
        ]

        assert can_category_be_deleted(CategoryId(value=1), [], categories) is False

    def test_allows_deletion_with_children_when_forced(self):
        """Category with children can be deleted when allow_with_children=True."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import can_category_be_deleted
        from src.shared import CategoryId

        categories = [
            Category(
                id=CategoryId(value=2), name="Child", parent_id=CategoryId(value=1)
            )
        ]

        assert (
            can_category_be_deleted(
                CategoryId(value=1), [], categories, allow_with_children=True
            )
            is True
        )


# ============================================================
# Segment Invariant Tests
# ============================================================


class TestIsValidTextPosition:
    """Tests for is_valid_text_position invariant."""

    def test_accepts_valid_position(self):
        """Valid positions within source bounds should be accepted."""
        from src.contexts.coding.core.entities import TextPosition
        from src.contexts.coding.core.invariants import is_valid_text_position

        position = TextPosition(start=0, end=10)
        assert is_valid_text_position(position, source_length=100) is True

    def test_accepts_position_at_end(self):
        """Position at exact end of source should be accepted."""
        from src.contexts.coding.core.entities import TextPosition
        from src.contexts.coding.core.invariants import is_valid_text_position

        position = TextPosition(start=90, end=100)
        assert is_valid_text_position(position, source_length=100) is True

    def test_rejects_position_beyond_end(self):
        """Position beyond source length should be rejected."""
        from src.contexts.coding.core.entities import TextPosition
        from src.contexts.coding.core.invariants import is_valid_text_position

        position = TextPosition(start=90, end=110)
        assert is_valid_text_position(position, source_length=100) is False


class TestIsValidImageRegion:
    """Tests for is_valid_image_region invariant."""

    def test_accepts_valid_region(self):
        """Valid region within image bounds should be accepted."""
        from src.contexts.coding.core.entities import ImageRegion
        from src.contexts.coding.core.invariants import is_valid_image_region

        region = ImageRegion(x=0, y=0, width=50, height=50)
        assert is_valid_image_region(region, image_width=100, image_height=100) is True

    def test_accepts_region_at_bounds(self):
        """Region exactly at image bounds should be accepted."""
        from src.contexts.coding.core.entities import ImageRegion
        from src.contexts.coding.core.invariants import is_valid_image_region

        region = ImageRegion(x=50, y=50, width=50, height=50)
        assert is_valid_image_region(region, image_width=100, image_height=100) is True

    def test_rejects_region_beyond_width(self):
        """Region extending beyond image width should be rejected."""
        from src.contexts.coding.core.entities import ImageRegion
        from src.contexts.coding.core.invariants import is_valid_image_region

        region = ImageRegion(x=80, y=0, width=50, height=50)
        assert is_valid_image_region(region, image_width=100, image_height=100) is False

    def test_rejects_region_beyond_height(self):
        """Region extending beyond image height should be rejected."""
        from src.contexts.coding.core.entities import ImageRegion
        from src.contexts.coding.core.invariants import is_valid_image_region

        region = ImageRegion(x=0, y=80, width=50, height=50)
        assert is_valid_image_region(region, image_width=100, image_height=100) is False


class TestIsValidTimeRange:
    """Tests for is_valid_time_range invariant."""

    def test_accepts_valid_range(self):
        """Valid time range within duration should be accepted."""
        from src.contexts.coding.core.entities import TimeRange
        from src.contexts.coding.core.invariants import is_valid_time_range

        time_range = TimeRange(start_ms=0, end_ms=5000)
        assert is_valid_time_range(time_range, duration_ms=10000) is True

    def test_accepts_range_at_duration(self):
        """Range ending at exact duration should be accepted."""
        from src.contexts.coding.core.entities import TimeRange
        from src.contexts.coding.core.invariants import is_valid_time_range

        time_range = TimeRange(start_ms=5000, end_ms=10000)
        assert is_valid_time_range(time_range, duration_ms=10000) is True

    def test_rejects_range_beyond_duration(self):
        """Range extending beyond duration should be rejected."""
        from src.contexts.coding.core.entities import TimeRange
        from src.contexts.coding.core.invariants import is_valid_time_range

        time_range = TimeRange(start_ms=5000, end_ms=15000)
        assert is_valid_time_range(time_range, duration_ms=10000) is False


class TestIsValidImportance:
    """Tests for is_valid_importance invariant."""

    def test_accepts_valid_values(self):
        """Valid importance values (0, 1, 2) should be accepted."""
        from src.contexts.coding.core.invariants import is_valid_importance

        assert is_valid_importance(0) is True
        assert is_valid_importance(1) is True
        assert is_valid_importance(2) is True

    def test_rejects_invalid_values(self):
        """Invalid importance values should be rejected."""
        from src.contexts.coding.core.invariants import is_valid_importance

        assert is_valid_importance(-1) is False
        assert is_valid_importance(3) is False
        assert is_valid_importance(100) is False


class TestDoesSegmentOverlap:
    """Tests for does_segment_overlap invariant."""

    def test_detects_overlap(self):
        """Should detect overlapping segments with same code."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.invariants import does_segment_overlap
        from src.shared import CodeId, SegmentId, SourceId

        existing = [
            TextSegment(
                id=SegmentId(value=1),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=10, end=20),
                selected_text="test",
            )
        ]

        new_position = TextPosition(start=15, end=25)
        assert does_segment_overlap(new_position, existing, CodeId(value=1)) is True

    def test_no_overlap_with_different_code(self):
        """Should not detect overlap with different code."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.invariants import does_segment_overlap
        from src.shared import CodeId, SegmentId, SourceId

        existing = [
            TextSegment(
                id=SegmentId(value=1),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=10, end=20),
                selected_text="test",
            )
        ]

        new_position = TextPosition(start=15, end=25)
        # Different code ID
        assert does_segment_overlap(new_position, existing, CodeId(value=2)) is False

    def test_no_overlap_when_adjacent(self):
        """Adjacent segments should not overlap."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.invariants import does_segment_overlap
        from src.shared import CodeId, SegmentId, SourceId

        existing = [
            TextSegment(
                id=SegmentId(value=1),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=10, end=20),
                selected_text="test",
            )
        ]

        new_position = TextPosition(start=20, end=30)
        assert does_segment_overlap(new_position, existing, CodeId(value=1)) is False


# ============================================================
# Cross-Entity Invariant Tests
# ============================================================


class TestDoesCodeExist:
    """Tests for does_code_exist invariant."""

    def test_finds_existing_code(self):
        """Should find code that exists."""
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.invariants import does_code_exist
        from src.shared import CodeId

        codes = [Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))]

        assert does_code_exist(CodeId(value=1), codes) is True

    def test_returns_false_for_missing_code(self):
        """Should return False for non-existent code."""
        from src.contexts.coding.core.invariants import does_code_exist
        from src.shared import CodeId

        assert does_code_exist(CodeId(value=999), []) is False


class TestDoesCategoryExist:
    """Tests for does_category_exist invariant."""

    def test_finds_existing_category(self):
        """Should find category that exists."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import does_category_exist
        from src.shared import CategoryId

        categories = [Category(id=CategoryId(value=1), name="Themes")]

        assert does_category_exist(CategoryId(value=1), categories) is True

    def test_returns_false_for_missing_category(self):
        """Should return False for non-existent category."""
        from src.contexts.coding.core.invariants import does_category_exist
        from src.shared import CategoryId

        assert does_category_exist(CategoryId(value=999), []) is False


class TestCountSegmentsForCode:
    """Tests for count_segments_for_code invariant."""

    def test_counts_segments(self):
        """Should count segments for a code."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.invariants import count_segments_for_code
        from src.shared import CodeId, SegmentId, SourceId

        segments = [
            TextSegment(
                id=SegmentId(value=1),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=0, end=10),
                selected_text="test",
            ),
            TextSegment(
                id=SegmentId(value=2),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=20, end=30),
                selected_text="test2",
            ),
            TextSegment(
                id=SegmentId(value=3),
                source_id=SourceId(value=1),
                code_id=CodeId(value=2),
                position=TextPosition(start=40, end=50),
                selected_text="test3",
            ),
        ]

        assert count_segments_for_code(CodeId(value=1), segments) == 2
        assert count_segments_for_code(CodeId(value=2), segments) == 1
        assert count_segments_for_code(CodeId(value=3), segments) == 0


class TestCountCodesInCategory:
    """Tests for count_codes_in_category invariant."""

    def test_counts_codes(self):
        """Should count codes in a category."""
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.invariants import count_codes_in_category
        from src.shared import CategoryId, CodeId

        codes = [
            Code(
                id=CodeId(value=1),
                name="Theme1",
                color=Color(255, 0, 0),
                category_id=CategoryId(value=1),
            ),
            Code(
                id=CodeId(value=2),
                name="Theme2",
                color=Color(0, 255, 0),
                category_id=CategoryId(value=1),
            ),
            Code(
                id=CodeId(value=3),
                name="Pattern",
                color=Color(0, 0, 255),
                category_id=CategoryId(value=2),
            ),
        ]

        assert count_codes_in_category(CategoryId(value=1), codes) == 2
        assert count_codes_in_category(CategoryId(value=2), codes) == 1
        assert count_codes_in_category(CategoryId(value=3), codes) == 0
