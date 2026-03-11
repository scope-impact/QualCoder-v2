"""
Coding Context: Invariant Tests

Tests for pure predicate functions that validate business rules for Coding.
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
# Code Invariant Tests
# ============================================================


class TestIsValidCodeName:
    """Tests for is_valid_code_name invariant."""

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("Theme", True),
            ("Emerging-Pattern", True),
            ("Code_With_Numbers_123", True),
            ("a" * 100, True),
            ("", False),
            ("   ", False),
            ("\t\n", False),
            ("a" * 101, False),
        ],
    )
    def test_validates_code_names(self, name, expected):
        """Valid names are accepted; empty, whitespace-only, and too-long names are rejected."""
        from src.contexts.coding.core.invariants import is_valid_code_name

        assert is_valid_code_name(name) is expected


class TestIsCodeNameUnique:
    """Tests for is_code_name_unique invariant."""

    def test_uniqueness_and_case_insensitive_duplicate(self):
        """Detects duplicates case-insensitively; any name is unique in empty list."""
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.invariants import is_code_name_unique
        from src.shared import CodeId

        assert is_code_name_unique("Theme", []) is True

        existing = [Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0))]

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
            Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
            Code(id=CodeId(value="2"), name="Pattern", color=Color(0, 255, 0)),
        ]

        # Same name is allowed when it's the same code (rename to same name)
        assert (
            is_code_name_unique("Theme", existing, exclude_code_id=CodeId(value="1"))
            is True
        )
        # But not if another code has that name
        assert (
            is_code_name_unique("Pattern", existing, exclude_code_id=CodeId(value="1"))
            is False
        )


class TestCanCodeBeDeleted:
    """Tests for can_code_be_deleted invariant."""

    def test_deletion_rules(self):
        """Code without segments can be deleted; with segments blocked unless forced."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.invariants import can_code_be_deleted
        from src.shared import CodeId, SegmentId, SourceId

        assert can_code_be_deleted(CodeId(value="1"), []) is True

        segments = [
            TextSegment(
                id=SegmentId(value="1"),
                source_id=SourceId(value="1"),
                code_id=CodeId(value="1"),
                position=TextPosition(start=0, end=10),
                selected_text="test text",
            )
        ]

        assert can_code_be_deleted(CodeId(value="1"), segments) is False
        assert (
            can_code_be_deleted(CodeId(value="1"), segments, allow_with_segments=True)
            is True
        )


class TestAreCodesMergeable:
    """Tests for are_codes_mergeable invariant."""

    def test_allows_merge_of_different_existing_codes(self):
        """Two different existing codes can be merged."""
        from src.contexts.coding.core.invariants import are_codes_mergeable
        from src.shared import CodeId

        def code_exists(code_id: CodeId) -> bool:
            return code_id.value in ("1", "2")

        assert (
            are_codes_mergeable(CodeId(value="1"), CodeId(value="2"), code_exists)
            is True
        )

    @pytest.mark.parametrize(
        "source_id, target_id, existing_ids",
        [
            ("1", "1", {"1"}),  # self-merge
            ("1", "2", {"2"}),  # source not found
            ("1", "2", {"1"}),  # target not found
        ],
    )
    def test_prevents_invalid_merges(self, source_id, target_id, existing_ids):
        """Cannot merge with self, or when source/target don't exist."""
        from src.contexts.coding.core.invariants import are_codes_mergeable
        from src.shared import CodeId

        def code_exists(code_id: CodeId) -> bool:
            return code_id.value in existing_ids

        assert (
            are_codes_mergeable(
                CodeId(value=source_id), CodeId(value=target_id), code_exists
            )
            is False
        )


# ============================================================
# Category Invariant Tests
# ============================================================


class TestIsValidCategoryName:
    """Tests for is_valid_category_name invariant."""

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("Themes", True),
            ("Sub-Category", True),
            ("a" * 100, True),
            ("", False),
            ("   ", False),
            ("a" * 101, False),
        ],
    )
    def test_validates_category_names(self, name, expected):
        """Valid names accepted; empty, whitespace-only, and too-long rejected."""
        from src.contexts.coding.core.invariants import is_valid_category_name

        assert is_valid_category_name(name) is expected


