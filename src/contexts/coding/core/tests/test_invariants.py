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


@allure.story("QC-028.01 Code Name Validation")
class TestCodeNameInvariants:
    """Tests for is_valid_code_name and is_code_name_unique invariants."""

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
    @allure.title(
        "Validates code names: accepts valid, rejects empty/whitespace/too-long"
    )
    def test_validates_code_names(self, name, expected):
        """Valid names are accepted; empty, whitespace-only, and too-long names are rejected."""
        from src.contexts.coding.core.invariants import is_valid_code_name

        assert is_valid_code_name(name) is expected

    @allure.title("Checks uniqueness case-insensitively and excludes self on rename")
    def test_uniqueness_and_self_exclusion(self):
        """Detects duplicates case-insensitively; excludes the code being renamed."""
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.invariants import is_code_name_unique
        from src.shared import CodeId

        assert is_code_name_unique("Theme", []) is True

        existing = [
            Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
            Code(id=CodeId(value="2"), name="Pattern", color=Color(0, 255, 0)),
        ]

        assert is_code_name_unique("Theme", existing) is False
        assert is_code_name_unique("theme", existing) is False
        assert is_code_name_unique("THEME", existing) is False
        assert is_code_name_unique("Different", existing) is True

        # Exclude self on rename
        assert (
            is_code_name_unique("Theme", existing, exclude_code_id=CodeId(value="1"))
            is True
        )
        assert (
            is_code_name_unique("Pattern", existing, exclude_code_id=CodeId(value="1"))
            is False
        )


@allure.story("QC-028.01 Code Deletion and Merge")
class TestCodeDeletionAndMerge:
    """Tests for can_code_be_deleted and are_codes_mergeable invariants."""

    @allure.title("Deletion rules: no segments ok, with segments blocked unless forced")
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

    @allure.title(
        "Merge rules: allows different existing codes, prevents invalid merges"
    )
    def test_merge_rules(self):
        """Two different existing codes can merge; self-merge and missing codes prevented."""
        from src.contexts.coding.core.invariants import are_codes_mergeable
        from src.shared import CodeId

        def code_exists(code_id: CodeId) -> bool:
            return code_id.value in ("1", "2")

        assert (
            are_codes_mergeable(CodeId(value="1"), CodeId(value="2"), code_exists)
            is True
        )
        assert (
            are_codes_mergeable(CodeId(value="1"), CodeId(value="1"), code_exists)
            is False
        )  # self

        def only_target(code_id: CodeId) -> bool:
            return code_id.value == "2"

        assert (
            are_codes_mergeable(CodeId(value="1"), CodeId(value="2"), only_target)
            is False
        )  # source missing

        def only_source(code_id: CodeId) -> bool:
            return code_id.value == "1"

        assert (
            are_codes_mergeable(CodeId(value="1"), CodeId(value="2"), only_source)
            is False
        )  # target missing


# ============================================================
# Category Invariant Tests
# ============================================================


@allure.story("QC-028.02 Category Validation")
class TestCategoryInvariants:
    """Tests for category name, uniqueness, hierarchy, and deletion invariants."""

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
    @allure.title("Validates category names")
    def test_validates_category_names(self, name, expected):
        """Valid names accepted; empty, whitespace-only, and too-long rejected."""
        from src.contexts.coding.core.invariants import is_valid_category_name

        assert is_valid_category_name(name) is expected

    @allure.title("Checks category name uniqueness case-insensitively")
    def test_category_name_uniqueness(self):
        """Any name unique with no categories; duplicates detected case-insensitively."""
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.invariants import is_category_name_unique
        from src.shared import CategoryId

        assert is_category_name_unique("Themes", []) is True

        existing = [Category(id=CategoryId(value="1"), name="Themes")]
        assert is_category_name_unique("Themes", existing) is False
        assert is_category_name_unique("themes", existing) is False
        assert is_category_name_unique("Patterns", existing) is True

    @allure.title(
        "Validates hierarchy: root ok, self-parent blocked, valid parent allowed"
    )
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

        assert (
            is_category_hierarchy_valid(CategoryId(value="2"), None, categories) is True
        )
        assert (
            is_category_hierarchy_valid(
                CategoryId(value="1"), CategoryId(value="1"), categories
            )
            is False
        )
        assert (
            is_category_hierarchy_valid(
                CategoryId(value="2"), CategoryId(value="1"), categories
            )
            is True
        )

    @allure.title("Deletion rules: empty ok, codes block, children block unless forced")
    def test_deletion_rules(self):
        """Category without codes/children can be deleted; codes/children block unless forced."""
        from src.contexts.coding.core.entities import Category, Code, Color
        from src.contexts.coding.core.invariants import can_category_be_deleted
        from src.shared import CategoryId, CodeId

        assert can_category_be_deleted(CategoryId(value="1"), [], []) is True

        codes = [
            Code(
                id=CodeId(value="1"),
                name="Theme",
                color=Color(255, 0, 0),
                category_id=CategoryId(value="1"),
            )
        ]
        assert can_category_be_deleted(CategoryId(value="1"), codes, []) is False

        children = [
            Category(
                id=CategoryId(value="2"), name="Child", parent_id=CategoryId(value="1")
            )
        ]
        assert can_category_be_deleted(CategoryId(value="1"), [], children) is False
        assert (
            can_category_be_deleted(
                CategoryId(value="1"), [], children, allow_with_children=True
            )
            is True
        )


