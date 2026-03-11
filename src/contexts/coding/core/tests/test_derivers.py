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

    @allure.title("Creates code with valid name, color, and memo")
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

    @pytest.mark.parametrize(
        "name, existing_codes, category_id, existing_categories, expected_reason",
        [
            pytest.param("", (), None, (), "EMPTY_NAME", id="empty_name"),
            pytest.param("   ", (), None, (), "EMPTY_NAME", id="whitespace_name"),
            pytest.param("Theme", "USE_EXISTING", None, (), "DUPLICATE_NAME", id="duplicate_name"),
            pytest.param("Theme", (), "USE_CATEGORY", (), "CATEGORY_NOT_FOUND", id="invalid_category"),
        ],
    )
    @allure.title("Rejects invalid inputs: empty name, duplicate, missing category")
    def test_fails_with_invalid_inputs(
        self, name, existing_codes, category_id, existing_categories, expected_reason
    ):
        """Should fail with CodeNotCreated for various invalid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_create_code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodeNotCreated
        from src.shared import CategoryId, CodeId

        if existing_codes == "USE_EXISTING":
            existing_codes = (Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),)
        if category_id == "USE_CATEGORY":
            category_id = CategoryId(value="999")

        state = CodingState(
            existing_codes=existing_codes, existing_categories=existing_categories
        )

        result = derive_create_code(
            name=name,
            color=Color(255, 0, 0),
            memo=None,
            category_id=category_id,
            owner=None,
            state=state,
        )

        assert isinstance(result, CodeNotCreated)
        assert result.reason == expected_reason
        if expected_reason == "DUPLICATE_NAME":
            assert result.name == "Theme"


@allure.story("QC-028.03 Rename and Recolor Codes")
class TestDeriveRenameCode:
    """Tests for derive_rename_code deriver."""

    @allure.title("Renames code producing CodeRenamed event")
    def test_renames_code_with_valid_inputs(self):
        """Should create CodeRenamed event with valid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_rename_code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodeRenamed
        from src.shared import CodeId

        existing = (
            Code(id=CodeId(value="1"), name="Old Name", color=Color(255, 0, 0)),
        )
        state = CodingState(existing_codes=existing)

        result = derive_rename_code(
            code_id=CodeId(value="1"),
            new_name="New Name",
            state=state,
        )

        assert isinstance(result, CodeRenamed)
        assert result.code_id == CodeId(value="1")
        assert result.old_name == "Old Name"
        assert result.new_name == "New Name"

    @pytest.mark.parametrize(
        "code_id_val, new_name, existing_codes, expected_reason",
        [
            pytest.param("999", "New Name", (), "NOT_FOUND", id="code_not_found"),
            pytest.param("1", "", "USE_SINGLE", "EMPTY_NAME", id="empty_name"),
            pytest.param("1", "Pattern", "USE_PAIR", "DUPLICATE_NAME", id="duplicate_name"),
        ],
    )
    @allure.title("Rejects invalid rename: not found, empty name, duplicate")
    def test_fails_with_invalid_inputs(
        self, code_id_val, new_name, existing_codes, expected_reason
    ):
        """Should fail with CodeNotRenamed for various invalid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_rename_code
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodeNotRenamed
        from src.shared import CodeId

        if existing_codes == "USE_SINGLE":
            existing_codes = (Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),)
        elif existing_codes == "USE_PAIR":
            existing_codes = (
                Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
                Code(id=CodeId(value="2"), name="Pattern", color=Color(0, 255, 0)),
            )

        state = CodingState(existing_codes=existing_codes)

        result = derive_rename_code(
            code_id=CodeId(value=code_id_val),
            new_name=new_name,
            state=state,
        )

        assert isinstance(result, CodeNotRenamed)
        assert result.reason == expected_reason


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

        # Success case
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

        # Failure case: not found
        state = CodingState(existing_codes=())

        result = derive_change_code_color(
            code_id=CodeId(value="999"),
            new_color=Color(0, 255, 0),
            state=state,
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

        # Success case
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
            code_id=CodeId(value="1"),
            new_memo="New memo",
            state=state,
        )

        assert isinstance(result, CodeMemoUpdated)
        assert result.old_memo == "Old memo"
        assert result.new_memo == "New memo"

        # Failure case: not found
        state = CodingState(existing_codes=())

        result = derive_update_code_memo(
            code_id=CodeId(value="999"),
            new_memo="New memo",
            state=state,
        )

        assert isinstance(result, CodeNotUpdated)
        assert result.reason == "NOT_FOUND"


@allure.story("QC-028.01 Create New Code")
class TestDeriveDeleteCode:
    """Tests for derive_delete_code deriver."""

    @allure.title("Deletes code with and without associated segments")
    def test_deletes_code_with_and_without_segments(self):
        """Should delete code without segments and with segments when forced."""
        from src.contexts.coding.core.derivers import CodingState, derive_delete_code
        from src.contexts.coding.core.entities import (
            Code,
            Color,
            TextPosition,
            TextSegment,
        )
        from src.contexts.coding.core.events import CodeDeleted
        from src.shared import CodeId, SegmentId, SourceId

        # Without segments
        existing = (Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),)
        state = CodingState(existing_codes=existing, existing_segments=())

        result = derive_delete_code(
            code_id=CodeId(value="1"),
            delete_segments=False,
            state=state,
        )

        assert isinstance(result, CodeDeleted)
        assert result.code_id == CodeId(value="1")
        assert result.name == "Theme"

        # With segments, forced
        existing_segments = (
            TextSegment(
                id=SegmentId(value="1"),
                source_id=SourceId(value="1"),
                code_id=CodeId(value="1"),
                position=TextPosition(start=0, end=10),
                selected_text="test",
            ),
        )
        state = CodingState(
            existing_codes=existing, existing_segments=existing_segments
        )

        result = derive_delete_code(
            code_id=CodeId(value="1"),
            delete_segments=True,
            state=state,
        )

        assert isinstance(result, CodeDeleted)
        assert result.segments_removed == 1

    @pytest.mark.parametrize(
        "code_id_val, has_segments, expected_reason",
        [
            pytest.param("999", False, "NOT_FOUND", id="not_found"),
            pytest.param("1", True, "HAS_REFERENCES", id="has_references"),
        ],
    )
    @allure.title("Rejects delete: not found or has references without force")
    def test_fails_with_invalid_inputs(self, code_id_val, has_segments, expected_reason):
        """Should fail with CodeNotDeleted for various invalid inputs."""
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
            (Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),)
            if code_id_val == "1" or has_segments
            else ()
        )
        existing_segments = ()
        if has_segments:
            existing_segments = (
                TextSegment(
                    id=SegmentId(value="1"),
                    source_id=SourceId(value="1"),
                    code_id=CodeId(value="1"),
                    position=TextPosition(start=0, end=10),
                    selected_text="test",
                ),
            )

        state = CodingState(
            existing_codes=existing_codes, existing_segments=existing_segments
        )

        result = derive_delete_code(
            code_id=CodeId(value=code_id_val),
            delete_segments=False,
            state=state,
        )

        assert isinstance(result, CodeNotDeleted)
        assert result.reason == expected_reason


@allure.story("QC-028.01 Create New Code")
class TestDeriveMergeCodes:
    """Tests for derive_merge_codes deriver."""

    @allure.title("Merges source code into target code")
    def test_merges_codes_with_valid_inputs(self):
        """Should create CodesMerged event with valid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_merge_codes
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import CodesMerged
        from src.shared import CodeId

        existing = (
            Code(id=CodeId(value="1"), name="Source", color=Color(255, 0, 0)),
            Code(id=CodeId(value="2"), name="Target", color=Color(0, 255, 0)),
        )
        state = CodingState(existing_codes=existing)

        result = derive_merge_codes(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            state=state,
        )

        assert isinstance(result, CodesMerged)
        assert result.source_code_id == CodeId(value="1")
        assert result.target_code_id == CodeId(value="2")

    @pytest.mark.parametrize(
        "source_id, target_id, existing_ids_names, expected_reason",
        [
            pytest.param("1", "1", [("1", "Theme")], "SAME_CODE", id="self_merge"),
            pytest.param("1", "2", [("2", "Target")], "SOURCE_NOT_FOUND", id="source_not_found"),
            pytest.param("1", "2", [("1", "Source")], "TARGET_NOT_FOUND", id="target_not_found"),
        ],
    )
    @allure.title("Rejects merge: self-merge, source or target not found")
    def test_fails_with_invalid_inputs(
        self, source_id, target_id, existing_ids_names, expected_reason
    ):
        """Should fail with CodesNotMerged for various invalid inputs."""
        from src.contexts.coding.core.derivers import CodingState, derive_merge_codes
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodesNotMerged
        from src.shared import CodeId

        existing = tuple(
            Code(id=CodeId(value=cid), name=name, color=Color(255, 0, 0))
            for cid, name in existing_ids_names
        )
        state = CodingState(existing_codes=existing)

        result = derive_merge_codes(
            source_code_id=CodeId(value=source_id),
            target_code_id=CodeId(value=target_id),
            state=state,
        )

        assert isinstance(result, CodesNotMerged)
        assert result.reason == expected_reason


