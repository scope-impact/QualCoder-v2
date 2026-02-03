"""
Coding Context: Deriver Tests

Tests for pure functions that compose invariants and derive domain events.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ============================================================
# Code Deriver Tests
# ============================================================


class TestDeriveCreateCode:
    """Tests for derive_create_code deriver."""

    def test_creates_code_with_valid_inputs(self):
        """Should create CodeCreated event with valid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_create_code
        from src.contexts.coding.core.entities import Color
        from src.contexts.coding.core.events import CodeCreated

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

    def test_fails_with_empty_name(self):
        """Should fail with CodeNotCreated for empty name."""
        from src.contexts.coding.core.derivers import CodingState, derive_create_code
        from src.contexts.coding.core.entities import Color
        from src.contexts.coding.core.failure_events import CodeNotCreated

        state = CodingState(existing_codes=())

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

    def test_fails_with_whitespace_name(self):
        """Should fail with CodeNotCreated for whitespace-only name."""
        from src.contexts.coding.core.derivers import CodingState, derive_create_code
        from src.contexts.coding.core.entities import Color
        from src.contexts.coding.core.failure_events import CodeNotCreated

        state = CodingState(existing_codes=())

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

    def test_fails_with_duplicate_name(self):
        """Should fail with CodeNotCreated for duplicate name."""
        from src.contexts.coding.core.derivers import CodingState, derive_create_code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodeNotCreated
        from src.shared import CodeId

        existing = (Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),)
        state = CodingState(existing_codes=existing)

        result = derive_create_code(
            name="Theme",
            color=Color(0, 255, 0),
            memo=None,
            category_id=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, CodeNotCreated)
        assert result.reason == "DUPLICATE_NAME"
        assert result.name == "Theme"

    def test_fails_with_invalid_category(self):
        """Should fail when category doesn't exist."""
        from src.contexts.coding.core.derivers import CodingState, derive_create_code
        from src.contexts.coding.core.entities import Color
        from src.contexts.coding.core.failure_events import CodeNotCreated
        from src.shared import CategoryId

        state = CodingState(existing_codes=(), existing_categories=())

        result = derive_create_code(
            name="Theme",
            color=Color(255, 0, 0),
            memo=None,
            category_id=CategoryId(value=999),
            owner=None,
            state=state,
        )

        assert isinstance(result, CodeNotCreated)
        assert result.reason == "CATEGORY_NOT_FOUND"


class TestDeriveRenameCode:
    """Tests for derive_rename_code deriver."""

    def test_renames_code_with_valid_inputs(self):
        """Should create CodeRenamed event with valid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_rename_code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodeRenamed
        from src.shared import CodeId

        existing = (Code(id=CodeId(value=1), name="Old Name", color=Color(255, 0, 0)),)
        state = CodingState(existing_codes=existing)

        result = derive_rename_code(
            code_id=CodeId(value=1),
            new_name="New Name",
            state=state,
        )

        assert isinstance(result, CodeRenamed)
        assert result.code_id == CodeId(value=1)
        assert result.old_name == "Old Name"
        assert result.new_name == "New Name"

    def test_fails_when_code_not_found(self):
        """Should fail when code doesn't exist."""
        from src.contexts.coding.core.derivers import CodingState, derive_rename_code
        from src.contexts.coding.core.failure_events import CodeNotRenamed
        from src.shared import CodeId

        state = CodingState(existing_codes=())

        result = derive_rename_code(
            code_id=CodeId(value=999),
            new_name="New Name",
            state=state,
        )

        assert isinstance(result, CodeNotRenamed)
        assert result.reason == "NOT_FOUND"

    def test_fails_with_empty_name(self):
        """Should fail with empty new name."""
        from src.contexts.coding.core.derivers import CodingState, derive_rename_code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodeNotRenamed
        from src.shared import CodeId

        existing = (Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),)
        state = CodingState(existing_codes=existing)

        result = derive_rename_code(
            code_id=CodeId(value=1),
            new_name="",
            state=state,
        )

        assert isinstance(result, CodeNotRenamed)
        assert result.reason == "EMPTY_NAME"

    def test_fails_with_duplicate_name(self):
        """Should fail when new name conflicts with existing code."""
        from src.contexts.coding.core.derivers import CodingState, derive_rename_code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodeNotRenamed
        from src.shared import CodeId

        existing = (
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
            Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0)),
        )
        state = CodingState(existing_codes=existing)

        result = derive_rename_code(
            code_id=CodeId(value=1),
            new_name="Pattern",
            state=state,
        )

        assert isinstance(result, CodeNotRenamed)
        assert result.reason == "DUPLICATE_NAME"


