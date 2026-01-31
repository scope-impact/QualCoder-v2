"""Tests for CodingControllerImpl."""

from __future__ import annotations

from returns.result import Failure, Success

from src.application.protocols import (
    ApplyCodeCommand,
    ChangeCodeColorCommand,
    CreateCategoryCommand,
    CreateCodeCommand,
    DeleteCategoryCommand,
    DeleteCodeCommand,
    MergeCodesCommand,
    RemoveCodeCommand,
    RenameCodeCommand,
)
from src.domain.coding.events import (
    CategoryCreated,
    CategoryDeleted,
    CodeColorChanged,
    CodeCreated,
    CodeDeleted,
    CodeRenamed,
    CodesMerged,
    SegmentCoded,
    SegmentUncoded,
)


class TestCreateCode:
    """Tests for create_code command."""

    def test_creates_code_successfully(self, controller, event_bus):
        """Test successful code creation."""
        command = CreateCodeCommand(name="Test Code", color="#ff0000")

        result = controller.create_code(command)

        assert isinstance(result, Success)
        code = result.unwrap()
        assert code.name == "Test Code"
        assert code.color.to_hex() == "#ff0000"

        # Verify event was published
        history = event_bus.get_history()
        assert len(history) == 1
        assert isinstance(history[0].event, CodeCreated)

    def test_fails_with_empty_name(self, controller):
        """Test failure with empty name."""
        command = CreateCodeCommand(name="", color="#ff0000")

        result = controller.create_code(command)

        assert isinstance(result, Failure)

    def test_fails_with_duplicate_name(self, controller):
        """Test failure with duplicate name."""
        command1 = CreateCodeCommand(name="Duplicate", color="#ff0000")
        command2 = CreateCodeCommand(name="Duplicate", color="#00ff00")

        controller.create_code(command1)
        result = controller.create_code(command2)

        assert isinstance(result, Failure)

    def test_fails_with_invalid_color(self, controller):
        """Test failure with invalid color."""
        command = CreateCodeCommand(name="Test", color="invalid")

        result = controller.create_code(command)

        assert isinstance(result, Failure)

    def test_creates_code_with_category(self, controller):
        """Test creating code in a category."""
        # First create a category
        cat_command = CreateCategoryCommand(name="Category1")
        cat_result = controller.create_category(cat_command)
        category = cat_result.unwrap()

        # Create code in category
        command = CreateCodeCommand(
            name="Test Code",
            color="#ff0000",
            category_id=category.id.value,
        )
        result = controller.create_code(command)

        assert isinstance(result, Success)
        code = result.unwrap()
        assert code.category_id == category.id


class TestRenameCode:
    """Tests for rename_code command."""

    def test_renames_code_successfully(self, controller, event_bus):
        """Test successful code rename."""
        # Create a code first
        create_cmd = CreateCodeCommand(name="Original", color="#ff0000")
        code = controller.create_code(create_cmd).unwrap()

        # Rename it
        rename_cmd = RenameCodeCommand(code_id=code.id.value, new_name="Renamed")
        result = controller.rename_code(rename_cmd)

        assert isinstance(result, Success)

        # Verify the code was renamed
        updated = controller.get_code(code.id.value)
        assert updated.name == "Renamed"

        # Verify event
        history = event_bus.get_history()
        assert any(isinstance(r.event, CodeRenamed) for r in history)

    def test_fails_for_nonexistent_code(self, controller):
        """Test failure for nonexistent code."""
        command = RenameCodeCommand(code_id=999, new_name="New Name")

        result = controller.rename_code(command)

        assert isinstance(result, Failure)

    def test_fails_for_duplicate_name(self, controller):
        """Test failure when renaming to existing name."""
        controller.create_code(CreateCodeCommand(name="First", color="#ff0000"))
        code2 = controller.create_code(
            CreateCodeCommand(name="Second", color="#00ff00")
        ).unwrap()

        command = RenameCodeCommand(code_id=code2.id.value, new_name="First")
        result = controller.rename_code(command)

        assert isinstance(result, Failure)


