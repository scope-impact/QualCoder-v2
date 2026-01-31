"""
Tests for coding domain invariants.

Invariants are pure predicate functions that validate business rules.
Tests verify they correctly identify valid and invalid states.
"""

import pytest

pytestmark = pytest.mark.unit  # All tests in this module are unit tests

from src.domain.coding.entities import (
    Category,
    Code,
    Color,
    ImageRegion,
    TextPosition,
    TextSegment,
    TimeRange,
)
from src.domain.coding.invariants import (
    are_codes_mergeable,
    can_category_be_deleted,
    can_code_be_deleted,
    count_codes_in_category,
    count_segments_for_code,
    does_category_exist,
    # Cross-entity invariants
    does_code_exist,
    does_segment_overlap,
    # Category invariants
    is_category_hierarchy_valid,
    is_code_name_unique,
    # Code invariants
    is_valid_code_name,
    is_valid_color,
    is_valid_image_region,
    is_valid_importance,
    # Segment invariants
    is_valid_text_position,
    is_valid_time_range,
)
from src.domain.shared.types import CategoryId, CodeId


class TestCodeNameInvariants:
    """Tests for code name validation."""

    def test_valid_code_name_accepts_normal_string(self):
        """Normal alphanumeric names should be valid."""
        assert is_valid_code_name("Theme A") is True
        assert is_valid_code_name("code-123") is True
        assert is_valid_code_name("My_Code") is True

    def test_valid_code_name_rejects_empty_string(self):
        """Empty string should be invalid."""
        assert is_valid_code_name("") is False

    def test_valid_code_name_rejects_whitespace_only(self):
        """Whitespace-only strings should be invalid."""
        assert is_valid_code_name("   ") is False
        assert is_valid_code_name("\t\n") is False

    def test_valid_code_name_accepts_max_length(self):
        """Names up to 100 characters should be valid."""
        assert is_valid_code_name("A" * 100) is True

    def test_valid_code_name_rejects_over_max_length(self):
        """Names over 100 characters should be invalid."""
        assert is_valid_code_name("A" * 101) is False


class TestCodeNameUniqueness:
    """Tests for code name uniqueness validation."""

    def test_unique_name_in_empty_collection(self):
        """Any name is unique in empty collection."""
        assert is_code_name_unique("Theme A", []) is True

    def test_duplicate_name_detected(self, sample_codes: list[Code]):
        """Exact duplicate names should be detected."""
        assert is_code_name_unique("Theme A", sample_codes) is False

    def test_case_insensitive_duplicate_detected(self, sample_codes: list[Code]):
        """Case-insensitive duplicates should be detected."""
        assert is_code_name_unique("theme a", sample_codes) is False
        assert is_code_name_unique("THEME A", sample_codes) is False

    def test_unique_name_accepted(self, sample_codes: list[Code]):
        """Truly unique names should be accepted."""
        assert is_code_name_unique("Theme D", sample_codes) is True

    def test_exclude_code_id_allows_self_rename(self, sample_codes: list[Code]):
        """Excluding own ID allows keeping same name during rename."""
        # Theme A has CodeId(1) - should allow keeping its own name
        assert (
            is_code_name_unique(
                "Theme A", sample_codes, exclude_code_id=CodeId(value=1)
            )
            is True
        )

    def test_exclude_code_id_still_detects_other_duplicates(
        self, sample_codes: list[Code]
    ):
        """Excluding own ID should still detect duplicates with other codes."""
        # Try to rename code 1 to "Theme B" which exists as code 2
        assert (
            is_code_name_unique(
                "Theme B", sample_codes, exclude_code_id=CodeId(value=1)
            )
            is False
        )


class TestColorInvariants:
    """Tests for color validation."""

    def test_valid_color_accepts_valid_rgb(self):
        """Valid RGB values 0-255 should be accepted."""
        assert is_valid_color(Color(red=0, green=0, blue=0)) is True
        assert is_valid_color(Color(red=255, green=255, blue=255)) is True
        assert is_valid_color(Color(red=128, green=64, blue=192)) is True


class TestCodeDeletionInvariants:
    """Tests for code deletion validation."""

    def test_code_without_segments_can_be_deleted(self):
        """Codes with no segments can be deleted."""
        assert can_code_be_deleted(CodeId(value=99), []) is True

    def test_code_with_segments_cannot_be_deleted_by_default(
        self, sample_segments: list[TextSegment]
    ):
        """Codes with segments cannot be deleted without force flag."""
        # Code 1 has segments in sample_segments
        assert can_code_be_deleted(CodeId(value=1), sample_segments) is False

    def test_code_with_segments_can_be_deleted_with_force(
        self, sample_segments: list[TextSegment]
    ):
        """Codes with segments can be deleted with force flag."""
        assert (
            can_code_be_deleted(
                CodeId(value=1), sample_segments, allow_with_segments=True
            )
            is True
        )