@allure.story("QC-028.02 Organize Codes into Categories")
class TestDeriveMoveCodeToCategory:
    """Tests for derive_move_code_to_category deriver."""

    @allure.title("Moves code to category and back to root")
    def test_moves_code_to_category_and_to_root(self):
        """Should move code to a category and to root (no category)."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_move_code_to_category,
        )
        from src.contexts.coding.core.entities import Category, Code, Color
        from src.contexts.coding.core.events import CodeMovedToCategory
        from src.shared import CategoryId, CodeId

        # Move to category
        existing_codes = (
            Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
        )
        existing_categories = (Category(id=CategoryId(value="1"), name="Themes"),)
        state = CodingState(
            existing_codes=existing_codes, existing_categories=existing_categories
        )

        result = derive_move_code_to_category(
            code_id=CodeId(value="1"),
            new_category_id=CategoryId(value="1"),
            state=state,
        )

        assert isinstance(result, CodeMovedToCategory)
        assert result.code_id == CodeId(value="1")
        assert result.new_category_id == CategoryId(value="1")

        # Move to root
        existing_codes = (
            Code(
                id=CodeId(value="1"),
                name="Theme",
                color=Color(255, 0, 0),
                category_id=CategoryId(value="1"),
            ),
        )
        state = CodingState(existing_codes=existing_codes)

        result = derive_move_code_to_category(
            code_id=CodeId(value="1"),
            new_category_id=None,
            state=state,
        )

        assert isinstance(result, CodeMovedToCategory)
        assert result.new_category_id is None

    @pytest.mark.parametrize(
        "code_id_val, has_code, category_id_val, has_category, expected_reason",
        [
            pytest.param("999", False, "1", False, "CODE_NOT_FOUND", id="code_not_found"),
            pytest.param("1", True, "999", False, "CATEGORY_NOT_FOUND", id="category_not_found"),
        ],
    )
    @allure.title("Rejects move: code or category not found")
    def test_fails_with_invalid_inputs(
        self, code_id_val, has_code, category_id_val, has_category, expected_reason
    ):
        """Should fail with CodeNotMoved for various invalid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_move_code_to_category,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import CodeNotMoved
        from src.shared import CategoryId, CodeId

        existing_codes = (
            (Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),)
            if has_code
            else ()
        )
        state = CodingState(existing_codes=existing_codes, existing_categories=())

        result = derive_move_code_to_category(
            code_id=CodeId(value=code_id_val),
            new_category_id=CategoryId(value=category_id_val),
            state=state,
        )

        assert isinstance(result, CodeNotMoved)
        assert result.reason == expected_reason