class TestDeriveChangeCodeColor:
    """Tests for derive_change_code_color deriver."""

    def test_changes_color_with_valid_inputs(self):
        """Should create CodeColorChanged event with valid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_change_code_color,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodeColorChanged
        from src.shared import CodeId

        existing = (Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),)
        state = CodingState(existing_codes=existing)

        result = derive_change_code_color(
            code_id=CodeId(value=1),
            new_color=Color(0, 255, 0),
            state=state,
        )

        assert isinstance(result, CodeColorChanged)
        assert result.old_color == Color(255, 0, 0)
        assert result.new_color == Color(0, 255, 0)

    def test_fails_when_code_not_found(self):
        """Should fail when code doesn't exist."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_change_code_color,
        )
        from src.contexts.coding.core.entities import Color
        from src.contexts.coding.core.failure_events import CodeNotUpdated
        from src.shared import CodeId

        state = CodingState(existing_codes=())

        result = derive_change_code_color(
            code_id=CodeId(value=999),
            new_color=Color(0, 255, 0),
            state=state,
        )

        assert isinstance(result, CodeNotUpdated)
        assert result.reason == "NOT_FOUND"


class TestDeriveUpdateCodeMemo:
    """Tests for derive_update_code_memo deriver."""

    def test_updates_memo_with_valid_inputs(self):
        """Should create CodeMemoUpdated event with valid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_update_code_memo,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodeMemoUpdated
        from src.shared import CodeId

        existing = (
            Code(
                id=CodeId(value=1),
                name="Theme",
                color=Color(255, 0, 0),
                memo="Old memo",
            ),
        )
        state = CodingState(existing_codes=existing)

        result = derive_update_code_memo(
            code_id=CodeId(value=1),
            new_memo="New memo",
            state=state,
        )

        assert isinstance(result, CodeMemoUpdated)
        assert result.old_memo == "Old memo"
        assert result.new_memo == "New memo"

    def test_fails_when_code_not_found(self):
        """Should fail when code doesn't exist."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_update_code_memo,
        )
        from src.contexts.coding.core.failure_events import CodeNotUpdated
        from src.shared import CodeId

        state = CodingState(existing_codes=())

        result = derive_update_code_memo(
            code_id=CodeId(value=999),
            new_memo="New memo",
            state=state,
        )

        assert isinstance(result, CodeNotUpdated)
        assert result.reason == "NOT_FOUND"


