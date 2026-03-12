"""
Coding Context: Deriver Tests

Tests for pure functions that compose invariants and derive domain events.
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
# Code Deriver Tests
# ============================================================


@allure.story("QC-028.01 Create New Code")
class TestDeriveCreateCode:
    """Tests for derive_create_code deriver."""

    @allure.title("Creates code with valid inputs and rejects invalid inputs")
    def test_creates_and_rejects_invalid(self):
        """Should create CodeCreated event with valid inputs and reject invalid ones."""
        from src.contexts.coding.core.derivers import CodingState, derive_create_code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodeCreated
        from src.contexts.coding.core.failure_events import CodeNotCreated
        from src.shared import CategoryId, CodeId

        # Success case
        state = CodingState(existing_codes=())
        result = derive_create_code(
            name="Theme",
            color=Color(255, 128, 0),
            memo="A recurring theme in interviews",
            category_id=None,
            owner="user1",
            state=state,
        )
        assert isinstance(result, CodeCreated)
        assert result.name == "Theme"
        assert result.color == Color(255, 128, 0)
        assert result.memo == "A recurring theme in interviews"

        # Empty name
        result = derive_create_code(
            name="",
            color=Color(255, 0, 0),
            memo=None,
            category_id=None,
            owner=None,
            state=state,
        )
        assert isinstance(result, CodeNotCreated)
        assert result.reason == "EMPTY_NAME"

        # Whitespace name
        result = derive_create_code(
            name="   ",
            color=Color(255, 0, 0),
            memo=None,
            category_id=None,
            owner=None,
            state=state,
        )
        assert isinstance(result, CodeNotCreated)
        assert result.reason == "EMPTY_NAME"

        # Duplicate name
        state_dup = CodingState(
            existing_codes=(
                Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
            )
        )
        result = derive_create_code(
            name="Theme",
            color=Color(255, 0, 0),
            memo=None,
            category_id=None,
            owner=None,
            state=state_dup,
        )
        assert isinstance(result, CodeNotCreated)
        assert result.reason == "DUPLICATE_NAME"
        assert result.name == "Theme"

        # Invalid category
        result = derive_create_code(
            name="Theme",
            color=Color(255, 0, 0),
            memo=None,
            category_id=CategoryId(value="999"),
            owner=None,
            state=CodingState(existing_codes=(), existing_categories=()),
        )
        assert isinstance(result, CodeNotCreated)
        assert result.reason == "CATEGORY_NOT_FOUND"


@allure.story("QC-028.03 Rename and Recolor Codes")
class TestDeriveRenameCode:
    """Tests for derive_rename_code deriver."""

    @allure.title("Renames code and rejects invalid rename inputs")
    def test_renames_and_rejects_invalid(self):
        """Should create CodeRenamed event and reject invalid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_rename_code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodeRenamed
        from src.contexts.coding.core.failure_events import CodeNotRenamed
        from src.shared import CodeId

        existing = (
            Code(id=CodeId(value="1"), name="Old Name", color=Color(255, 0, 0)),
            Code(id=CodeId(value="2"), name="Pattern", color=Color(0, 255, 0)),
        )
        state = CodingState(existing_codes=existing)

        # Success
        result = derive_rename_code(
            code_id=CodeId(value="1"), new_name="New Name", state=state
        )
        assert isinstance(result, CodeRenamed)
        assert result.old_name == "Old Name"
        assert result.new_name == "New Name"

        # Not found
        result = derive_rename_code(
            code_id=CodeId(value="999"),
            new_name="New Name",
            state=CodingState(existing_codes=()),
        )
        assert isinstance(result, CodeNotRenamed)
        assert result.reason == "NOT_FOUND"

        # Empty name
        result = derive_rename_code(code_id=CodeId(value="1"), new_name="", state=state)
        assert isinstance(result, CodeNotRenamed)
        assert result.reason == "EMPTY_NAME"

        # Duplicate name
        result = derive_rename_code(
            code_id=CodeId(value="1"), new_name="Pattern", state=state
        )
        assert isinstance(result, CodeNotRenamed)
        assert result.reason == "DUPLICATE_NAME"