class TestChangeCodeColor:
    """Tests for change_code_color command."""

    def test_changes_color_successfully(self, controller, event_bus):
        """Test successful color change."""
        code = controller.create_code(
            CreateCodeCommand(name="Test", color="#ff0000")
        ).unwrap()

        command = ChangeCodeColorCommand(code_id=code.id.value, new_color="#00ff00")
        result = controller.change_code_color(command)

        assert isinstance(result, Success)

        updated = controller.get_code(code.id.value)
        assert updated.color.to_hex() == "#00ff00"

        history = event_bus.get_history()
        assert any(isinstance(r.event, CodeColorChanged) for r in history)

    def test_fails_for_invalid_color(self, controller):
        """Test failure with invalid color."""
        code = controller.create_code(
            CreateCodeCommand(name="Test", color="#ff0000")
        ).unwrap()

        command = ChangeCodeColorCommand(code_id=code.id.value, new_color="bad")
        result = controller.change_code_color(command)

        assert isinstance(result, Failure)


class TestDeleteCode:
    """Tests for delete_code command."""

    def test_deletes_code_successfully(self, controller, event_bus):
        """Test successful code deletion."""
        code = controller.create_code(
            CreateCodeCommand(name="ToDelete", color="#ff0000")
        ).unwrap()

        command = DeleteCodeCommand(code_id=code.id.value)
        result = controller.delete_code(command)

        assert isinstance(result, Success)
        assert controller.get_code(code.id.value) is None

        history = event_bus.get_history()
        assert any(isinstance(r.event, CodeDeleted) for r in history)

    def test_fails_when_has_segments_and_not_force(self, controller):
        """Test failure when code has segments and delete_segments=False."""
        code = controller.create_code(
            CreateCodeCommand(name="WithSegments", color="#ff0000")
        ).unwrap()

        # Apply code to create a segment
        apply_cmd = ApplyCodeCommand(
            code_id=code.id.value,
            source_id=1,
            start_position=0,
            end_position=10,
        )
        controller.apply_code(apply_cmd)

        # Try to delete without force
        delete_cmd = DeleteCodeCommand(code_id=code.id.value, delete_segments=False)
        result = controller.delete_code(delete_cmd)

        assert isinstance(result, Failure)

    def test_deletes_with_segments_when_forced(self, controller):
        """Test deletion with segments when delete_segments=True."""
        code = controller.create_code(
            CreateCodeCommand(name="WithSegments", color="#ff0000")
        ).unwrap()

        apply_cmd = ApplyCodeCommand(
            code_id=code.id.value,
            source_id=1,
            start_position=0,
            end_position=10,
        )
        controller.apply_code(apply_cmd)

        # Delete with force
        delete_cmd = DeleteCodeCommand(code_id=code.id.value, delete_segments=True)
        result = controller.delete_code(delete_cmd)

        assert isinstance(result, Success)
        assert controller.get_code(code.id.value) is None


class TestMergeCodes:
    """Tests for merge_codes command."""

    def test_merges_codes_successfully(self, controller, event_bus):
        """Test successful code merge."""
        source = controller.create_code(
            CreateCodeCommand(name="Source", color="#ff0000")
        ).unwrap()
        target = controller.create_code(
            CreateCodeCommand(name="Target", color="#00ff00")
        ).unwrap()

        # Add segment to source
        controller.apply_code(
            ApplyCodeCommand(
                code_id=source.id.value,
                source_id=1,
                start_position=0,
                end_position=10,
            )
        )

        # Merge
        command = MergeCodesCommand(
            source_code_id=source.id.value, target_code_id=target.id.value
        )
        result = controller.merge_codes(command)

        assert isinstance(result, Success)

        # Source should be deleted
        assert controller.get_code(source.id.value) is None

        # Segments should be reassigned to target
        segments = controller.get_segments_for_code(target.id.value)
        assert len(segments) == 1

        history = event_bus.get_history()
        assert any(isinstance(r.event, CodesMerged) for r in history)


class TestApplyCode:
    """Tests for apply_code command."""

    def test_applies_code_successfully(self, controller, event_bus):
        """Test successful code application."""
        code = controller.create_code(
            CreateCodeCommand(name="Test", color="#ff0000")
        ).unwrap()

        command = ApplyCodeCommand(
            code_id=code.id.value,
            source_id=1,
            start_position=0,
            end_position=10,
            memo="Test memo",
        )
        result = controller.apply_code(command)

        assert isinstance(result, Success)
        segment = result.unwrap()
        assert segment.code_id == code.id
        assert segment.position.start == 0
        assert segment.position.end == 10

        history = event_bus.get_history()
        assert any(isinstance(r.event, SegmentCoded) for r in history)

    def test_fails_for_nonexistent_code(self, controller):
        """Test failure for nonexistent code."""
        command = ApplyCodeCommand(
            code_id=999,
            source_id=1,
            start_position=0,
            end_position=10,
        )
        result = controller.apply_code(command)

        assert isinstance(result, Failure)