class TestDeriveDeleteCode:
    """Tests for derive_delete_code deriver."""

    def test_deletes_code_without_segments(self):
        """Should create CodeDeleted event for code without segments."""
        from src.contexts.coding.core.derivers import CodingState, derive_delete_code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodeDeleted
        from src.shared import CodeId

        existing = (Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),)
        state = CodingState(existing_codes=existing, existing_segments=())

        result = derive_delete_code(
            code_id=CodeId(value=1),
            delete_segments=False,
            state=state,
        )

        assert isinstance(result, CodeDeleted)
        assert result.code_id == CodeId(value=1)
        assert result.name == "Theme"

    def test_fails_when_code_not_found(self):
        """Should fail when code doesn't exist."""
        from src.contexts.coding.core.derivers import CodingState, derive_delete_code
        from src.contexts.coding.core.failure_events import CodeNotDeleted
        from src.shared import CodeId

        state = CodingState(existing_codes=())

        result = derive_delete_code(
            code_id=CodeId(value=999),
            delete_segments=False,
            state=state,
        )

        assert isinstance(result, CodeNotDeleted)
        assert result.reason == "NOT_FOUND"

    def test_fails_with_segments_when_not_forced(self):
        """Should fail when code has segments and delete_segments=False."""
        from src.contexts.coding.core.derivers import CodingState, derive_delete_code
        from src.contexts.coding.core.entities import (
            Code,
            Color,
            TextPosition,
            TextSegment,
        )
        from src.contexts.coding.core.failure_events import CodeNotDeleted
        from src.shared import CodeId, SegmentId, SourceId

        existing_codes = (
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
        )
        existing_segments = (
            TextSegment(
                id=SegmentId(value=1),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=0, end=10),
                selected_text="test",
            ),
        )
        state = CodingState(
            existing_codes=existing_codes, existing_segments=existing_segments
        )

        result = derive_delete_code(
            code_id=CodeId(value=1),
            delete_segments=False,
            state=state,
        )

        assert isinstance(result, CodeNotDeleted)
        assert result.reason == "HAS_REFERENCES"

    def test_deletes_code_with_segments_when_forced(self):
        """Should delete code with segments when delete_segments=True."""
        from src.contexts.coding.core.derivers import CodingState, derive_delete_code
        from src.contexts.coding.core.entities import (
            Code,
            Color,
            TextPosition,
            TextSegment,
        )
        from src.contexts.coding.core.events import CodeDeleted
        from src.shared import CodeId, SegmentId, SourceId

        existing_codes = (
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
        )
        existing_segments = (
            TextSegment(
                id=SegmentId(value=1),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=0, end=10),
                selected_text="test",
            ),
        )
        state = CodingState(
            existing_codes=existing_codes, existing_segments=existing_segments
        )

        result = derive_delete_code(
            code_id=CodeId(value=1),
            delete_segments=True,
            state=state,
        )

        assert isinstance(result, CodeDeleted)
        assert result.segments_removed == 1


class TestDeriveMergeCodes:
    """Tests for derive_merge_codes deriver."""

    def test_merges_codes_with_valid_inputs(self):
        """Should create CodesMerged event with valid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_merge_codes
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodesMerged
        from src.shared import CodeId

        existing = (
            Code(id=CodeId(value=1), name="Source", color=Color(255, 0, 0)),
            Code(id=CodeId(value=2), name="Target", color=Color(0, 255, 0)),
        )
        state = CodingState(existing_codes=existing)

        result = derive_merge_codes(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            state=state,
        )

        assert isinstance(result, CodesMerged)
        assert result.source_code_id == CodeId(value=1)
        assert result.target_code_id == CodeId(value=2)

    def test_fails_when_merging_with_self(self):
        """Should fail when merging code with itself."""
        from src.contexts.coding.core.derivers import CodingState, derive_merge_codes
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodesNotMerged
        from src.shared import CodeId

        existing = (Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),)
        state = CodingState(existing_codes=existing)

        result = derive_merge_codes(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=1),
            state=state,
        )

        assert isinstance(result, CodesNotMerged)
        assert result.reason == "SAME_CODE"

    def test_fails_when_source_not_found(self):
        """Should fail when source code doesn't exist."""
        from src.contexts.coding.core.derivers import CodingState, derive_merge_codes
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodesNotMerged
        from src.shared import CodeId

        existing = (Code(id=CodeId(value=2), name="Target", color=Color(0, 255, 0)),)
        state = CodingState(existing_codes=existing)

        result = derive_merge_codes(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            state=state,
        )

        assert isinstance(result, CodesNotMerged)
        assert result.reason == "SOURCE_NOT_FOUND"

    def test_fails_when_target_not_found(self):
        """Should fail when target code doesn't exist."""
        from src.contexts.coding.core.derivers import CodingState, derive_merge_codes
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodesNotMerged
        from src.shared import CodeId

        existing = (Code(id=CodeId(value=1), name="Source", color=Color(255, 0, 0)),)
        state = CodingState(existing_codes=existing)

        result = derive_merge_codes(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            state=state,
        )

        assert isinstance(result, CodesNotMerged)
        assert result.reason == "TARGET_NOT_FOUND"