@allure.story("QC-028.03 Rename and Recolor Codes")
class TestDeriveChangeCodeColor:
    """Tests for derive_change_code_color deriver."""

    @allure.title("Changes code color and fails when code not found")
    def test_changes_color_and_fails_when_not_found(self):
        """Should change color with valid inputs and fail when not found."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_change_code_color,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodeColorChanged
        from src.contexts.coding.core.failure_events import CodeNotUpdated
        from src.shared import CodeId

        existing = (Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),)
        state = CodingState(existing_codes=existing)

        result = derive_change_code_color(
            code_id=CodeId(value="1"),
            new_color=Color(0, 255, 0),
            state=state,
        )
        assert isinstance(result, CodeColorChanged)
        assert result.old_color == Color(255, 0, 0)
        assert result.new_color == Color(0, 255, 0)

        result = derive_change_code_color(
            code_id=CodeId(value="999"),
            new_color=Color(0, 255, 0),
            state=CodingState(existing_codes=()),
        )
        assert isinstance(result, CodeNotUpdated)
        assert result.reason == "NOT_FOUND"


@allure.story("QC-028.01 Create New Code")
class TestDeriveUpdateCodeMemo:
    """Tests for derive_update_code_memo deriver."""

    @allure.title("Updates code memo and fails when code not found")
    def test_updates_memo_and_fails_when_not_found(self):
        """Should update memo with valid inputs and fail when not found."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_update_code_memo,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodeMemoUpdated
        from src.contexts.coding.core.failure_events import CodeNotUpdated
        from src.shared import CodeId

        existing = (
            Code(
                id=CodeId(value="1"),
                name="Theme",
                color=Color(255, 0, 0),
                memo="Old memo",
            ),
        )
        state = CodingState(existing_codes=existing)

        result = derive_update_code_memo(
            code_id=CodeId(value="1"), new_memo="New memo", state=state
        )
        assert isinstance(result, CodeMemoUpdated)
        assert result.old_memo == "Old memo"
        assert result.new_memo == "New memo"

        result = derive_update_code_memo(
            code_id=CodeId(value="999"),
            new_memo="New memo",
            state=CodingState(existing_codes=()),
        )
        assert isinstance(result, CodeNotUpdated)
        assert result.reason == "NOT_FOUND"


@allure.story("QC-028.01 Create New Code")
class TestDeriveDeleteCode:
    """Tests for derive_delete_code deriver."""

    @allure.title("Deletes code with/without segments and rejects invalid delete")
    def test_deletes_and_rejects_invalid(self):
        """Should delete code and reject when not found or has references."""
        from src.contexts.coding.core.derivers import CodingState, derive_delete_code
        from src.contexts.coding.core.entities import (
            Code,
            Color,
            TextPosition,
            TextSegment,
        )
        from src.contexts.coding.core.events import CodeDeleted
        from src.contexts.coding.core.failure_events import CodeNotDeleted
        from src.shared import CodeId, SegmentId, SourceId

        existing = (Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),)
        segment = TextSegment(
            id=SegmentId(value="1"),
            source_id=SourceId(value="1"),
            code_id=CodeId(value="1"),
            position=TextPosition(start=0, end=10),
            selected_text="test",
        )

        # Without segments
        result = derive_delete_code(
            code_id=CodeId(value="1"),
            delete_segments=False,
            state=CodingState(existing_codes=existing, existing_segments=()),
        )
        assert isinstance(result, CodeDeleted)
        assert result.name == "Theme"

        # With segments, forced
        result = derive_delete_code(
            code_id=CodeId(value="1"),
            delete_segments=True,
            state=CodingState(existing_codes=existing, existing_segments=(segment,)),
        )
        assert isinstance(result, CodeDeleted)
        assert result.segments_removed == 1

        # Not found
        result = derive_delete_code(
            code_id=CodeId(value="999"),
            delete_segments=False,
            state=CodingState(existing_codes=(), existing_segments=()),
        )
        assert isinstance(result, CodeNotDeleted)
        assert result.reason == "NOT_FOUND"

        # Has references without force
        result = derive_delete_code(
            code_id=CodeId(value="1"),
            delete_segments=False,
            state=CodingState(existing_codes=existing, existing_segments=(segment,)),
        )
        assert isinstance(result, CodeNotDeleted)
        assert result.reason == "HAS_REFERENCES"


