"""
Coding Controller - Application Service

Orchestrates domain operations by:
1. Loading state from repositories
2. Calling pure domain derivers
3. Persisting changes on success
4. Publishing domain events

This is the "Imperative Shell" that coordinates the "Functional Core".
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from returns.result import Failure, Result, Success

from src.application.protocols import (
    ApplyCodeCommand,
    ChangeCodeColorCommand,
    CreateCategoryCommand,
    CreateCodeCommand,
    DeleteCategoryCommand,
    DeleteCodeCommand,
    MergeCodesCommand,
    MoveCodeToCategoryCommand,
    RemoveCodeCommand,
    RenameCodeCommand,
    UpdateCodeMemoCommand,
)
from src.domain.coding.derivers import (
    CodingState,
    derive_apply_code_to_text,
    derive_change_code_color,
    derive_create_category,
    derive_create_code,
    derive_delete_category,
    derive_delete_code,
    derive_merge_codes,
    derive_move_code_to_category,
    derive_remove_segment,
    derive_rename_code,
    derive_update_code_memo,
)
from src.domain.coding.entities import Category, Code, Color, TextSegment
from src.domain.coding.events import (
    CategoryCreated,
    CategoryDeleted,
    CodeColorChanged,
    CodeCreated,
    CodeDeleted,
    CodeMemoUpdated,
    CodeMovedToCategory,
    CodeRenamed,
    CodesMerged,
    SegmentCoded,
    SegmentUncoded,
)
from src.domain.shared.types import CategoryId, CodeId, SegmentId, SourceId

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.infrastructure.coding.repositories import (
        SQLiteCategoryRepository,
        SQLiteCodeRepository,
        SQLiteSegmentRepository,
    )


class CodingControllerImpl:
    """
    Implementation of the CodingController protocol.

    Coordinates between:
    - Domain derivers (pure business logic)
    - Repositories (data persistence)
    - Event bus (event publishing)
    """

    def __init__(
        self,
        code_repo: SQLiteCodeRepository,
        category_repo: SQLiteCategoryRepository,
        segment_repo: SQLiteSegmentRepository,
        event_bus: EventBus,
        source_content_provider: Any | None = None,
    ) -> None:
        """
        Initialize the controller with dependencies.

        Args:
            code_repo: Repository for Code entities
            category_repo: Repository for Category entities
            segment_repo: Repository for Segment entities
            event_bus: Event bus for publishing domain events
            source_content_provider: Optional provider for source content/length
        """
        self._code_repo = code_repo
        self._category_repo = category_repo
        self._segment_repo = segment_repo
        self._event_bus = event_bus
        self._source_provider = source_content_provider

    # =========================================================================
    # Code Commands
    # =========================================================================

    def create_code(self, command: CreateCodeCommand) -> Result:
        """Create a new code in the codebook."""
        # Build current state
        state = self._build_coding_state()

        # Parse color
        try:
            color = Color.from_hex(command.color)
        except ValueError as e:
            return Failure(str(e))

        # Derive event or failure
        category_id = (
            CategoryId(value=command.category_id) if command.category_id else None
        )
        result = derive_create_code(
            name=command.name,
            color=color,
            memo=command.memo,
            category_id=category_id,
            owner=None,  # Could come from session context
            state=state,
        )

        # Handle result
        if isinstance(result, Failure):
            return result

        # It's a CodeCreated event
        event: CodeCreated = result

        # Create and persist the entity
        code = Code(
            id=event.code_id,
            name=event.name,
            color=event.color,
            memo=event.memo,
            category_id=event.category_id,
            owner=event.owner,
        )
        self._code_repo.save(code)

        # Publish event
        self._event_bus.publish(event)

        return Success(code)

    def rename_code(self, command: RenameCodeCommand) -> Result:
        """Rename an existing code."""
        state = self._build_coding_state()
        code_id = CodeId(value=command.code_id)

        result = derive_rename_code(
            code_id=code_id,
            new_name=command.new_name,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CodeRenamed = result

        # Update entity
        code = self._code_repo.get_by_id(code_id)
        if code:
            updated_code = code.with_name(event.new_name)
            self._code_repo.save(updated_code)

        self._event_bus.publish(event)
        return Success(event)

    def change_code_color(self, command: ChangeCodeColorCommand) -> Result:
        """Change a code's color."""
        state = self._build_coding_state()
        code_id = CodeId(value=command.code_id)

        try:
            new_color = Color.from_hex(command.new_color)
        except ValueError as e:
            return Failure(str(e))

        result = derive_change_code_color(
            code_id=code_id,
            new_color=new_color,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CodeColorChanged = result

        # Update entity
        code = self._code_repo.get_by_id(code_id)
        if code:
            updated_code = code.with_color(event.new_color)
            self._code_repo.save(updated_code)

        self._event_bus.publish(event)
        return Success(event)

    def delete_code(self, command: DeleteCodeCommand) -> Result:
        """Delete a code from the codebook."""
        state = self._build_coding_state()
        code_id = CodeId(value=command.code_id)

        result = derive_delete_code(
            code_id=code_id,
            delete_segments=command.delete_segments,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CodeDeleted = result

        # Delete segments if requested
        if command.delete_segments:
            self._segment_repo.delete_by_code(code_id)

        # Delete the code
        self._code_repo.delete(code_id)

        self._event_bus.publish(event)
        return Success(event)

    def merge_codes(self, command: MergeCodesCommand) -> Result:
        """Merge source code into target code."""
        state = self._build_coding_state()
        source_code_id = CodeId(value=command.source_code_id)
        target_code_id = CodeId(value=command.target_code_id)

        result = derive_merge_codes(
            source_code_id=source_code_id,
            target_code_id=target_code_id,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CodesMerged = result

        # Reassign segments from source to target
        self._segment_repo.reassign_code(source_code_id, target_code_id)

        # Delete the source code
        self._code_repo.delete(source_code_id)

        self._event_bus.publish(event)
        return Success(event)

    def update_code_memo(self, command: UpdateCodeMemoCommand) -> Result:
        """Update a code's memo."""
        state = self._build_coding_state()
        code_id = CodeId(value=command.code_id)

        result = derive_update_code_memo(
            code_id=code_id,
            new_memo=command.new_memo,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CodeMemoUpdated = result

        # Update entity
        code = self._code_repo.get_by_id(code_id)
        if code:
            updated_code = code.with_memo(event.new_memo)
            self._code_repo.save(updated_code)

        self._event_bus.publish(event)
        return Success(event)

    def move_code_to_category(self, command: MoveCodeToCategoryCommand) -> Result:
        """Move a code to a different category."""
        state = self._build_coding_state()
        code_id = CodeId(value=command.code_id)
        new_category_id = (
            CategoryId(value=command.category_id) if command.category_id else None
        )

        result = derive_move_code_to_category(
            code_id=code_id,
            new_category_id=new_category_id,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CodeMovedToCategory = result

        # Update entity
        code = self._code_repo.get_by_id(code_id)
        if code:
            updated_code = code.with_category(event.new_category_id)
            self._code_repo.save(updated_code)

        self._event_bus.publish(event)
        return Success(event)

    # =========================================================================
    # Segment Commands
    # =========================================================================

    def apply_code(self, command: ApplyCodeCommand) -> Result:
        """Apply a code to a text segment."""
        code_id = CodeId(value=command.code_id)
        source_id = SourceId(value=command.source_id)

        # Get source content for the selected text
        selected_text = self._get_selected_text(
            source_id, command.start_position, command.end_position
        )

        # Build state with source info
        state = self._build_coding_state(
            source_id=source_id,
            source_exists=True,  # Assume exists for now
        )

        result = derive_apply_code_to_text(
            code_id=code_id,
            source_id=source_id,
            start=command.start_position,
            end=command.end_position,
            selected_text=selected_text,
            memo=command.memo,
            importance=command.importance,
            owner=None,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: SegmentCoded = result

        # Create and persist segment
        segment = TextSegment(
            id=event.segment_id,
            source_id=source_id,
            code_id=code_id,
            position=event.position,
            selected_text=event.selected_text,
            memo=event.memo,
            importance=command.importance,
            owner=event.owner,
        )
        self._segment_repo.save(segment)

        self._event_bus.publish(event)
        return Success(segment)

    def remove_code(self, command: RemoveCodeCommand) -> Result:
        """Remove coding from a segment."""
        segment_id = SegmentId(value=command.segment_id)
        state = self._build_coding_state()

        result = derive_remove_segment(
            segment_id=segment_id,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: SegmentUncoded = result

        # Delete the segment
        self._segment_repo.delete(segment_id)

        self._event_bus.publish(event)
        return Success(event)

    # =========================================================================
    # Category Commands
    # =========================================================================

    def create_category(self, command: CreateCategoryCommand) -> Result:
        """Create a new code category."""
        state = self._build_coding_state()
        parent_id = CategoryId(value=command.parent_id) if command.parent_id else None

        result = derive_create_category(
            name=command.name,
            parent_id=parent_id,
            memo=command.memo,
            owner=None,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CategoryCreated = result

        # Create and persist category
        category = Category(
            id=event.category_id,
            name=event.name,
            parent_id=event.parent_id,
            memo=event.memo,
        )
        self._category_repo.save(category)

        self._event_bus.publish(event)
        return Success(category)

    def delete_category(self, command: DeleteCategoryCommand) -> Result:
        """Delete a code category."""
        state = self._build_coding_state()
        category_id = CategoryId(value=command.category_id)

        result = derive_delete_category(
            category_id=category_id,
            orphan_strategy=command.orphan_strategy,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CategoryDeleted = result

        # Handle orphaned codes based on strategy
        if command.orphan_strategy == "move_to_parent":
            category = self._category_repo.get_by_id(category_id)
            parent_id = category.parent_id if category else None
            # Update codes to point to parent (or None)
            for code in self._code_repo.get_by_category(category_id):
                updated_code = code.with_category(parent_id)
                self._code_repo.save(updated_code)

        # Delete the category
        self._category_repo.delete(category_id)

        self._event_bus.publish(event)
        return Success(event)

    # =========================================================================
    # Queries
    # =========================================================================

    def get_all_codes(self) -> list[Code]:
        """Get all codes in the project."""
        return self._code_repo.get_all()

    def get_code(self, code_id: int) -> Code | None:
        """Get a specific code by ID."""
        return self._code_repo.get_by_id(CodeId(value=code_id))

    def get_segments_for_source(self, source_id: int) -> list[TextSegment]:
        """Get all segments for a source."""
        return self._segment_repo.get_by_source(SourceId(value=source_id))

    def get_segments_for_code(self, code_id: int) -> list[TextSegment]:
        """Get all segments with a specific code."""
        return self._segment_repo.get_by_code(CodeId(value=code_id))

    def get_all_categories(self) -> list[Category]:
        """Get all categories."""
        return self._category_repo.get_all()

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _build_coding_state(
        self,
        source_id: SourceId | None = None,
        source_exists: bool = True,
    ) -> CodingState:
        """Build the current state for derivers."""
        codes = tuple(self._code_repo.get_all())
        categories = tuple(self._category_repo.get_all())
        segments = tuple(self._segment_repo.get_all())

        source_length = None
        if source_id and self._source_provider:
            source_length = self._source_provider.get_length(source_id)

        return CodingState(
            existing_codes=codes,
            existing_categories=categories,
            existing_segments=segments,
            source_length=source_length,
            source_exists=source_exists,
        )

    def _get_selected_text(self, source_id: SourceId, start: int, end: int) -> str:
        """Get the selected text from a source."""
        if self._source_provider:
            content = self._source_provider.get_content(source_id)
            if content:
                return content[start:end]
        # Fallback: return placeholder
        return f"[text from {start} to {end}]"