class TestDeriveMoveCodeToCategory:
    """Tests for derive_move_code_to_category deriver."""

    def test_moves_code_to_category(self):
        """Should create CodeMovedToCategory event with valid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_move_code_to_category,
        )
        from src.contexts.coding.core.entities import Category, Code, Color
        from src.contexts.coding.core.events import CodeMovedToCategory
        from src.shared import CategoryId, CodeId

        existing_codes = (
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
        )
        existing_categories = (Category(id=CategoryId(value=1), name="Themes"),)
        state = CodingState(
            existing_codes=existing_codes, existing_categories=existing_categories
        )

        result = derive_move_code_to_category(
            code_id=CodeId(value=1),
            new_category_id=CategoryId(value=1),
            state=state,
        )

        assert isinstance(result, CodeMovedToCategory)
        assert result.code_id == CodeId(value=1)
        assert result.new_category_id == CategoryId(value=1)

    def test_moves_code_to_root(self):
        """Should allow moving code to root (no category)."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_move_code_to_category,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodeMovedToCategory
        from src.shared import CategoryId, CodeId

        existing_codes = (
            Code(
                id=CodeId(value=1),
                name="Theme",
                color=Color(255, 0, 0),
                category_id=CategoryId(value=1),
            ),
        )
        state = CodingState(existing_codes=existing_codes)

        result = derive_move_code_to_category(
            code_id=CodeId(value=1),
            new_category_id=None,
            state=state,
        )

        assert isinstance(result, CodeMovedToCategory)
        assert result.new_category_id is None

    def test_fails_when_code_not_found(self):
        """Should fail when code doesn't exist."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_move_code_to_category,
        )
        from src.contexts.coding.core.failure_events import CodeNotMoved
        from src.shared import CategoryId, CodeId

        state = CodingState(existing_codes=())

        result = derive_move_code_to_category(
            code_id=CodeId(value=999),
            new_category_id=CategoryId(value=1),
            state=state,
        )

        assert isinstance(result, CodeNotMoved)
        assert result.reason == "CODE_NOT_FOUND"

    def test_fails_when_category_not_found(self):
        """Should fail when target category doesn't exist."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_move_code_to_category,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodeNotMoved
        from src.shared import CategoryId, CodeId

        existing_codes = (
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
        )
        state = CodingState(existing_codes=existing_codes, existing_categories=())

        result = derive_move_code_to_category(
            code_id=CodeId(value=1),
            new_category_id=CategoryId(value=999),
            state=state,
        )

        assert isinstance(result, CodeNotMoved)
        assert result.reason == "CATEGORY_NOT_FOUND"


# ============================================================
# Category Deriver Tests
# ============================================================


