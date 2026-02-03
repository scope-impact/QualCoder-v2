"""
Move Source to Folder Use Case

Functional use case for moving a source to a folder.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.projects.commands import MoveSourceToFolderCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import (
    FolderState,
    derive_move_source_to_folder,
)
from src.contexts.projects.core.events import SourceMovedToFolder
from src.contexts.projects.core.failure_events import SourceNotMoved
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import FolderId, SourceId

if TYPE_CHECKING:
    from src.application.contexts import SourcesContext
    from src.application.event_bus import EventBus


def move_source_to_folder(
    command: MoveSourceToFolderCommand,
    state: ProjectState,
    sources_ctx: SourcesContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Move a source to a different folder.

    Args:
        command: Command with source ID and target folder ID
        state: Project state cache
        sources_ctx: Sources context with repositories
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
    folder_state = FolderState(
        existing_folders=tuple(state.folders),
        existing_sources=tuple(state.sources),
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
    source = state.get_source(command.source_id)
    if source:
        updated_source = source.with_folder(event.new_folder_id)

        # Persist and update state
        if sources_ctx and sources_ctx.source_repo:
            sources_ctx.source_repo.save(updated_source)

        state.update_source(updated_source)

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
