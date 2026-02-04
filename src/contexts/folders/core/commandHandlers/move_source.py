"""
Move Source to Folder Use Case

Functional use case for moving a source to a folder.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.folders.core.commandHandlers._state import (
    FolderRepository,
    SourceRepository,
)
from src.contexts.projects.core.commands import MoveSourceToFolderCommand
from src.contexts.projects.core.derivers import (
    FolderState,
    derive_move_source_to_folder,
)
from src.contexts.projects.core.events import SourceMovedToFolder
from src.contexts.projects.core.failure_events import SourceNotMoved
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import FolderId, SourceId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def move_source_to_folder(
    command: MoveSourceToFolderCommand,
    state: ProjectState,
    folder_repo: FolderRepository | None,
    source_repo: SourceRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Move a source to a different folder.

    Args:
        command: Command with source ID and target folder ID
        state: Project state cache
        source_repo: Repository for source operations
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with SourceMovedToFolder event on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_MOVED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    source_id = SourceId(value=command.source_id)
    folder_id = (
        FolderId(value=command.folder_id) if command.folder_id is not None else None
    )

    # Build state and derive event
    # Get existing data from repos (source of truth) instead of state cache
    existing_folders = tuple(folder_repo.get_all()) if folder_repo else ()
    existing_sources = tuple(source_repo.get_all()) if source_repo else ()
    folder_state = FolderState(
        existing_folders=existing_folders,
        existing_sources=existing_sources,
    )

    result = derive_move_source_to_folder(
        source_id=source_id,
        folder_id=folder_id,
        state=folder_state,
    )

    if isinstance(result, SourceNotMoved):
        return OperationResult.fail(
            error=result.reason,
            error_code=f"SOURCE_NOT_MOVED/{result.event_type.upper()}",
        )

    event: SourceMovedToFolder = result

    # Find and update the source
    if source_repo:
        source = source_repo.get_by_id(source_id)
        if source:
            updated_source = source.with_folder(event.new_folder_id)
            source_repo.save(updated_source)

    # Publish event
    event_bus.publish(event)

    # Get old folder ID for rollback
    old_folder_id = event.old_folder_id.value if event.old_folder_id else None
    return OperationResult.ok(
        data=event,
        rollback=MoveSourceToFolderCommand(
            source_id=command.source_id, folder_id=old_folder_id
        ),
    )