class TestDeriveCreateCategory:
    """Tests for derive_create_category deriver."""

    def test_creates_category_with_valid_inputs(self):
        """Should create CategoryCreated event with valid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_create_category,
        )
        from src.contexts.coding.core.events import CategoryCreated

        state = CodingState(existing_categories=())

        result = derive_create_category(
            name="Themes",
            parent_id=None,
            memo="Main themes category",
            owner="user1",
            state=state,
        )

        assert isinstance(result, CategoryCreated)
        assert result.name == "Themes"
        assert result.memo == "Main themes category"

    def test_fails_with_empty_name(self):
        """Should fail with empty name."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_create_category,
        )
        from src.contexts.coding.core.failure_events import CategoryNotCreated

        state = CodingState(existing_categories=())

        result = derive_create_category(
            name="",
            parent_id=None,
            memo=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, CategoryNotCreated)
        assert result.reason == "EMPTY_NAME"

    def test_fails_with_duplicate_name(self):
        """Should fail with duplicate name."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_create_category,
        )
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.failure_events import CategoryNotCreated
        from src.shared import CategoryId

        existing = (Category(id=CategoryId(value=1), name="Themes"),)
        state = CodingState(existing_categories=existing)

        result = derive_create_category(
            name="Themes",
            parent_id=None,
            memo=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, CategoryNotCreated)
        assert result.reason == "DUPLICATE_NAME"

    def test_fails_with_invalid_parent(self):
        """Should fail when parent doesn't exist."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_create_category,
        )
        from src.contexts.coding.core.failure_events import CategoryNotCreated
        from src.shared import CategoryId

        state = CodingState(existing_categories=())

        result = derive_create_category(
            name="Child",
            parent_id=CategoryId(value=999),
            memo=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, CategoryNotCreated)
        assert result.reason == "PARENT_NOT_FOUND"


class TestDeriveRenameCategory:
    """Tests for derive_rename_category deriver."""

    def test_renames_category_with_valid_inputs(self):
        """Should create CategoryRenamed event with valid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_rename_category,
        )
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.events import CategoryRenamed
        from src.shared import CategoryId

        existing = (Category(id=CategoryId(value=1), name="Old Name"),)
        state = CodingState(existing_categories=existing)

        result = derive_rename_category(
            category_id=CategoryId(value=1),
            new_name="New Name",
            state=state,
        )

        assert isinstance(result, CategoryRenamed)
        assert result.old_name == "Old Name"
        assert result.new_name == "New Name"

    def test_fails_when_category_not_found(self):
        """Should fail when category doesn't exist."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_rename_category,
        )
        from src.contexts.coding.core.failure_events import CategoryNotRenamed
        from src.shared import CategoryId

        state = CodingState(existing_categories=())

        result = derive_rename_category(
            category_id=CategoryId(value=999),
            new_name="New Name",
            state=state,
        )

        assert isinstance(result, CategoryNotRenamed)
        assert result.reason == "NOT_FOUND"


class TestDeriveDeleteCategory:
    """Tests for derive_delete_category deriver."""

    def test_deletes_category_with_valid_inputs(self):
        """Should create CategoryDeleted event with valid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_delete_category,
        )
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.events import CategoryDeleted
        from src.shared import CategoryId

        existing = (Category(id=CategoryId(value=1), name="Themes"),)
        state = CodingState(existing_categories=existing)

        result = derive_delete_category(
            category_id=CategoryId(value=1),
            orphan_strategy="move_to_parent",
            state=state,
        )

        assert isinstance(result, CategoryDeleted)
        assert result.name == "Themes"

    def test_fails_when_category_not_found(self):
        """Should fail when category doesn't exist."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_delete_category,
        )
        from src.contexts.coding.core.failure_events import CategoryNotDeleted
        from src.shared import CategoryId

        state = CodingState(existing_categories=())

        result = derive_delete_category(
            category_id=CategoryId(value=999),
            orphan_strategy="move_to_parent",
            state=state,
        )

        assert isinstance(result, CategoryNotDeleted)
        assert result.reason == "NOT_FOUND"


# ============================================================
# Segment Deriver Tests
# ============================================================