# ============================================================
# Category Deriver Tests
# ============================================================


@allure.story("QC-028.02 Organize Codes into Categories")
class TestDeriveCreateCategory:
    """Tests for derive_create_category deriver."""

    @allure.title("Creates category with valid name and memo")
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

    @pytest.mark.parametrize(
        "name, existing_categories, parent_id, expected_reason",
        [
            pytest.param("", (), None, "EMPTY_NAME", id="empty_name"),
            pytest.param("Themes", "USE_EXISTING", None, "DUPLICATE_NAME", id="duplicate_name"),
            pytest.param("Child", (), "USE_PARENT", "PARENT_NOT_FOUND", id="invalid_parent"),
        ],
    )
    @allure.title("Rejects invalid category: empty name, duplicate, missing parent")
    def test_fails_with_invalid_inputs(
        self, name, existing_categories, parent_id, expected_reason
    ):
        """Should fail with CategoryNotCreated for various invalid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_create_category,
        )
        from src.contexts.coding.core.entities import Category
        from src.contexts.coding.core.failure_events import CategoryNotCreated
        from src.shared import CategoryId

        if existing_categories == "USE_EXISTING":
            existing_categories = (Category(id=CategoryId(value="1"), name="Themes"),)
        if parent_id == "USE_PARENT":
            parent_id = CategoryId(value="999")

        state = CodingState(existing_categories=existing_categories)

        result = derive_create_category(
            name=name,
            parent_id=parent_id,
            memo=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, CategoryNotCreated)
        assert result.reason == expected_reason


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

        # Success case
        existing = (Category(id=CategoryId(value="1"), name="Old Name"),)
        state = CodingState(existing_categories=existing)

        result = derive_rename_category(
            category_id=CategoryId(value="1"),
            new_name="New Name",
            state=state,
        )

        assert isinstance(result, CategoryRenamed)
        assert result.old_name == "Old Name"
        assert result.new_name == "New Name"

        # Failure case: not found
        state = CodingState(existing_categories=())

        result = derive_rename_category(
            category_id=CategoryId(value="999"),
            new_name="New Name",
            state=state,
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

        # Success case
        existing = (Category(id=CategoryId(value="1"), name="Themes"),)
        state = CodingState(existing_categories=existing)

        result = derive_delete_category(
            category_id=CategoryId(value="1"),
            orphan_strategy="move_to_parent",
            state=state,
        )

        assert isinstance(result, CategoryDeleted)
        assert result.name == "Themes"

        # Failure case: not found
        state = CodingState(existing_categories=())

        result = derive_delete_category(
            category_id=CategoryId(value="999"),
            orphan_strategy="move_to_parent",
            state=state,
        )

        assert isinstance(result, CategoryNotDeleted)
        assert result.reason == "NOT_FOUND"


# ============================================================
# Segment Deriver Tests
# ============================================================


@allure.story("QC-029.01 Apply Code to Text")
class TestDeriveApplyCodeToText:
    """Tests for derive_apply_code_to_text deriver."""

    @allure.title("Applies code to text producing SegmentCoded event")
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
            Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
        )
        state = CodingState(
            existing_codes=existing_codes,
            source_length=100,
            source_exists=True,
        )

        result = derive_apply_code_to_text(
            code_id=CodeId(value="1"),
            source_id=SourceId(value="1"),
            start=10,
            end=20,
            selected_text="sample text",
            memo="A note about this segment",
            importance=1,
            owner="user1",
            state=state,
        )

        assert isinstance(result, SegmentCoded)
        assert result.code_id == CodeId(value="1")
        assert result.selected_text == "sample text"

    @pytest.mark.parametrize(
        "code_id_val, has_code, source_exists, source_length, start, end, expected_reason",
        [
            pytest.param("999", False, True, 100, 10, 20, "CODE_NOT_FOUND", id="code_not_found"),
            pytest.param("1", True, False, 0, 10, 20, "SOURCE_NOT_FOUND", id="source_not_found"),
            pytest.param("1", True, True, 50, 40, 60, "INVALID_POSITION", id="invalid_position"),
        ],
    )
    @allure.title("Rejects coding: code not found, source missing, invalid position")
    def test_fails_with_invalid_inputs(
        self, code_id_val, has_code, source_exists, source_length, start, end, expected_reason
    ):
        """Should fail with SegmentNotCoded for various invalid inputs."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_apply_code_to_text,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.failure_events import SegmentNotCoded
        from src.shared import CodeId, SourceId

        existing_codes = (
            (Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),)
            if has_code
            else ()
        )
        state = CodingState(
            existing_codes=existing_codes,
            source_length=source_length,
            source_exists=source_exists,
        )

        result = derive_apply_code_to_text(
            code_id=CodeId(value=code_id_val),
            source_id=SourceId(value="1"),
            start=start,
            end=end,
            selected_text="sample text",
            memo=None,
            importance=0,
            owner=None,
            state=state,
        )

        assert isinstance(result, SegmentNotCoded)
        assert result.reason == expected_reason