@allure.story("QC-028.01 Create New Code")
class TestDeriveMergeCodes:
    """Tests for derive_merge_codes deriver."""

    @allure.title("Merges codes and rejects invalid merge inputs")
    def test_merges_and_rejects_invalid(self):
        """Should merge codes and reject self-merge or missing codes."""
        from src.contexts.coding.core.derivers import CodingState, derive_merge_codes
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodesMerged
        from src.contexts.coding.core.failure_events import CodesNotMerged
        from src.shared import CodeId

        existing = (
            Code(id=CodeId(value="1"), name="Source", color=Color(255, 0, 0)),
            Code(id=CodeId(value="2"), name="Target", color=Color(0, 255, 0)),
        )
        state = CodingState(existing_codes=existing)

        # Success
        result = derive_merge_codes(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            state=state,
        )
        assert isinstance(result, CodesMerged)
        assert result.source_code_id == CodeId(value="1")

        # Self-merge
        state_self = CodingState(
            existing_codes=(
                Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
            )
        )
        result = derive_merge_codes(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="1"),
            state=state_self,
        )
        assert isinstance(result, CodesNotMerged)
        assert result.reason == "SAME_CODE"

        # Source not found
        result = derive_merge_codes(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            state=CodingState(
                existing_codes=(
                    Code(id=CodeId(value="2"), name="Target", color=Color(0, 255, 0)),
                )
            ),
        )
        assert isinstance(result, CodesNotMerged)
        assert result.reason == "SOURCE_NOT_FOUND"

        # Target not found
        result = derive_merge_codes(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            state=CodingState(
                existing_codes=(
                    Code(id=CodeId(value="1"), name="Source", color=Color(255, 0, 0)),
                )
            ),
        )
        assert isinstance(result, CodesNotMerged)
        assert result.reason == "TARGET_NOT_FOUND"


