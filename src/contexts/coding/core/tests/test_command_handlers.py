"""
Coding Context: Command Handler Unit Tests

Tests for command handlers that orchestrate use cases.
These tests verify:
- Success scenarios with OperationResult.ok()
- Failure scenarios with OperationResult.fail()
- Event publishing behavior
- Repository interactions via mocks
- Rollback command generation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import allure
import pytest

from src.contexts.coding.core.commands import (
    ApplyCodeCommand,
    ChangeCodeColorCommand,
    DeleteCategoryCommand,
)
from src.contexts.coding.core.entities import (
    Category,
    Code,
    Color,
    TextPosition,
    TextSegment,
)
from src.shared.common.types import CategoryId, CodeId, SegmentId, SourceId

if TYPE_CHECKING:
    pass

pytestmark = [pytest.mark.unit]


# ============================================================
# Mock Repositories
# ============================================================


@dataclass
class MockCodeRepository:
    """In-memory mock code repository for testing."""

    _codes: dict[int, Code] = field(default_factory=dict)
    _conn: MagicMock = field(default_factory=MagicMock)

    def get_all(self) -> list[Code]:
        return list(self._codes.values())

    def get_by_id(self, code_id: CodeId) -> Code | None:
        return self._codes.get(code_id.value)

    def get_by_category(self, category_id: CategoryId) -> list[Code]:
        return [c for c in self._codes.values() if c.category_id == category_id]

    def save(self, code: Code) -> None:
        self._codes[code.id.value] = code

    def delete(self, code_id: CodeId) -> None:
        self._codes.pop(code_id.value, None)


@dataclass
class MockCategoryRepository:
    """In-memory mock category repository for testing."""

    _categories: dict[int, Category] = field(default_factory=dict)
    _conn: MagicMock = field(default_factory=MagicMock)

    def get_all(self) -> list[Category]:
        return list(self._categories.values())

    def get_by_id(self, category_id: CategoryId) -> Category | None:
        return self._categories.get(category_id.value)

    def save(self, category: Category) -> None:
        self._categories[category.id.value] = category

    def delete(self, category_id: CategoryId) -> None:
        self._categories.pop(category_id.value, None)


@dataclass
class MockSegmentRepository:
    """In-memory mock segment repository for testing."""

    _segments: dict[int, TextSegment] = field(default_factory=dict)
    _conn: MagicMock = field(default_factory=MagicMock)

    def get_all(self) -> list[TextSegment]:
        return list(self._segments.values())

    def get_by_id(self, segment_id: SegmentId) -> TextSegment | None:
        return self._segments.get(segment_id.value)

    def get_by_source(self, source_id: SourceId) -> list[TextSegment]:
        return [s for s in self._segments.values() if s.source_id == source_id]

    def get_by_code(self, code_id: CodeId) -> list[TextSegment]:
        return [s for s in self._segments.values() if s.code_id == code_id]

    def save(self, segment: TextSegment) -> None:
        self._segments[segment.id.value] = segment

    def delete(self, segment_id: SegmentId) -> None:
        self._segments.pop(segment_id.value, None)

    def delete_by_code(self, code_id: CodeId) -> int:
        count = sum(1 for s in self._segments.values() if s.code_id == code_id)
        self._segments = {
            k: v for k, v in self._segments.items() if v.code_id != code_id
        }
        return count

    def reassign_code(self, from_code_id: CodeId, to_code_id: CodeId) -> int:
        count = 0
        for segment in self._segments.values():
            if segment.code_id == from_code_id:
                count += 1
        return count


@dataclass
class MockEventBus:
    """Mock event bus that records published events."""

    published_events: list = field(default_factory=list)

    def publish(self, event) -> None:
        self.published_events.append(event)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def code_repo() -> MockCodeRepository:
    """Create a mock code repository."""
    return MockCodeRepository()


@pytest.fixture
def category_repo() -> MockCategoryRepository:
    """Create a mock category repository."""
    return MockCategoryRepository()


@pytest.fixture
def segment_repo() -> MockSegmentRepository:
    """Create a mock segment repository."""
    return MockSegmentRepository()


@pytest.fixture
def event_bus() -> MockEventBus:
    """Create a mock event bus."""
    return MockEventBus()


@pytest.fixture
def sample_code() -> Code:
    """Create a sample code for testing."""
    return Code(
        id=CodeId(value="1"),
        name="Test Code",
        color=Color(255, 0, 0),
        memo="Test memo",
    )


@pytest.fixture
def sample_category() -> Category:
    """Create a sample category for testing."""
    return Category(
        id=CategoryId(value="1"),
        name="Test Category",
        memo="Test category memo",
    )


@pytest.fixture
def sample_segment() -> TextSegment:
    """Create a sample segment for testing."""
    return TextSegment(
        id=SegmentId(value="1"),
        source_id=SourceId(value="1"),
        code_id=CodeId(value="1"),
        position=TextPosition(start=0, end=10),
        selected_text="Test text",
    )


# ============================================================
# DeleteCategory Handler Tests
# ============================================================


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("Delete Category")
class TestDeleteCategoryHandler:
    """Tests for the delete_category command handler."""

    @allure.title("Successfully deletes category and moves orphan codes to parent")
    def test_delete_category_success_and_move_codes(
        self,
        code_repo: MockCodeRepository,
        category_repo: MockCategoryRepository,
        segment_repo: MockSegmentRepository,
        event_bus: MockEventBus,
    ):
        """Should delete category without codes, and move orphaned codes to parent."""
        from src.contexts.coding.core.commandHandlers.delete_category import (
            delete_category,
        )
        from src.contexts.coding.core.events import CategoryDeleted

        # Setup: parent and child categories
        parent_category = Category(
            id=CategoryId(value="1"),
            name="Parent Category",
        )
        child_category = Category(
            id=CategoryId(value="2"),
            name="Child Category",
            parent_id=parent_category.id,
        )
        category_repo.save(parent_category)
        category_repo.save(child_category)

        # Add a code in the child category
        code_in_child = Code(
            id=CodeId(value="1"),
            name="Code in Child",
            color=Color(128, 128, 128),
            category_id=child_category.id,
        )
        code_repo.save(code_in_child)

        # Delete child category
        command = DeleteCategoryCommand(
            category_id=child_category.id.value,
            orphan_strategy="move_to_parent",
        )
        result = delete_category(
            command=command,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        # Verify success
        assert result.is_success
        assert isinstance(result.data, CategoryDeleted)
        assert result.data.codes_orphaned == 1

        # Verify code was moved to parent
        updated_code = code_repo.get_by_id(CodeId(value="1"))
        assert updated_code is not None
        assert updated_code.category_id == parent_category.id

        # Verify category was deleted and event published
        assert category_repo.get_by_id(child_category.id) is None
        assert len(event_bus.published_events) == 1
        assert isinstance(event_bus.published_events[0], CategoryDeleted)

    @allure.title("Fails with correct error when category not found")
    def test_delete_category_not_found(
        self,
        code_repo: MockCodeRepository,
        category_repo: MockCategoryRepository,
        segment_repo: MockSegmentRepository,
        event_bus: MockEventBus,
    ):
        """Should fail with appropriate error when category doesn't exist."""
        from src.contexts.coding.core.commandHandlers.delete_category import (
            delete_category,
        )

        command = DeleteCategoryCommand(category_id="999", orphan_strategy="move_to_parent")
        result = delete_category(
            command=command,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        assert result.is_failure
        assert result.error_code == "CATEGORY_NOT_DELETED/NOT_FOUND"
        assert not result.success
        assert result.error is not None
        assert "not found" in result.error.lower()
        assert len(event_bus.published_events) == 1


# ============================================================
# ChangeCodeColor Handler Tests
# ============================================================


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("Change Code Color")
class TestChangeCodeColorHandler:
    """Tests for the change_code_color command handler."""

    @allure.title("Successfully changes color and provides rollback command")
    def test_change_code_color_success_with_rollback(
        self,
        code_repo: MockCodeRepository,
        category_repo: MockCategoryRepository,
        segment_repo: MockSegmentRepository,
        event_bus: MockEventBus,
        sample_code: Code,
    ):
        """Should change color, publish event, and return rollback command."""
        from src.contexts.coding.core.commandHandlers.change_code_color import (
            change_code_color,
        )
        from src.contexts.coding.core.events import CodeColorChanged

        code_repo.save(sample_code)
        original_color_hex = sample_code.color.to_hex()

        command = ChangeCodeColorCommand(
            code_id=sample_code.id.value,
            new_color="#00FF00",
        )
        result = change_code_color(
            command=command,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        # Verify success
        assert result.is_success
        assert isinstance(result.data, CodeColorChanged)
        assert result.data.old_color == Color(255, 0, 0)
        assert result.data.new_color == Color(0, 255, 0)

        # Verify code updated in repo
        updated_code = code_repo.get_by_id(sample_code.id)
        assert updated_code is not None
        assert updated_code.color == Color(0, 255, 0)

        # Verify event published
        assert len(event_bus.published_events) == 1
        assert isinstance(event_bus.published_events[0], CodeColorChanged)

        # Verify rollback command
        assert result.rollback_command is not None
        assert isinstance(result.rollback_command, ChangeCodeColorCommand)
        assert result.rollback_command.code_id == sample_code.id.value
        assert result.rollback_command.new_color == original_color_hex

    @allure.title("Fails when code not found or color is invalid")
    def test_change_code_color_failures(
        self,
        code_repo: MockCodeRepository,
        category_repo: MockCategoryRepository,
        segment_repo: MockSegmentRepository,
        event_bus: MockEventBus,
        sample_code: Code,
    ):
        """Should fail for nonexistent code or invalid color with suggestions."""
        from src.contexts.coding.core.commandHandlers.change_code_color import (
            change_code_color,
        )

        # Code not found
        command_nf = ChangeCodeColorCommand(code_id="999", new_color="#00FF00")
        result_nf = change_code_color(
            command=command_nf,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )
        assert result_nf.is_failure
        assert result_nf.error_code == "CODE_NOT_UPDATED/NOT_FOUND"
        assert len(event_bus.published_events) == 1

        # Invalid color
        event_bus.published_events.clear()
        code_repo.save(sample_code)
        command_ic = ChangeCodeColorCommand(
            code_id=sample_code.id.value,
            new_color="not-a-color",
        )
        result_ic = change_code_color(
            command=command_ic,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )
        assert result_ic.is_failure
        assert result_ic.error_code == "CODE_COLOR_NOT_CHANGED/INVALID_COLOR"
        assert result_ic.suggestions is not None
        assert len(result_ic.suggestions) > 0
        assert any("hex" in s.lower() for s in result_ic.suggestions)


# ============================================================
# ApplyCode Handler Tests
# ============================================================


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("Apply Code")
class TestApplyCodeHandler:
    """Tests for the apply_code command handler."""

    @allure.title("Successfully applies code, saves segment, publishes event with rollback")
    def test_apply_code_success(
        self,
        code_repo: MockCodeRepository,
        category_repo: MockCategoryRepository,
        segment_repo: MockSegmentRepository,
        event_bus: MockEventBus,
        sample_code: Code,
    ):
        """Should apply code to segment, save it, publish event, and return rollback."""
        from src.contexts.coding.core.commandHandlers.apply_code import apply_code
        from src.contexts.coding.core.commands import RemoveCodeCommand
        from src.contexts.coding.core.events import SegmentCoded

        code_repo.save(sample_code)

        command = ApplyCodeCommand(
            code_id=sample_code.id.value,
            source_id="1",
            start_position=5,
            end_position=15,
            memo="Important segment",
            importance=1,
        )
        result = apply_code(
            command=command,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        # Verify success
        assert result.is_success
        assert result.data is not None
        segment = result.data
        assert segment.code_id == sample_code.id
        assert segment.source_id == SourceId(value="1")

        # Verify segment saved with correct fields
        saved_segment = segment_repo.get_by_id(result.data.id)
        assert saved_segment is not None
        assert saved_segment.memo == "Important segment"
        assert saved_segment.importance == 1

        # Verify event published
        assert len(event_bus.published_events) == 1
        event = event_bus.published_events[0]
        assert isinstance(event, SegmentCoded)
        assert event.code_id == sample_code.id
        assert event.code_name == sample_code.name
        assert event.source_id == SourceId(value="1")
        assert event.memo == "Important segment"

        # Verify rollback command
        assert result.rollback_command is not None
        assert isinstance(result.rollback_command, RemoveCodeCommand)
        assert result.rollback_command.segment_id == result.data.id.value

    @allure.title("Uses source content provider for selected text")
    def test_apply_code_with_source_content_provider(
        self,
        code_repo: MockCodeRepository,
        category_repo: MockCategoryRepository,
        segment_repo: MockSegmentRepository,
        event_bus: MockEventBus,
        sample_code: Code,
    ):
        """Should use source content provider to get selected text."""
        from src.contexts.coding.core.commandHandlers.apply_code import apply_code

        code_repo.save(sample_code)

        source_provider = MagicMock()
        source_provider.get_content.return_value = "Hello World! This is test content."
        source_provider.get_length.return_value = 34

        command = ApplyCodeCommand(
            code_id=sample_code.id.value,
            source_id="1",
            start_position=0,
            end_position=12,
        )
        result = apply_code(
            command=command,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            source_content_provider=source_provider,
        )

        assert result.is_success
        assert result.data.selected_text == "Hello World!"

    @allure.title("Fails when code does not exist")
    def test_apply_code_code_not_found(
        self,
        code_repo: MockCodeRepository,
        category_repo: MockCategoryRepository,
        segment_repo: MockSegmentRepository,
        event_bus: MockEventBus,
    ):
        """Should fail with appropriate error when code doesn't exist."""
        from src.contexts.coding.core.commandHandlers.apply_code import apply_code

        command = ApplyCodeCommand(
            code_id="999",
            source_id="1",
            start_position=0,
            end_position=10,
        )
        result = apply_code(
            command=command,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        assert result.is_failure
        assert result.error_code == "SEGMENT_NOT_CODED/CODE_NOT_FOUND"
        assert len(event_bus.published_events) == 1


# ============================================================
# Integration-like Tests (Testing Handler Flow)
# ============================================================


@allure.epic("QualCoder v2")
@allure.feature("QC-028 Code Management")
@allure.story("Handler Integration")
class TestHandlerIntegration:
    """Integration-like tests that verify handler flow."""

    @allure.title("Change color then undo via rollback; delete category moves codes")
    def test_color_rollback_and_category_delete_integration(
        self,
        code_repo: MockCodeRepository,
        category_repo: MockCategoryRepository,
        segment_repo: MockSegmentRepository,
        event_bus: MockEventBus,
        sample_code: Code,
    ):
        """Should undo color change via rollback and correctly move codes on category delete."""
        from src.contexts.coding.core.commandHandlers.change_code_color import (
            change_code_color,
        )
        from src.contexts.coding.core.commandHandlers.delete_category import (
            delete_category,
        )

        # --- Color rollback ---
        code_repo.save(sample_code)
        original_color = sample_code.color

        command = ChangeCodeColorCommand(
            code_id=sample_code.id.value,
            new_color="#00FF00",
        )
        result = change_code_color(
            command=command,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )
        assert result.is_success
        assert code_repo.get_by_id(sample_code.id).color == Color(0, 255, 0)

        rollback_result = change_code_color(
            command=result.rollback_command,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )
        assert rollback_result.is_success
        assert code_repo.get_by_id(sample_code.id).color == original_color

        # --- Category delete with code hierarchy ---
        event_bus.published_events.clear()
        root = Category(id=CategoryId(value="1"), name="Root")
        parent = Category(id=CategoryId(value="2"), name="Parent", parent_id=root.id)
        child = Category(id=CategoryId(value="3"), name="Child", parent_id=parent.id)
        category_repo.save(root)
        category_repo.save(parent)
        category_repo.save(child)

        code1 = Code(id=CodeId(value="10"), name="Code1", color=Color(255, 0, 0), category_id=child.id)
        code2 = Code(id=CodeId(value="20"), name="Code2", color=Color(0, 255, 0), category_id=child.id)
        code_repo.save(code1)
        code_repo.save(code2)

        del_command = DeleteCategoryCommand(
            category_id=child.id.value,
            orphan_strategy="move_to_parent",
        )
        del_result = delete_category(
            command=del_command,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )
        assert del_result.is_success
        assert code_repo.get_by_id(CodeId(value="10")).category_id == parent.id
        assert code_repo.get_by_id(CodeId(value="20")).category_id == parent.id