class TestIsCategoryNameUnique:
    """Tests for is_category_name_unique invariant."""

    def test_uniqueness_and_case_insensitive_duplicate(self):
        """Any name is unique with no categories; duplicates detected case-insensitively."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import is_category_name_unique
        from src.shared import CategoryId

        assert is_category_name_unique("Themes", []) is True

        existing = [Category(id=CategoryId(value="1"), name="Themes")]

        assert is_category_name_unique("Themes", existing) is False
        assert is_category_name_unique("themes", existing) is False
        assert is_category_name_unique("Patterns", existing) is True


class TestIsCategoryHierarchyValid:
    """Tests for is_category_hierarchy_valid invariant."""

    def test_hierarchy_rules(self):
        """Move to root is valid; self-parent is invalid; valid parent is allowed."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import is_category_hierarchy_valid
        from src.shared import CategoryId

        categories = [
            Category(id=CategoryId(value="1"), name="Parent"),
            Category(
                id=CategoryId(value="2"), name="Child", parent_id=CategoryId(value="1")
            ),
        ]

        # Move to root
        assert (
            is_category_hierarchy_valid(CategoryId(value="2"), None, categories) is True
        )
        # Self-parent
        assert (
            is_category_hierarchy_valid(
                CategoryId(value="1"), CategoryId(value="1"), categories
            )
            is False
        )
        # Valid parent
        assert (
            is_category_hierarchy_valid(
                CategoryId(value="2"), CategoryId(value="1"), categories
            )
            is True
        )


class TestCanCategoryBeDeleted:
    """Tests for can_category_be_deleted invariant."""

    def test_allows_deletion_of_empty_category(self):
        """Category without codes or children can be deleted."""
        from src.contexts.coding.core.invariants import can_category_be_deleted
        from src.shared import CategoryId

        assert can_category_be_deleted(CategoryId(value="1"), [], []) is True

    def test_prevents_deletion_with_codes(self):
        """Category with codes cannot be deleted by default."""
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.invariants import can_category_be_deleted
        from src.shared import CategoryId, CodeId

        codes = [
            Code(
                id=CodeId(value="1"),
                name="Theme",
                color=Color(255, 0, 0),
                category_id=CategoryId(value="1"),
            )
        ]

        assert can_category_be_deleted(CategoryId(value="1"), codes, []) is False

    def test_children_block_unless_forced(self):
        """Category with children blocked by default; allowed when forced."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import can_category_be_deleted
        from src.shared import CategoryId

        categories = [
            Category(
                id=CategoryId(value="2"), name="Child", parent_id=CategoryId(value="1")
            )
        ]

        assert can_category_be_deleted(CategoryId(value="1"), [], categories) is False
        assert (
            can_category_be_deleted(
                CategoryId(value="1"), [], categories, allow_with_children=True
            )
            is True
        )


# ============================================================
# Segment Invariant Tests
# ============================================================


class TestIsValidTextPosition:
    """Tests for is_valid_text_position invariant."""

    @pytest.mark.parametrize(
        "start, end, source_length, expected",
        [
            (0, 10, 100, True),
            (90, 100, 100, True),
            (90, 110, 100, False),
        ],
    )
    def test_validates_text_positions(self, start, end, source_length, expected):
        """Positions within bounds accepted; beyond bounds rejected."""
        from src.contexts.coding.core.entities import TextPosition
        from src.contexts.coding.core.invariants import is_valid_text_position

        position = TextPosition(start=start, end=end)
        assert is_valid_text_position(position, source_length=source_length) is expected


class TestIsValidImageRegion:
    """Tests for is_valid_image_region invariant."""

    @pytest.mark.parametrize(
        "x, y, width, height, expected",
        [
            (0, 0, 50, 50, True),
            (50, 50, 50, 50, True),
            (80, 0, 50, 50, False),
            (0, 80, 50, 50, False),
        ],
    )
    def test_validates_image_regions(self, x, y, width, height, expected):
        """Regions within bounds accepted; beyond width or height rejected."""
        from src.contexts.coding.core.entities import ImageRegion
        from src.contexts.coding.core.invariants import is_valid_image_region

        region = ImageRegion(x=x, y=y, width=width, height=height)
        assert (
            is_valid_image_region(region, image_width=100, image_height=100) is expected
        )


class TestIsValidTimeRange:
    """Tests for is_valid_time_range invariant."""

    @pytest.mark.parametrize(
        "start_ms, end_ms, duration_ms, expected",
        [
            (0, 5000, 10000, True),
            (5000, 10000, 10000, True),
            (5000, 15000, 10000, False),
        ],
    )
    def test_validates_time_ranges(self, start_ms, end_ms, duration_ms, expected):
        """Ranges within duration accepted; beyond duration rejected."""
        from src.contexts.coding.core.entities import TimeRange
        from src.contexts.coding.core.invariants import is_valid_time_range

        time_range = TimeRange(start_ms=start_ms, end_ms=end_ms)
        assert is_valid_time_range(time_range, duration_ms=duration_ms) is expected


class TestIsValidImportance:
    """Tests for is_valid_importance invariant."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            (0, True),
            (1, True),
            (2, True),
            (-1, False),
            (3, False),
            (100, False),
        ],
    )
    def test_validates_importance(self, value, expected):
        """Values 0-2 accepted; others rejected."""
        from src.contexts.coding.core.invariants import is_valid_importance

        assert is_valid_importance(value) is expected