@allure.story("QC-028.02 Organize Codes into Categories")
class TestDeriveMoveCodeToCategory:
    """Tests for derive_move_code_to_category deriver."""

    @allure.title("Moves code to category/root and rejects invalid inputs")
    def test_moves_and_rejects_invalid(self):
        """Should move code to category/root and reject when not found."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_move_code_to_category,
        )
        from src.contexts.coding.core.entities import Category, Code, Color
        from src.contexts.coding.core.events import CodeMovedToCategory
        from src.contexts.coding.core.failure_events import CodeNotMoved
        from src.shared import CategoryId, CodeId

        existing_codes = (
            Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
        )
        existing_categories = (Category(id=CategoryId(value="1"), name="Themes"),)
        state = CodingState(
            existing_codes=existing_codes, existing_categories=existing_categories
        )

        # Move to category
        result = derive_move_code_to_category(
            code_id=CodeId(value="1"),
            new_category_id=CategoryId(value="1"),
            state=state,
        )
        assert isinstance(result, CodeMovedToCategory)
        assert result.new_category_id == CategoryId(value="1")

        # Move to root
        existing_with_cat = (
            Code(
                id=CodeId(value="1"),
                name="Theme",
                color=Color(255, 0, 0),
                category_id=CategoryId(value="1"),
            ),
        )
        result = derive_move_code_to_category(
            code_id=CodeId(value="1"),
            new_category_id=None,
            state=CodingState(existing_codes=existing_with_cat),
        )
        assert isinstance(result, CodeMovedToCategory)
        assert result.new_category_id is None

        # Code not found
        result = derive_move_code_to_category(
            code_id=CodeId(value="999"),
            new_category_id=CategoryId(value="1"),
            state=CodingState(existing_codes=(), existing_categories=()),
        )
        assert isinstance(result, CodeNotMoved)
        assert result.reason == "CODE_NOT_FOUND"

        # Category not found
        result = derive_move_code_to_category(
            code_id=CodeId(value="1"),
            new_category_id=CategoryId(value="999"),
            state=CodingState(existing_codes=existing_codes, existing_categories=()),
        )
        assert isinstance(result, CodeNotMoved)
        assert result.reason == "CATEGORY_NOT_FOUND"


# ============================================================
# Category Deriver Tests
# ============================================================


@allure.story("QC-028.02 Organize Codes into Categories")
class TestDeriveCreateCategory:
    """Tests for derive_create_category deriver."""

    @allure.title("Creates category and rejects invalid inputs")
    def test_creates_and_rejects_invalid(self):
        """Should create category and reject invalid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_create_category,
        )
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.events import CategoryCreated
        from src.contexts.coding.core.failure_events import CategoryNotCreated
        from src.shared import CategoryId

        state = CodingState(existing_categories=())

        # Success
        result = derive_create_category(
            name="Themes",
            parent_id=None,
            memo="Main themes category",
            owner="user1",
            state=state,
        )
        assert isinstance(result, CategoryCreated)
        assert result.name == "Themes"

        # Empty name
        result = derive_create_category(
            name="", parent_id=None, memo=None, owner=None, state=state
        )
        assert isinstance(result, CategoryNotCreated)
        assert result.reason == "EMPTY_NAME"

        # Duplicate name
        state_dup = CodingState(
            existing_categories=(Category(id=CategoryId(value="1"), name="Themes"),)
        )
        result = derive_create_category(
            name="Themes", parent_id=None, memo=None, owner=None, state=state_dup
        )
        assert isinstance(result, CategoryNotCreated)
        assert result.reason == "DUPLICATE_NAME"

        # Invalid parent
        result = derive_create_category(
            name="Child",
            parent_id=CategoryId(value="999"),
            memo=None,
            owner=None,
            state=CodingState(existing_categories=()),
        )
        assert isinstance(result, CategoryNotCreated)
        assert result.reason == "PARENT_NOT_FOUND"


@allure.story("QC-028.02 Organize Codes into Categories")
class TestDeriveRenameCategory:
    """Tests for derive_rename_category deriver."""

    @allure.title("Renames category and fails when not found")
    def test_renames_category_and_fails_when_not_found(self):
        """Should rename category with valid inputs and fail when not found."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_rename_category,
        )
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.events import CategoryRenamed
        from src.contexts.coding.core.failure_events import CategoryNotRenamed
        from src.shared import CategoryId

        existing = (Category(id=CategoryId(value="1"), name="Old Name"),)
        state = CodingState(existing_categories=existing)

        result = derive_rename_category(
            category_id=CategoryId(value="1"), new_name="New Name", state=state
        )
        assert isinstance(result, CategoryRenamed)
        assert result.old_name == "Old Name"
        assert result.new_name == "New Name"

        result = derive_rename_category(
            category_id=CategoryId(value="999"),
            new_name="New Name",
            state=CodingState(existing_categories=()),
        )
        assert isinstance(result, CategoryNotRenamed)
        assert result.reason == "NOT_FOUND"


@allure.story("QC-028.02 Organize Codes into Categories")
class TestDeriveDeleteCategory:
    """Tests for derive_delete_category deriver."""

    @allure.title("Deletes category and fails when not found")
    def test_deletes_category_and_fails_when_not_found(self):
        """Should delete category with valid inputs and fail when not found."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_delete_category,
        )
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.events import CategoryDeleted
        from src.contexts.coding.core.failure_events import CategoryNotDeleted
        from src.shared import CategoryId

        existing = (Category(id=CategoryId(value="1"), name="Themes"),)
        state = CodingState(existing_categories=existing)

        result = derive_delete_category(
            category_id=CategoryId(value="1"),
            orphan_strategy="move_to_parent",
            state=state,
        )
        assert isinstance(result, CategoryDeleted)
        assert result.name == "Themes"

        result = derive_delete_category(
            category_id=CategoryId(value="999"),
            orphan_strategy="move_to_parent",
            state=CodingState(existing_categories=()),
        )
        assert isinstance(result, CategoryNotDeleted)
        assert result.reason == "NOT_FOUND"