class TestCodeMergeInvariants:
    """Tests for code merge validation."""

    def test_cannot_merge_code_with_itself(self):
        """A code cannot be merged with itself."""
        code_id = CodeId(value=1)

        def exists_fn(_id):
            return True

        assert are_codes_mergeable(code_id, code_id, exists_fn) is False

    def test_cannot_merge_nonexistent_source(self):
        """Cannot merge from a nonexistent code."""

        def exists_fn(id):
            return id.value == 2  # Only code 2 exists

        assert are_codes_mergeable(CodeId(value=1), CodeId(value=2), exists_fn) is False

    def test_cannot_merge_to_nonexistent_target(self):
        """Cannot merge into a nonexistent code."""

        def exists_fn(id):
            return id.value == 1  # Only code 1 exists

        assert are_codes_mergeable(CodeId(value=1), CodeId(value=2), exists_fn) is False

    def test_can_merge_existing_codes(self):
        """Two existing different codes can be merged."""

        def exists_fn(_id):
            return True

        assert are_codes_mergeable(CodeId(value=1), CodeId(value=2), exists_fn) is True


class TestCategoryHierarchyInvariants:
    """Tests for category hierarchy validation."""

    def test_move_to_root_always_valid(self, sample_categories: list[Category]):
        """Moving any category to root should be valid."""
        assert (
            is_category_hierarchy_valid(
                CategoryId(value=3),  # Grandchild
                None,  # Move to root
                sample_categories,
            )
            is True
        )

    def test_cannot_be_own_parent(self, sample_categories: list[Category]):
        """A category cannot be its own parent."""
        assert (
            is_category_hierarchy_valid(
                CategoryId(value=1),
                CategoryId(value=1),  # Self-parent
                sample_categories,
            )
            is False
        )

    def test_cannot_create_cycle_parent_to_child(
        self, sample_categories: list[Category]
    ):
        """Cannot move a parent under its child (creates cycle)."""
        # Root (1) -> Child (2) -> Grandchild (3)
        # Try to make Grandchild the parent of Root
        assert (
            is_category_hierarchy_valid(
                CategoryId(value=1),  # Root
                CategoryId(value=3),  # Grandchild as new parent
                sample_categories,
            )
            is False
        )

    def test_valid_reparenting(self, sample_categories: list[Category]):
        """Valid reparenting should be allowed."""
        # Move Grandchild directly under Root (skip Child)
        assert (
            is_category_hierarchy_valid(
                CategoryId(value=3),  # Grandchild
                CategoryId(value=1),  # Root as new parent
                sample_categories,
            )
            is True
        )


class TestCategoryDeletionInvariants:
    """Tests for category deletion validation."""

    def test_empty_category_can_be_deleted(self):
        """Empty categories can be deleted."""
        assert (
            can_category_be_deleted(
                CategoryId(value=99),
                codes=[],
                categories=[],
            )
            is True
        )

    def test_category_with_codes_cannot_be_deleted(self, sample_codes: list[Code]):
        """Categories with codes cannot be deleted by default."""
        # Category 1 has codes in sample_codes
        assert (
            can_category_be_deleted(
                CategoryId(value=1),
                codes=sample_codes,
                categories=[],
            )
            is False
        )

    def test_category_with_children_cannot_be_deleted(
        self, sample_categories: list[Category]
    ):
        """Categories with child categories cannot be deleted by default."""
        # Category 1 is parent of Category 2
        assert (
            can_category_be_deleted(
                CategoryId(value=1),
                codes=[],
                categories=sample_categories,
            )
            is False
        )

    def test_category_with_codes_can_be_deleted_with_force(
        self, sample_codes: list[Code]
    ):
        """Categories with codes can be deleted with force flag."""
        assert (
            can_category_be_deleted(
                CategoryId(value=1),
                codes=sample_codes,
                categories=[],
                allow_with_children=True,
            )
            is True
        )