@allure.story("QC-029.01 Apply Code to Text")
class TestDeriveRemoveSegment:
    """Tests for derive_remove_segment deriver."""

    @allure.title("Removes segment and fails when not found")
    def test_removes_segment_and_fails_when_not_found(self):
        """Should remove segment with valid inputs and fail when not found."""
        from src.contexts.coding.core.derivers import CodingState, derive_remove_segment
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.events import SegmentUncoded
        from src.contexts.coding.core.failure_events import SegmentNotRemoved
        from src.shared import CodeId, SegmentId, SourceId

        # Success case
        existing_segments = (
            TextSegment(
                id=SegmentId(value="1"),
                source_id=SourceId(value="1"),
                code_id=CodeId(value="1"),
                position=TextPosition(start=0, end=10),
                selected_text="test",
            ),
        )
        state = CodingState(existing_segments=existing_segments)

        result = derive_remove_segment(
            segment_id=SegmentId(value="1"),
            state=state,
        )

        assert isinstance(result, SegmentUncoded)
        assert result.segment_id == SegmentId(value="1")

        # Failure case: not found
        state = CodingState(existing_segments=())

        result = derive_remove_segment(
            segment_id=SegmentId(value="999"),
            state=state,
        )

        assert isinstance(result, SegmentNotRemoved)
        assert result.reason == "NOT_FOUND"