# ============================================================
# Segment Deriver Tests
# ============================================================


@allure.story("QC-029.01 Apply Code to Text")
class TestDeriveApplyCodeToText:
    """Tests for derive_apply_code_to_text deriver."""

    @allure.title("Applies code to text and rejects invalid inputs")
    def test_applies_and_rejects_invalid(self):
        """Should create SegmentCoded event and reject invalid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_apply_code_to_text,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import SegmentCoded
        from src.contexts.coding.core.failure_events import SegmentNotCoded
        from src.shared import CodeId, SourceId

        existing_codes = (
            Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
        )

        # Success
        state = CodingState(
            existing_codes=existing_codes, source_length=100, source_exists=True
        )
        result = derive_apply_code_to_text(
            code_id=CodeId(value="1"),
            source_id=SourceId(value="1"),
            start=10,
            end=20,
            selected_text="sample text",
            memo="A note",
            importance=1,
            owner="user1",
            state=state,
        )
        assert isinstance(result, SegmentCoded)
        assert result.code_id == CodeId(value="1")

        # Code not found
        state_nc = CodingState(existing_codes=(), source_length=100, source_exists=True)
        result = derive_apply_code_to_text(
            code_id=CodeId(value="999"),
            source_id=SourceId(value="1"),
            start=10,
            end=20,
            selected_text="sample text",
            memo=None,
            importance=0,
            owner=None,
            state=state_nc,
        )
        assert isinstance(result, SegmentNotCoded)
        assert result.reason == "CODE_NOT_FOUND"

        # Source not found
        state_ns = CodingState(
            existing_codes=existing_codes, source_length=0, source_exists=False
        )
        result = derive_apply_code_to_text(
            code_id=CodeId(value="1"),
            source_id=SourceId(value="1"),
            start=10,
            end=20,
            selected_text="sample text",
            memo=None,
            importance=0,
            owner=None,
            state=state_ns,
        )
        assert isinstance(result, SegmentNotCoded)
        assert result.reason == "SOURCE_NOT_FOUND"

        # Invalid position
        state_ip = CodingState(
            existing_codes=existing_codes, source_length=50, source_exists=True
        )
        result = derive_apply_code_to_text(
            code_id=CodeId(value="1"),
            source_id=SourceId(value="1"),
            start=40,
            end=60,
            selected_text="sample text",
            memo=None,
            importance=0,
            owner=None,
            state=state_ip,
        )
        assert isinstance(result, SegmentNotCoded)
        assert result.reason == "INVALID_POSITION"


@allure.story("QC-029.01 Apply Code to Text")
class TestDeriveRemoveSegmentAndUpdateMemo:
    """Tests for derive_remove_segment and derive_update_segment_memo derivers."""

    @allure.title("Removes segment and updates memo, failing when not found")
    def test_removes_and_updates_memo(self):
        """Should remove segment, update memo, and fail when not found."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_remove_segment,
            derive_update_segment_memo,
        )
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.events import SegmentMemoUpdated, SegmentUncoded
        from src.contexts.coding.core.failure_events import (
            SegmentNotRemoved,
            SegmentNotUpdated,
        )
        from src.shared import CodeId, SegmentId, SourceId

        segment = TextSegment(
            id=SegmentId(value="1"),
            source_id=SourceId(value="1"),
            code_id=CodeId(value="1"),
            position=TextPosition(start=0, end=10),
            selected_text="test",
            memo="Old memo",
        )
        state = CodingState(existing_segments=(segment,))

        # Remove success
        result = derive_remove_segment(segment_id=SegmentId(value="1"), state=state)
        assert isinstance(result, SegmentUncoded)
        assert result.segment_id == SegmentId(value="1")

        # Remove not found
        result = derive_remove_segment(
            segment_id=SegmentId(value="999"),
            state=CodingState(existing_segments=()),
        )
        assert isinstance(result, SegmentNotRemoved)
        assert result.reason == "NOT_FOUND"

        # Update memo success
        result = derive_update_segment_memo(
            segment_id=SegmentId(value="1"),
            new_memo="New memo",
            state=state,
        )
        assert isinstance(result, SegmentMemoUpdated)
        assert result.old_memo == "Old memo"
        assert result.new_memo == "New memo"

        # Update memo not found
        result = derive_update_segment_memo(
            segment_id=SegmentId(value="999"),
            new_memo="New memo",
            state=CodingState(existing_segments=()),
        )
        assert isinstance(result, SegmentNotUpdated)
        assert result.reason == "NOT_FOUND"