class TestDoesSegmentOverlap:
    """Tests for does_segment_overlap invariant."""

    def test_overlap_detection(self):
        """Detects overlap with same code; no overlap with different code or adjacent."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.invariants import does_segment_overlap
        from src.shared import CodeId, SegmentId, SourceId

        existing = [
            TextSegment(
                id=SegmentId(value="1"),
                source_id=SourceId(value="1"),
                code_id=CodeId(value="1"),
                position=TextPosition(start=10, end=20),
                selected_text="test",
            )
        ]

        # Overlapping with same code
        assert does_segment_overlap(
            TextPosition(start=15, end=25), existing, CodeId(value="1")
        ) is True
        # Overlapping range but different code
        assert does_segment_overlap(
            TextPosition(start=15, end=25), existing, CodeId(value="2")
        ) is False
        # Adjacent (not overlapping) with same code
        assert does_segment_overlap(
            TextPosition(start=20, end=30), existing, CodeId(value="1")
        ) is False


# ============================================================
# Cross-Entity Invariant Tests
# ============================================================


class TestDoesCodeExist:
    """Tests for does_code_exist invariant."""

    @pytest.mark.parametrize(
        "code_id_val, codes_present, expected",
        [
            ("1", True, True),
            ("999", False, False),
        ],
    )
    def test_checks_code_existence(self, code_id_val, codes_present, expected):
        """Finds existing code; returns False for missing."""
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.invariants import does_code_exist
        from src.shared import CodeId

        codes = (
            [Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0))]
            if codes_present
            else []
        )
        assert does_code_exist(CodeId(value=code_id_val), codes) is expected


class TestDoesCategoryExist:
    """Tests for does_category_exist invariant."""

    @pytest.mark.parametrize(
        "cat_id_val, cats_present, expected",
        [
            ("1", True, True),
            ("999", False, False),
        ],
    )
    def test_checks_category_existence(self, cat_id_val, cats_present, expected):
        """Finds existing category; returns False for missing."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import does_category_exist
        from src.shared import CategoryId

        categories = (
            [Category(id=CategoryId(value="1"), name="Themes")]
            if cats_present
            else []
        )
        assert does_category_exist(CategoryId(value=cat_id_val), categories) is expected


class TestCountSegmentsForCode:
    """Tests for count_segments_for_code invariant."""

    def test_counts_segments(self):
        """Should count segments for a code."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.invariants import count_segments_for_code
        from src.shared import CodeId, SegmentId, SourceId

        segments = [
            TextSegment(
                id=SegmentId(value="1"),
                source_id=SourceId(value="1"),
                code_id=CodeId(value="1"),
                position=TextPosition(start=0, end=10),
                selected_text="test",
            ),
            TextSegment(
                id=SegmentId(value="2"),
                source_id=SourceId(value="1"),
                code_id=CodeId(value="1"),
                position=TextPosition(start=20, end=30),
                selected_text="test2",
            ),
            TextSegment(
                id=SegmentId(value="3"),
                source_id=SourceId(value="1"),
                code_id=CodeId(value="2"),
                position=TextPosition(start=40, end=50),
                selected_text="test3",
            ),
        ]

        assert count_segments_for_code(CodeId(value="1"), segments) == 2
        assert count_segments_for_code(CodeId(value="2"), segments) == 1
        assert count_segments_for_code(CodeId(value="3"), segments) == 0


class TestCountCodesInCategory:
    """Tests for count_codes_in_category invariant."""

    def test_counts_codes(self):
        """Should count codes in a category."""
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.invariants import count_codes_in_category
        from src.shared import CategoryId, CodeId

        codes = [
            Code(
                id=CodeId(value="1"),
                name="Theme1",
                color=Color(255, 0, 0),
                category_id=CategoryId(value="1"),
            ),
            Code(
                id=CodeId(value="2"),
                name="Theme2",
                color=Color(0, 255, 0),
                category_id=CategoryId(value="1"),
            ),
            Code(
                id=CodeId(value="3"),
                name="Pattern",
                color=Color(0, 0, 255),
                category_id=CategoryId(value="2"),
            ),
        ]

        assert count_codes_in_category(CategoryId(value="1"), codes) == 2
        assert count_codes_in_category(CategoryId(value="2"), codes) == 1
        assert count_codes_in_category(CategoryId(value="3"), codes) == 0
