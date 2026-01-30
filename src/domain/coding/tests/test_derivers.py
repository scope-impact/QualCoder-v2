"""
Tests for coding domain derivers.

Derivers are pure functions that compose invariants and produce domain events.
Tests verify they return correct events for valid operations and appropriate
failures for invalid operations.
"""

import pytest

from src.domain.coding.derivers import (
    CategoryNotFound,
    CodingState,
    HasReferences,
    SameEntity,
    derive_apply_code_to_text,
    derive_change_code_color,
    derive_create_category,
    derive_create_code,
    derive_delete_category,
    derive_delete_code,
    derive_merge_codes,
    derive_move_code_to_category,
    derive_remove_segment,
    derive_rename_category,
    derive_rename_code,
    derive_update_segment_memo,
)
from src.domain.coding.entities import (
    Color,
)
from src.domain.coding.events import (
    CategoryCreated,
    CategoryDeleted,
    CategoryRenamed,
    CodeColorChanged,
    CodeCreated,
    CodeDeleted,
    CodeMovedToCategory,
    CodeRenamed,
    CodesMerged,
    SegmentCoded,
    SegmentMemoUpdated,
    SegmentUncoded,
)
from src.domain.shared.types import (
    CategoryId,
    CodeId,
    CodeNotFound,
    DuplicateName,
    EmptyName,
    Failure,
    InvalidPosition,
    SegmentId,
    SourceId,
    SourceNotFound,
)


class TestDeriveCreateCode:
    """Tests for derive_create_code deriver."""

    def test_creates_code_with_valid_inputs(self, empty_state: CodingState):
        """Should create CodeCreated event with valid inputs."""
        color = Color(red=100, green=150, blue=200)
        result = derive_create_code(
            name="New Theme",
            color=color,
            memo="Test memo",
            category_id=None,
            owner="user1",
            state=empty_state,
        )

        assert isinstance(result, CodeCreated)
        assert result.name == "New Theme"
        assert result.color == color
        assert result.memo == "Test memo"
        assert result.category_id is None
        assert result.owner == "user1"

    def test_fails_with_empty_name(self, empty_state: CodingState):
        """Should fail with EmptyName for empty names."""
        result = derive_create_code(
            name="",
            color=Color(red=100, green=100, blue=100),
            memo=None,
            category_id=None,
            owner="user1",
            state=empty_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, EmptyName)

    def test_fails_with_duplicate_name(self, populated_state: CodingState):
        """Should fail with DuplicateName for existing names."""
        result = derive_create_code(
            name="Theme A",  # Already exists in sample_codes
            color=Color(red=100, green=100, blue=100),
            memo=None,
            category_id=None,
            owner="user1",
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, DuplicateName)
        assert result.error.name == "Theme A"

    def test_fails_with_nonexistent_category(self, empty_state: CodingState):
        """Should fail with CategoryNotFound for invalid category."""
        result = derive_create_code(
            name="New Theme",
            color=Color(red=100, green=100, blue=100),
            memo=None,
            category_id=CategoryId(value=999),
            owner="user1",
            state=empty_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, CategoryNotFound)

    def test_creates_code_in_existing_category(self, populated_state: CodingState):
        """Should create code in existing category."""
        result = derive_create_code(
            name="New Theme",
            color=Color(red=100, green=100, blue=100),
            memo=None,
            category_id=CategoryId(value=1),  # Root Category exists
            owner="user1",
            state=populated_state,
        )

        assert isinstance(result, CodeCreated)
        assert result.category_id == CategoryId(value=1)


class TestDeriveRenameCode:
    """Tests for derive_rename_code deriver."""

    def test_renames_existing_code(self, populated_state: CodingState):
        """Should rename existing code with valid new name."""
        result = derive_rename_code(
            code_id=CodeId(value=1),
            new_name="Renamed Theme",
            state=populated_state,
        )

        assert isinstance(result, CodeRenamed)
        assert result.code_id == CodeId(value=1)
        assert result.old_name == "Theme A"
        assert result.new_name == "Renamed Theme"

    def test_fails_for_nonexistent_code(self, populated_state: CodingState):
        """Should fail for nonexistent code."""
        result = derive_rename_code(
            code_id=CodeId(value=999),
            new_name="New Name",
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, CodeNotFound)

    def test_fails_with_empty_name(self, populated_state: CodingState):
        """Should fail with empty new name."""
        result = derive_rename_code(
            code_id=CodeId(value=1),
            new_name="",
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, EmptyName)

    def test_fails_with_duplicate_name(self, populated_state: CodingState):
        """Should fail when renaming to existing name."""
        result = derive_rename_code(
            code_id=CodeId(value=1),
            new_name="Theme B",  # Already exists
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, DuplicateName)

    def test_allows_keeping_same_name(self, populated_state: CodingState):
        """Should allow keeping the same name (case-insensitive)."""
        result = derive_rename_code(
            code_id=CodeId(value=1),
            new_name="Theme A",  # Same name
            state=populated_state,
        )

        assert isinstance(result, CodeRenamed)