@allure.story("QC-029.01 Apply Code to Text")
class TestDeriveUpdateSegmentMemo:
    """Tests for derive_update_segment_memo deriver."""

    @allure.title("Updates segment memo and fails when not found")
    def test_updates_memo_and_fails_when_not_found(self):
        """Should update memo with valid inputs and fail when not found."""
        from src.contexts.coding.core.derivers import (
            CodingState,
            derive_update_segment_memo,
        )
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.coding.core.events import SegmentMemoUpdated
        from src.contexts.coding.core.failure_events import SegmentNotUpdated
        from src.shared import CodeId, SegmentId, SourceId

        # Success case
        existing_segments = (
            TextSegment(
                id=SegmentId(value="1"),
                source_id=SourceId(value="1"),
                code_id=CodeId(value="1"),
                position=TextPosition(start=0, end=10),
                selected_text="test",
                memo="Old memo",
            ),
        )
        state = CodingState(existing_segments=existing_segments)

        result = derive_update_segment_memo(
            segment_id=SegmentId(value="1"),
            new_memo="New memo",
            state=state,
        )

        assert isinstance(result, SegmentMemoUpdated)
        assert result.old_memo == "Old memo"
        assert result.new_memo == "New memo"

        # Failure case: not found
        state = CodingState(existing_segments=())

        result = derive_update_segment_memo(
            segment_id=SegmentId(value="999"),
            new_memo="New memo",
            state=state,
        )

        assert isinstance(result, SegmentNotUpdated)
        assert result.reason == "NOT_FOUND"


# ============================================================
# Batch Deriver Tests
# ============================================================


@allure.story("QC-029.01 Apply Code to Text")
class TestDeriveCreateBatch:
    """Tests for derive_create_batch deriver."""

    @allure.title("Creates auto-code batch and fails when code not found")
    def test_creates_batch_and_fails_when_code_not_found(self):
        """Should create batch with valid inputs and fail when code not found."""
        from src.contexts.coding.core.derivers import CodingState, derive_create_batch
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.coding.core.events import BatchCreated
        from src.contexts.coding.core.failure_events import BatchNotCreated
        from src.shared import CodeId, SegmentId

        # Success case
        existing_codes = (
            Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
        )
        state = CodingState(existing_codes=existing_codes)

        result = derive_create_batch(
            code_id=CodeId(value="1"),
            pattern="test pattern",
            segment_ids=(SegmentId(value="1"), SegmentId(value="2")),
            owner="user1",
            state=state,
        )

        assert isinstance(result, BatchCreated)
        assert result.code_id == CodeId(value="1")
        assert result.pattern == "test pattern"
        assert len(result.segment_ids) == 2

        # Failure case: code not found
        state = CodingState(existing_codes=())

        result = derive_create_batch(
            code_id=CodeId(value="999"),
            pattern="test pattern",
            segment_ids=(SegmentId(value="1"),),
            owner=None,
            state=state,
        )

        assert isinstance(result, BatchNotCreated)
        assert result.reason == "CODE_NOT_FOUND"


@allure.story("QC-029.01 Apply Code to Text")
class TestDeriveUndoBatch:
    """Tests for derive_undo_batch deriver."""

    @allure.title("Undoes batch removing segments and fails when not found")
    def test_undoes_batch_and_fails_when_not_found(self):
        """Should undo batch with valid inputs and fail when not found."""
        from src.contexts.coding.core.derivers import CodingState, derive_undo_batch
        from src.contexts.coding.core.entities import AutoCodeBatch, BatchId
        from src.contexts.coding.core.events import BatchUndone
        from src.contexts.coding.core.failure_events import BatchNotUndone
        from src.shared import CodeId, SegmentId

        # Success case
        existing_batches = (
            AutoCodeBatch(
                id=BatchId(value="batch_123"),
                code_id=CodeId(value="1"),
                pattern="test",
                segment_ids=(SegmentId(value="1"), SegmentId(value="2")),
            ),
        )
        state = CodingState(existing_batches=existing_batches)

        result = derive_undo_batch(
            batch_id=BatchId(value="batch_123"),
            state=state,
        )

        assert isinstance(result, BatchUndone)
        assert result.segments_removed == 2

        # Failure case: not found
        state = CodingState(existing_batches=())

        result = derive_undo_batch(
            batch_id=BatchId(value="batch_nonexistent"),
            state=state,
        )

        assert isinstance(result, BatchNotUndone)
        assert result.reason == "NOT_FOUND"