class TestRemoveCode:
    """Tests for remove_code command (uncoding)."""

    def test_removes_segment_successfully(self, controller, event_bus):
        """Test successful segment removal."""
        code = controller.create_code(
            CreateCodeCommand(name="Test", color="#ff0000")
        ).unwrap()

        segment = controller.apply_code(
            ApplyCodeCommand(
                code_id=code.id.value,
                source_id=1,
                start_position=0,
                end_position=10,
            )
        ).unwrap()

        command = RemoveCodeCommand(segment_id=segment.id.value)
        result = controller.remove_code(command)

        assert isinstance(result, Success)

        # Segment should be gone
        segments = controller.get_segments_for_code(code.id.value)
        assert len(segments) == 0

        history = event_bus.get_history()
        assert any(isinstance(r.event, SegmentUncoded) for r in history)


class TestCreateCategory:
    """Tests for create_category command."""

    def test_creates_category_successfully(self, controller, event_bus):
        """Test successful category creation."""
        command = CreateCategoryCommand(name="Test Category", memo="A memo")

        result = controller.create_category(command)

        assert isinstance(result, Success)
        category = result.unwrap()
        assert category.name == "Test Category"
        assert category.memo == "A memo"

        history = event_bus.get_history()
        assert any(isinstance(r.event, CategoryCreated) for r in history)

    def test_creates_nested_category(self, controller):
        """Test creating a nested category."""
        parent = controller.create_category(
            CreateCategoryCommand(name="Parent")
        ).unwrap()

        child_cmd = CreateCategoryCommand(name="Child", parent_id=parent.id.value)
        result = controller.create_category(child_cmd)

        assert isinstance(result, Success)
        child = result.unwrap()
        assert child.parent_id == parent.id


class TestDeleteCategory:
    """Tests for delete_category command."""

    def test_deletes_category_successfully(self, controller, event_bus):
        """Test successful category deletion."""
        category = controller.create_category(
            CreateCategoryCommand(name="ToDelete")
        ).unwrap()

        command = DeleteCategoryCommand(category_id=category.id.value)
        result = controller.delete_category(command)

        assert isinstance(result, Success)

        categories = controller.get_all_categories()
        assert len(categories) == 0

        history = event_bus.get_history()
        assert any(isinstance(r.event, CategoryDeleted) for r in history)

    def test_moves_codes_to_parent_on_delete(self, controller):
        """Test that codes are moved to parent when category is deleted."""
        parent = controller.create_category(
            CreateCategoryCommand(name="Parent")
        ).unwrap()
        child = controller.create_category(
            CreateCategoryCommand(name="Child", parent_id=parent.id.value)
        ).unwrap()

        # Create code in child category
        code = controller.create_code(
            CreateCodeCommand(name="Code", color="#ff0000", category_id=child.id.value)
        ).unwrap()

        # Delete child category
        controller.delete_category(
            DeleteCategoryCommand(
                category_id=child.id.value, orphan_strategy="move_to_parent"
            )
        )

        # Code should now be in parent category
        updated_code = controller.get_code(code.id.value)
        assert updated_code.category_id == parent.id


class TestQueries:
    """Tests for query methods."""

    def test_get_all_codes(self, controller):
        """Test getting all codes."""
        controller.create_code(CreateCodeCommand(name="Code1", color="#ff0000"))
        controller.create_code(CreateCodeCommand(name="Code2", color="#00ff00"))

        codes = controller.get_all_codes()

        assert len(codes) == 2
        names = {c.name for c in codes}
        assert names == {"Code1", "Code2"}

    def test_get_segments_for_source(self, controller):
        """Test getting segments by source."""
        code = controller.create_code(
            CreateCodeCommand(name="Test", color="#ff0000")
        ).unwrap()

        controller.apply_code(
            ApplyCodeCommand(
                code_id=code.id.value, source_id=1, start_position=0, end_position=10
            )
        )
        controller.apply_code(
            ApplyCodeCommand(
                code_id=code.id.value, source_id=1, start_position=20, end_position=30
            )
        )
        controller.apply_code(
            ApplyCodeCommand(
                code_id=code.id.value, source_id=2, start_position=0, end_position=5
            )
        )

        segments = controller.get_segments_for_source(1)
        assert len(segments) == 2

    def test_get_all_categories(self, controller):
        """Test getting all categories."""
        controller.create_category(CreateCategoryCommand(name="Cat1"))
        controller.create_category(CreateCategoryCommand(name="Cat2"))

        categories = controller.get_all_categories()

        assert len(categories) == 2