# ============================================================
# Batch Deriver Tests
# ============================================================


@allure.story("QC-029.01 Apply Code to Text")
class TestDeriveBatchOperations:
    """Tests for derive_create_batch and derive_undo_batch derivers."""

    @allure.title("Creates and undoes batch, failing when not found")
    def test_creates_and_undoes_batch(self):
        """Should create and undo batch, failing when code or batch not found."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_create_batch,
            derive_undo_batch,
        )
        from src.contexts.coding.core.entities import (
            AutoCodeBatch,
            BatchId,
            Code,
            Color,
        )
        from src.contexts.coding.core.events import BatchCreated, BatchUndone
        from src.contexts.coding.core.failure_events import (
            BatchNotCreated,
            BatchNotUndone,
        )
        from src.shared import CodeId, SegmentId

        existing_codes = (
            Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
        )

        # Create batch success
        result = derive_create_batch(
            code_id=CodeId(value="1"),
            pattern="test pattern",
            segment_ids=(SegmentId(value="1"), SegmentId(value="2")),
            owner="user1",
            state=CodingState(existing_codes=existing_codes),
        )
        assert isinstance(result, BatchCreated)
        assert result.code_id == CodeId(value="1")
        assert len(result.segment_ids) == 2

        # Create batch code not found
        result = derive_create_batch(
            code_id=CodeId(value="999"),
            pattern="test pattern",
            segment_ids=(SegmentId(value="1"),),
            owner=None,
            state=CodingState(existing_codes=()),
        )
        assert isinstance(result, BatchNotCreated)
        assert result.reason == "CODE_NOT_FOUND"

        # Undo batch success
        existing_batches = (
            AutoCodeBatch(
                id=BatchId(value="batch_123"),
                code_id=CodeId(value="1"),
                pattern="test",
                segment_ids=(SegmentId(value="1"), SegmentId(value="2")),
            ),
        )
        result = derive_undo_batch(
            batch_id=BatchId(value="batch_123"),
            state=CodingState(existing_batches=existing_batches),
        )
        assert isinstance(result, BatchUndone)
        assert result.segments_removed == 2

        # Undo batch not found
        result = derive_undo_batch(
            batch_id=BatchId(value="batch_nonexistent"),
            state=CodingState(existing_batches=()),
        )
        assert isinstance(result, BatchNotUndone)
        assert result.reason == "NOT_FOUND"
