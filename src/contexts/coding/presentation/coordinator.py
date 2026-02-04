"""
Coding Coordinator.

Wraps functional command handlers to provide a stateful interface for ViewModels.
Implements the CodingProvider protocol expected by TextCodingViewModel.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.coding.core.commandHandlers import (
    apply_code,
    create_category,
    create_code,
    delete_code,
    get_all_categories,
    get_all_codes,
    get_code,
    get_segments_for_code,
    get_segments_for_source,
    move_code_to_category,
    remove_segment,
    rename_code,
    update_code_memo,
)
from src.contexts.coding.core.commands import (
    ApplyCodeCommand,
    CreateCategoryCommand,
    CreateCodeCommand,
    DeleteCodeCommand,
    MoveCodeToCategoryCommand,
    RemoveCodeCommand,
    RenameCodeCommand,
    UpdateCodeMemoCommand,
)
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.coding.core.entities import Category, Code, TextSegment
    from src.contexts.coding.infra.repositories import (
        SQLiteCategoryRepository,
        SQLiteCodeRepository,
        SQLiteSegmentRepository,
    )
    from src.shared.infra.event_bus import EventBus


class CodingCoordinator:
    """
    Coordinator for coding operations.

    Provides a stateful interface over functional command handlers.
    Holds references to repositories and event bus.

    This class implements the CodingProvider protocol expected by TextCodingViewModel.
    """

    def __init__(
        self,
        code_repo: SQLiteCodeRepository,
        category_repo: SQLiteCategoryRepository,
        segment_repo: SQLiteSegmentRepository,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize the coordinator.

        Args:
            code_repo: Repository for codes
            category_repo: Repository for categories
            segment_repo: Repository for segments
            event_bus: Event bus for publishing domain events
        """
        self._code_repo = code_repo
        self._category_repo = category_repo
        self._segment_repo = segment_repo
        self._event_bus = event_bus

    # =========================================================================
    # Commands
    # =========================================================================

    def create_code(self, command: CreateCodeCommand) -> OperationResult:
        """Create a new code."""
        return create_code(
            command,
            self._code_repo,
            self._category_repo,
            self._segment_repo,
            self._event_bus,
        )

    def rename_code(self, command: RenameCodeCommand) -> OperationResult:
        """Rename an existing code."""
        return rename_code(
            command,
            self._code_repo,
            self._category_repo,
            self._segment_repo,
            self._event_bus,
        )

    def delete_code(self, command: DeleteCodeCommand) -> OperationResult:
        """Delete a code."""
        return delete_code(
            command,
            self._code_repo,
            self._category_repo,
            self._segment_repo,
            self._event_bus,
        )

    def update_code_memo(self, command: UpdateCodeMemoCommand) -> OperationResult:
        """Update a code's memo."""
        return update_code_memo(
            command,
            self._code_repo,
            self._category_repo,
            self._segment_repo,
            self._event_bus,
        )

    def move_code_to_category(
        self, command: MoveCodeToCategoryCommand
    ) -> OperationResult:
        """Move a code to a different category."""
        return move_code_to_category(
            command,
            self._code_repo,
            self._category_repo,
            self._segment_repo,
            self._event_bus,
        )

    def apply_code(self, command: ApplyCodeCommand) -> OperationResult:
        """Apply a code to a text segment."""
        return apply_code(
            command,
            self._code_repo,
            self._category_repo,
            self._segment_repo,
            self._event_bus,
        )

    def remove_segment(self, command: RemoveCodeCommand) -> OperationResult:
        """Remove coding from a segment."""
        return remove_segment(
            command,
            self._code_repo,
            self._category_repo,
            self._segment_repo,
            self._event_bus,
        )

    def create_category(self, command: CreateCategoryCommand) -> OperationResult:
        """Create a new category."""
        return create_category(
            command,
            self._code_repo,
            self._category_repo,
            self._segment_repo,
            self._event_bus,
        )

    # =========================================================================
    # Queries
    # =========================================================================

    def get_all_codes(self) -> list[Code]:
        """Get all codes."""
        return get_all_codes(self._code_repo)

    def get_code(self, code_id: int) -> Code | None:
        """Get a specific code by ID."""
        return get_code(self._code_repo, code_id)

    def get_all_categories(self) -> list[Category]:
        """Get all categories."""
        return get_all_categories(self._category_repo)

    def get_segments_for_source(self, source_id: int) -> list[TextSegment]:
        """Get all segments for a source document."""
        return get_segments_for_source(self._segment_repo, source_id)

    def get_segments_for_code(self, code_id: int) -> list[TextSegment]:
        """Get all segments with a specific code."""
        return get_segments_for_code(self._segment_repo, code_id)