class TestDeriveChangeCodeColor:
    """Tests for derive_change_code_color deriver."""

    def test_changes_color_for_existing_code(self, populated_state: CodingState):
        """Should change color for existing code."""
        new_color = Color(red=255, green=0, blue=0)
        result = derive_change_code_color(
            code_id=CodeId(value=1),
            new_color=new_color,
            state=populated_state,
        )

        assert isinstance(result, CodeColorChanged)
        assert result.code_id == CodeId(value=1)
        assert result.new_color == new_color

    def test_fails_for_nonexistent_code(self, populated_state: CodingState):
        """Should fail for nonexistent code."""
        result = derive_change_code_color(
            code_id=CodeId(value=999),
            new_color=Color(red=255, green=0, blue=0),
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, CodeNotFound)


class TestDeriveDeleteCode:
    """Tests for derive_delete_code deriver."""

    def test_deletes_code_without_segments(self, populated_state: CodingState):
        """Should delete code with no segments."""
        # Code 3 has no segments in sample_segments
        result = derive_delete_code(
            code_id=CodeId(value=3),
            delete_segments=False,
            state=populated_state,
        )

        assert isinstance(result, CodeDeleted)
        assert result.code_id == CodeId(value=3)

    def test_fails_to_delete_code_with_segments_without_force(
        self, populated_state: CodingState
    ):
        """Should fail to delete code with segments unless forced."""
        # Code 1 has segments
        result = derive_delete_code(
            code_id=CodeId(value=1),
            delete_segments=False,
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, HasReferences)

    def test_deletes_code_with_segments_when_forced(self, populated_state: CodingState):
        """Should delete code with segments when forced."""
        result = derive_delete_code(
            code_id=CodeId(value=1),
            delete_segments=True,
            state=populated_state,
        )

        assert isinstance(result, CodeDeleted)
        assert result.segments_removed == 2  # Code 1 has 2 segments

    def test_fails_for_nonexistent_code(self, populated_state: CodingState):
        """Should fail for nonexistent code."""
        result = derive_delete_code(
            code_id=CodeId(value=999),
            delete_segments=False,
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, CodeNotFound)


class TestDeriveMergeCodes:
    """Tests for derive_merge_codes deriver."""

    def test_merges_two_existing_codes(self, populated_state: CodingState):
        """Should merge two existing codes."""
        result = derive_merge_codes(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            state=populated_state,
        )

        assert isinstance(result, CodesMerged)
        assert result.source_code_id == CodeId(value=1)
        assert result.target_code_id == CodeId(value=2)
        assert result.segments_moved == 2  # Code 1 has 2 segments

    def test_fails_to_merge_code_with_itself(self, populated_state: CodingState):
        """Should fail when merging code with itself."""
        result = derive_merge_codes(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=1),
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, SameEntity)

    def test_fails_with_nonexistent_source(self, populated_state: CodingState):
        """Should fail when source code doesn't exist."""
        result = derive_merge_codes(
            source_code_id=CodeId(value=999),
            target_code_id=CodeId(value=1),
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, CodeNotFound)

    def test_fails_with_nonexistent_target(self, populated_state: CodingState):
        """Should fail when target code doesn't exist."""
        result = derive_merge_codes(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=999),
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, CodeNotFound)


class TestDeriveMoveCodeToCategory:
    """Tests for derive_move_code_to_category deriver."""

    def test_moves_code_to_existing_category(self, populated_state: CodingState):
        """Should move code to existing category."""
        result = derive_move_code_to_category(
            code_id=CodeId(value=1),
            new_category_id=CategoryId(value=2),
            state=populated_state,
        )

        assert isinstance(result, CodeMovedToCategory)
        assert result.code_id == CodeId(value=1)
        assert result.new_category_id == CategoryId(value=2)

    def test_moves_code_to_uncategorized(self, populated_state: CodingState):
        """Should move code to uncategorized (None)."""
        result = derive_move_code_to_category(
            code_id=CodeId(value=2),  # Currently in category 1
            new_category_id=None,
            state=populated_state,
        )

        assert isinstance(result, CodeMovedToCategory)
        assert result.new_category_id is None

    def test_fails_with_nonexistent_category(self, populated_state: CodingState):
        """Should fail for nonexistent target category."""
        result = derive_move_code_to_category(
            code_id=CodeId(value=1),
            new_category_id=CategoryId(value=999),
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, CategoryNotFound)