class TestDeriveApplyCodeToText:
    """Tests for derive_apply_code_to_text deriver."""

    def test_applies_code_to_text(self):
        """Should create SegmentCoded event with valid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_apply_code_to_text,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import SegmentCoded
        from src.shared import CodeId, SourceId

        existing_codes = (
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
        )
        state = CodingState(
            existing_codes=existing_codes,
            source_length=100,
            source_exists=True,
        )

        result = derive_apply_code_to_text(
            code_id=CodeId(value=1),
            source_id=SourceId(value=1),
            start=10,
            end=20,
            selected_text="sample text",
            memo="A note about this segment",
            importance=1,
            owner="user1",
            state=state,
        )

        assert isinstance(result, SegmentCoded)
        assert result.code_id == CodeId(value=1)
        assert result.selected_text == "sample text"

    def test_fails_when_code_not_found(self):
        """Should fail when code doesn't exist."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_apply_code_to_text,
        )
        from src.contexts.coding.core.failure_events import SegmentNotCoded
        from src.shared import CodeId, SourceId

        state = CodingState(existing_codes=(), source_length=100, source_exists=True)

        result = derive_apply_code_to_text(
            code_id=CodeId(value=999),
            source_id=SourceId(value=1),
            start=10,
            end=20,
            selected_text="sample text",
            memo=None,
            importance=0,
            owner=None,
            state=state,
        )

        assert isinstance(result, SegmentNotCoded)
        assert result.reason == "CODE_NOT_FOUND"

    def test_fails_when_source_not_found(self):
        """Should fail when source doesn't exist."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_apply_code_to_text,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import SegmentNotCoded
        from src.shared import CodeId, SourceId

        existing_codes = (
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
        )
        state = CodingState(existing_codes=existing_codes, source_exists=False)

        result = derive_apply_code_to_text(
            code_id=CodeId(value=1),
            source_id=SourceId(value=999),
            start=10,
            end=20,
            selected_text="sample text",
            memo=None,
            importance=0,
            owner=None,
            state=state,
        )

        assert isinstance(result, SegmentNotCoded)
        assert result.reason == "SOURCE_NOT_FOUND"

    def test_fails_with_invalid_position(self):
        """Should fail with invalid position."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_apply_code_to_text,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import SegmentNotCoded
        from src.shared import CodeId, SourceId

        existing_codes = (
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
        )
        state = CodingState(
            existing_codes=existing_codes,
            source_length=50,
            source_exists=True,
        )

        result = derive_apply_code_to_text(
            code_id=CodeId(value=1),
            source_id=SourceId(value=1),
            start=40,
            end=60,  # Beyond source length
            selected_text="sample text",
            memo=None,
            importance=0,
            owner=None,
            state=state,
        )

        assert isinstance(result, SegmentNotCoded)
        assert result.reason == "INVALID_POSITION"


class TestDeriveRemoveSegment:
    """Tests for derive_remove_segment deriver."""

    def test_removes_segment_with_valid_inputs(self):
        """Should create SegmentUncoded event with valid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_remove_segment
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.events import SegmentUncoded
        from src.shared import CodeId, SegmentId, SourceId

        existing_segments = (
            TextSegment(
                id=SegmentId(value=1),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=0, end=10),
                selected_text="test",
            ),
        )
        state = CodingState(existing_segments=existing_segments)

        result = derive_remove_segment(
            segment_id=SegmentId(value=1),
            state=state,
        )

        assert isinstance(result, SegmentUncoded)
        assert result.segment_id == SegmentId(value=1)

    def test_fails_when_segment_not_found(self):
        """Should fail when segment doesn't exist."""
        from src.contexts.coding.core.derivers import CodingState, derive_remove_segment
        from src.contexts.coding.core.failure_events import SegmentNotRemoved
        from src.shared import SegmentId

        state = CodingState(existing_segments=())

        result = derive_remove_segment(
            segment_id=SegmentId(value=999),
            state=state,
        )

        assert isinstance(result, SegmentNotRemoved)
        assert result.reason == "NOT_FOUND"


