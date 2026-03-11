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
    from src.shared.infra.session import Session


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
        session: Session | None = None,
    ) -> None:
        self._code_repo = code_repo
        self._category_repo = category_repo
        self._segment_repo = segment_repo
        self._event_bus = event_bus
        self._session = session

    def _dispatch(self, handler, command) -> OperationResult:
        """Dispatch a command to a handler with all standard dependencies."""
        return handler(
            command,
            self._code_repo,
            self._category_repo,
            self._segment_repo,
            self._event_bus,
            session=self._session,
        )

    # =========================================================================
    # Commands
    # =========================================================================

    def create_code(self, command: CreateCodeCommand) -> OperationResult:
        """Create a new code."""
        return self._dispatch(create_code, command)

    def rename_code(self, command: RenameCodeCommand) -> OperationResult:
        """Rename an existing code."""
        return self._dispatch(rename_code, command)

    def delete_code(self, command: DeleteCodeCommand) -> OperationResult:
        """Delete a code."""
        return self._dispatch(delete_code, command)

    def update_code_memo(self, command: UpdateCodeMemoCommand) -> OperationResult:
        """Update a code's memo."""
        return self._dispatch(update_code_memo, command)

    def move_code_to_category(
        self, command: MoveCodeToCategoryCommand
    ) -> OperationResult:
        """Move a code to a different category."""
        return self._dispatch(move_code_to_category, command)

    def apply_code(self, command: ApplyCodeCommand) -> OperationResult:
        """Apply a code to a text segment."""
        return self._dispatch(apply_code, command)

    def remove_segment(self, command: RemoveCodeCommand) -> OperationResult:
        """Remove coding from a segment."""
        return self._dispatch(remove_segment, command)

    def create_category(self, command: CreateCategoryCommand) -> OperationResult:
        """Create a new category."""
        return self._dispatch(create_category, command)

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

    def get_segment_counts_by_code(self) -> dict[int, int]:
        """
        Get segment counts for all codes in a single query.

        Returns:
            Dictionary mapping code_id to segment count
        """
        return self._segment_repo.count_all_by_code()