class TestDeriveCategoryOperations:
    """Tests for category derivers."""

    def test_creates_root_category(self, empty_state: CodingState):
        """Should create root category."""
        result = derive_create_category(
            name="New Category",
            parent_id=None,
            memo="Test memo",
            owner="user1",
            state=empty_state,
        )

        assert isinstance(result, CategoryCreated)
        assert result.name == "New Category"
        assert result.parent_id is None

    def test_creates_child_category(self, populated_state: CodingState):
        """Should create child category under existing parent."""
        result = derive_create_category(
            name="New Child",
            parent_id=CategoryId(value=1),
            memo=None,
            owner="user1",
            state=populated_state,
        )

        assert isinstance(result, CategoryCreated)
        assert result.parent_id == CategoryId(value=1)

    def test_fails_to_create_with_duplicate_name(self, populated_state: CodingState):
        """Should fail with duplicate category name."""
        result = derive_create_category(
            name="Root Category",  # Already exists
            parent_id=None,
            memo=None,
            owner="user1",
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, DuplicateName)

    def test_renames_category(self, populated_state: CodingState):
        """Should rename existing category."""
        result = derive_rename_category(
            category_id=CategoryId(value=1),
            new_name="Renamed Category",
            state=populated_state,
        )

        assert isinstance(result, CategoryRenamed)
        assert result.new_name == "Renamed Category"

    def test_deletes_category(self, populated_state: CodingState):
        """Should delete existing category."""
        result = derive_delete_category(
            category_id=CategoryId(value=1),
            orphan_strategy="move_to_parent",
            state=populated_state,
        )

        assert isinstance(result, CategoryDeleted)
        assert result.category_id == CategoryId(value=1)


class TestDeriveApplyCodeToText:
    """Tests for derive_apply_code_to_text deriver."""

    def test_applies_code_to_valid_text_range(self, populated_state: CodingState):
        """Should apply code to valid text range."""
        result = derive_apply_code_to_text(
            code_id=CodeId(value=1),
            source_id=SourceId(value=1),
            start=200,
            end=300,
            selected_text="Selected text content",
            memo="Test annotation",
            importance=1,
            owner="user1",
            state=populated_state,
        )

        assert isinstance(result, SegmentCoded)
        assert result.code_id == CodeId(value=1)
        assert result.source_id == SourceId(value=1)
        assert result.position.start == 200
        assert result.position.end == 300

    def test_fails_with_nonexistent_code(self, populated_state: CodingState):
        """Should fail when code doesn't exist."""
        result = derive_apply_code_to_text(
            code_id=CodeId(value=999),
            source_id=SourceId(value=1),
            start=0,
            end=50,
            selected_text="Test",
            memo=None,
            importance=0,
            owner="user1",
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, CodeNotFound)

    def test_fails_with_invalid_position(self, populated_state: CodingState):
        """Should fail with position outside source bounds."""
        result = derive_apply_code_to_text(
            code_id=CodeId(value=1),
            source_id=SourceId(value=1),
            start=900,
            end=1100,  # Exceeds source_length of 1000
            selected_text="Test",
            memo=None,
            importance=0,
            owner="user1",
            state=populated_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, InvalidPosition)

    def test_fails_with_nonexistent_source(self, populated_state: CodingState):
        """Should fail when source doesn't exist."""
        state_no_source = CodingState(
            existing_codes=populated_state.existing_codes,
            existing_categories=populated_state.existing_categories,
            existing_segments=(),
            source_length=None,
            source_exists=False,
        )

        result = derive_apply_code_to_text(
            code_id=CodeId(value=1),
            source_id=SourceId(value=999),
            start=0,
            end=50,
            selected_text="Test",
            memo=None,
            importance=0,
            owner="user1",
            state=state_no_source,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.error, SourceNotFound)


class TestDeriveSegmentOperations:
    """Tests for segment derivers."""

    def test_removes_existing_segment(self, populated_state: CodingState):
        """Should remove existing segment."""
        result = derive_remove_segment(
            segment_id=SegmentId(value=1),
            state=populated_state,
        )

        assert isinstance(result, SegmentUncoded)
        assert result.segment_id == SegmentId(value=1)

    def test_fails_to_remove_nonexistent_segment(self, populated_state: CodingState):
        """Should fail for nonexistent segment."""
        result = derive_remove_segment(
            segment_id=SegmentId(value=999),
            state=populated_state,
        )

        assert isinstance(result, Failure)

    def test_updates_segment_memo(self, populated_state: CodingState):
        """Should update segment memo."""
        result = derive_update_segment_memo(
            segment_id=SegmentId(value=1),
            new_memo="Updated memo",
            state=populated_state,
        )

        assert isinstance(result, SegmentMemoUpdated)
        assert result.new_memo == "Updated memo"

    def test_clears_segment_memo(self, populated_state: CodingState):
        """Should clear segment memo (set to None)."""
        result = derive_update_segment_memo(
            segment_id=SegmentId(value=2),  # Has a memo
            new_memo=None,
            state=populated_state,
        )

        assert isinstance(result, SegmentMemoUpdated)
        assert result.new_memo is None


class TestCodingStateImmutability:
    """Tests verifying CodingState immutability."""

    def test_state_is_frozen(self, populated_state: CodingState):
        """CodingState should be immutable."""
        with pytest.raises(AttributeError):  # FrozenInstanceError
            populated_state.source_length = 9999

    def test_state_tuples_are_immutable(self, populated_state: CodingState):
        """State collections should be immutable tuples."""
        assert isinstance(populated_state.existing_codes, tuple)
        assert isinstance(populated_state.existing_categories, tuple)
        assert isinstance(populated_state.existing_segments, tuple)