class TestDeriveUpdateSegmentMemo:
    """Tests for derive_update_segment_memo deriver."""

    def test_updates_memo_with_valid_inputs(self):
        """Should create SegmentMemoUpdated event with valid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_update_segment_memo,
        )
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.events import SegmentMemoUpdated
        from src.shared import CodeId, SegmentId, SourceId

        existing_segments = (
            TextSegment(
                id=SegmentId(value=1),
                source_id=SourceId(value=1),
                code_id=CodeId(value=1),
                position=TextPosition(start=0, end=10),
                selected_text="test",
                memo="Old memo",
            ),
        )
        state = CodingState(existing_segments=existing_segments)

        result = derive_update_segment_memo(
            segment_id=SegmentId(value=1),
            new_memo="New memo",
            state=state,
        )

        assert isinstance(result, SegmentMemoUpdated)
        assert result.old_memo == "Old memo"
        assert result.new_memo == "New memo"

    def test_fails_when_segment_not_found(self):
        """Should fail when segment doesn't exist."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_update_segment_memo,
        )
        from src.contexts.coding.core.failure_events import SegmentNotUpdated
        from src.shared import SegmentId

        state = CodingState(existing_segments=())

        result = derive_update_segment_memo(
            segment_id=SegmentId(value=999),
            new_memo="New memo",
            state=state,
        )

        assert isinstance(result, SegmentNotUpdated)
        assert result.reason == "NOT_FOUND"


# ============================================================
# Batch Deriver Tests
# ============================================================


class TestDeriveCreateBatch:
    """Tests for derive_create_batch deriver."""

    def test_creates_batch_with_valid_inputs(self):
        """Should create BatchCreated event with valid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_create_batch
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import BatchCreated
        from src.shared import CodeId, SegmentId

        existing_codes = (
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
        )
        state = CodingState(existing_codes=existing_codes)

        result = derive_create_batch(
            code_id=CodeId(value=1),
            pattern="test pattern",
            segment_ids=(SegmentId(value=1), SegmentId(value=2)),
            owner="user1",
            state=state,
        )

        assert isinstance(result, BatchCreated)
        assert result.code_id == CodeId(value=1)
        assert result.pattern == "test pattern"
        assert len(result.segment_ids) == 2

    def test_fails_when_code_not_found(self):
        """Should fail when code doesn't exist."""
        from src.contexts.coding.core.derivers import CodingState, derive_create_batch
        from src.contexts.coding.core.failure_events import BatchNotCreated
        from src.shared import CodeId, SegmentId

        state = CodingState(existing_codes=())

        result = derive_create_batch(
            code_id=CodeId(value=999),
            pattern="test pattern",
            segment_ids=(SegmentId(value=1),),
            owner=None,
            state=state,
        )

        assert isinstance(result, BatchNotCreated)
        assert result.reason == "CODE_NOT_FOUND"


class TestDeriveUndoBatch:
    """Tests for derive_undo_batch deriver."""

    def test_undoes_batch_with_valid_inputs(self):
        """Should create BatchUndone event with valid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_undo_batch
        from src.contexts.coding.core.entities import AutoCodeBatch, BatchId
        from src.contexts.coding.core.events import BatchUndone
        from src.shared import CodeId, SegmentId

        existing_batches = (
            AutoCodeBatch(
                id=BatchId(value="batch_123"),
                code_id=CodeId(value=1),
                pattern="test",
                segment_ids=(SegmentId(value=1), SegmentId(value=2)),
            ),
        )
        state = CodingState(existing_batches=existing_batches)

        result = derive_undo_batch(
            batch_id=BatchId(value="batch_123"),
            state=state,
        )

        assert isinstance(result, BatchUndone)
        assert result.segments_removed == 2

    def test_fails_when_batch_not_found(self):
        """Should fail when batch doesn't exist."""
        from src.contexts.coding.core.derivers import CodingState, derive_undo_batch
        from src.contexts.coding.core.entities import BatchId
        from src.contexts.coding.core.failure_events import BatchNotUndone

        state = CodingState(existing_batches=())

        result = derive_undo_batch(
            batch_id=BatchId(value="batch_nonexistent"),
            state=state,
        )

        assert isinstance(result, BatchNotUndone)
        assert result.reason == "NOT_FOUND"