class TestSegmentPositionInvariants:
    """Tests for segment position validation."""

    def test_valid_text_position_within_bounds(self):
        """Positions within source bounds should be valid."""
        position = TextPosition(start=10, end=50)
        assert is_valid_text_position(position, source_length=100) is True

    def test_invalid_position_start_out_of_bounds(self):
        """Positions starting before 0 should be invalid."""
        position = TextPosition(start=0, end=50)
        # Position is valid but source length is too short
        assert is_valid_text_position(position, source_length=25) is False

    def test_invalid_position_end_exceeds_length(self):
        """Positions ending after source length should be invalid."""
        position = TextPosition(start=0, end=100)
        assert is_valid_text_position(position, source_length=50) is False

    def test_valid_image_region_within_bounds(self):
        """Image regions within bounds should be valid."""
        region = ImageRegion(x=10, y=10, width=50, height=50)
        assert is_valid_image_region(region, image_width=100, image_height=100) is True

    def test_invalid_image_region_exceeds_bounds(self):
        """Image regions exceeding bounds should be invalid."""
        region = ImageRegion(x=10, y=10, width=100, height=50)
        assert is_valid_image_region(region, image_width=100, image_height=100) is False

    def test_valid_time_range_within_duration(self):
        """Time ranges within duration should be valid."""
        time_range = TimeRange(start_ms=1000, end_ms=5000)
        assert is_valid_time_range(time_range, duration_ms=10000) is True

    def test_invalid_time_range_exceeds_duration(self):
        """Time ranges exceeding duration should be invalid."""
        time_range = TimeRange(start_ms=5000, end_ms=15000)
        assert is_valid_time_range(time_range, duration_ms=10000) is False


class TestImportanceInvariants:
    """Tests for importance level validation."""

    def test_valid_importance_values(self):
        """Valid importance values (0, 1, 2) should pass."""
        assert is_valid_importance(0) is True
        assert is_valid_importance(1) is True
        assert is_valid_importance(2) is True

    def test_invalid_importance_values(self):
        """Invalid importance values should fail."""
        assert is_valid_importance(-1) is False
        assert is_valid_importance(3) is False
        assert is_valid_importance(100) is False


class TestSegmentOverlapInvariants:
    """Tests for segment overlap detection."""

    def test_no_overlap_with_empty_collection(self):
        """No overlaps in empty collection."""
        position = TextPosition(start=0, end=50)
        assert does_segment_overlap(position, [], CodeId(value=1)) is False

    def test_overlap_detected_same_code(self, sample_segments: list[TextSegment]):
        """Overlapping segments with same code should be detected."""
        # sample_segments has a segment at [0, 50) for code 1
        position = TextPosition(start=25, end=75)
        assert does_segment_overlap(position, sample_segments, CodeId(value=1)) is True

    def test_no_overlap_different_code(self, sample_segments: list[TextSegment]):
        """Overlapping positions with different code should not be detected."""
        # Position overlaps with code 1's segment, but checking for code 99
        position = TextPosition(start=25, end=75)
        assert (
            does_segment_overlap(position, sample_segments, CodeId(value=99)) is False
        )

    def test_no_overlap_non_overlapping_position(
        self, sample_segments: list[TextSegment]
    ):
        """Non-overlapping positions should not be detected."""
        # sample_segments has segments at [0,50) and [100,150) for code 1
        position = TextPosition(start=60, end=90)
        assert does_segment_overlap(position, sample_segments, CodeId(value=1)) is False


class TestCrossEntityInvariants:
    """Tests for cross-entity existence checks."""

    def test_code_exists_finds_existing(self, sample_codes: list[Code]):
        """Should find existing codes."""
        assert does_code_exist(CodeId(value=1), sample_codes) is True

    def test_code_exists_returns_false_for_missing(self, sample_codes: list[Code]):
        """Should return False for missing codes."""
        assert does_code_exist(CodeId(value=999), sample_codes) is False

    def test_category_exists_finds_existing(self, sample_categories: list[Category]):
        """Should find existing categories."""
        assert does_category_exist(CategoryId(value=1), sample_categories) is True

    def test_category_exists_returns_false_for_missing(
        self, sample_categories: list[Category]
    ):
        """Should return False for missing categories."""
        assert does_category_exist(CategoryId(value=999), sample_categories) is False

    def test_count_segments_for_code(self, sample_segments: list[TextSegment]):
        """Should correctly count segments for a code."""
        # Code 1 has 2 segments in sample_segments
        assert count_segments_for_code(CodeId(value=1), sample_segments) == 2
        # Code 2 has 1 segment
        assert count_segments_for_code(CodeId(value=2), sample_segments) == 1
        # Code 99 has no segments
        assert count_segments_for_code(CodeId(value=99), sample_segments) == 0

    def test_count_codes_in_category(self, sample_codes: list[Code]):
        """Should correctly count codes in a category."""
        # Category 1 has 2 codes (Theme B and Theme C)
        assert count_codes_in_category(CategoryId(value=1), sample_codes) == 2
        # No codes in category 99
        assert count_codes_in_category(CategoryId(value=99), sample_codes) == 0