# ============================================================
# Segment Invariant Tests
# ============================================================


@allure.story("QC-029.01 Segment Position Validation")
class TestSegmentPositionInvariants:
    """Tests for position, region, time range, and importance validation."""

    @pytest.mark.parametrize(
        "start, end, source_length, expected",
        [
            (0, 10, 100, True),
            (90, 100, 100, True),
            (90, 110, 100, False),
        ],
    )
    @allure.title("Validates text positions within source bounds")
    def test_validates_text_positions(self, start, end, source_length, expected):
        """Positions within bounds accepted; beyond bounds rejected."""
        from src.contexts.coding.core.entities import TextPosition
        from src.contexts.coding.core.invariants import is_valid_text_position

        position = TextPosition(start=start, end=end)
        assert is_valid_text_position(position, source_length=source_length) is expected

    @pytest.mark.parametrize(
        "x, y, width, height, expected",
        [
            (0, 0, 50, 50, True),
            (50, 50, 50, 50, True),
            (80, 0, 50, 50, False),
            (0, 80, 50, 50, False),
        ],
    )
    @allure.title("Validates image regions within image bounds")
    def test_validates_image_regions(self, x, y, width, height, expected):
        """Regions within bounds accepted; beyond width or height rejected."""
        from src.contexts.coding.core.entities import ImageRegion
        from src.contexts.coding.core.invariants import is_valid_image_region

        region = ImageRegion(x=x, y=y, width=width, height=height)
        assert (
            is_valid_image_region(region, image_width=100, image_height=100) is expected
        )

    @pytest.mark.parametrize(
        "start_ms, end_ms, duration_ms, expected",
        [
            (0, 5000, 10000, True),
            (5000, 10000, 10000, True),
            (5000, 15000, 10000, False),
        ],
    )
    @allure.title("Validates time ranges within media duration")
    def test_validates_time_ranges(self, start_ms, end_ms, duration_ms, expected):
        """Ranges within duration accepted; beyond duration rejected."""
        from src.contexts.coding.core.entities import TimeRange
        from src.contexts.coding.core.invariants import is_valid_time_range

        time_range = TimeRange(start_ms=start_ms, end_ms=end_ms)
        assert is_valid_time_range(time_range, duration_ms=duration_ms) is expected

    @pytest.mark.parametrize(
        "value, expected",
        [(0, True), (1, True), (2, True), (-1, False), (3, False), (100, False)],
    )
    @allure.title("Validates importance values 0-2")
    def test_validates_importance(self, value, expected):
        """Values 0-2 accepted; others rejected."""
        from src.contexts.coding.core.invariants import is_valid_importance

        assert is_valid_importance(value) is expected


@allure.story("QC-029.01 Segment Overlap Detection")
class TestSegmentOverlap:
    """Tests for does_segment_overlap invariant."""

    @allure.title(
        "Detects overlap with same code; no overlap with different code or adjacent"
    )
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

        assert (
            does_segment_overlap(
                TextPosition(start=15, end=25), existing, CodeId(value="1")
            )
            is True
        )
        assert (
            does_segment_overlap(
                TextPosition(start=15, end=25), existing, CodeId(value="2")
            )
            is False
        )
        assert (
            does_segment_overlap(
                TextPosition(start=20, end=30), existing, CodeId(value="1")
            )
            is False
        )


# ============================================================
# Cross-Entity Invariant Tests
# ============================================================


@allure.story("QC-028.01 Cross-Entity Existence and Counting")
class TestCrossEntityInvariants:
    """Tests for does_code_exist, does_category_exist, count_segments_for_code, count_codes_in_category."""

    @allure.title("Checks code and category existence")
    def test_entity_existence(self):
        """Finds existing code/category; returns False for missing."""
        from src.contexts.coding.core.entities import Category, Code, Color
        from src.contexts.coding.core.invariants import (
            does_category_exist,
            does_code_exist,
        )
        from src.shared import CategoryId, CodeId

        codes = [Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0))]
        assert does_code_exist(CodeId(value="1"), codes) is True
        assert does_code_exist(CodeId(value="999"), codes) is False

        categories = [Category(id=CategoryId(value="1"), name="Themes")]
        assert does_category_exist(CategoryId(value="1"), categories) is True
        assert does_category_exist(CategoryId(value="999"), categories) is False

    @allure.title("Counts segments for code and codes in category")
    def test_counting(self):
        """Should count segments for a code and codes in a category."""
        from src.contexts.coding.core.entities import (
            Code,
            Color,
            TextPosition,
            TextSegment,
        )
        from src.contexts.coding.core.invariants import (
            count_codes_in_category,
            count_segments_for_code,
        )
        from src.shared import CategoryId, CodeId, SegmentId, SourceId

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
