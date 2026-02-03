"""
Delete Folder Use Case

Functional use case for deleting an empty folder.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.projects.commands import DeleteFolderCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import FolderState, derive_delete_folder
from src.contexts.projects.core.events import FolderDeleted
from src.contexts.projects.core.failure_events import FolderNotDeleted
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import FolderId

if TYPE_CHECKING:
    from src.application.contexts import SourcesContext
    from src.application.event_bus import EventBus


def delete_folder(
    command: DeleteFolderCommand,
    state: ProjectState,
    sources_ctx: SourcesContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Delete an empty folder.

    Args:
        command: Command with folder ID
        state: Project state cache
        sources_ctx: Sources context with folder repository
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with FolderDeleted event on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="FOLDER_NOT_DELETED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    folder_id = FolderId(value=command.folder_id)

    # Build state and derive event
    folder_state = FolderState(
        existing_folders=tuple(state.folders),
        existing_sources=tuple(state.sources),
    )

    result = derive_delete_folder(folder_id=folder_id, state=folder_state)

    if isinstance(result, FolderNotDeleted):
        return OperationResult.fail(
            error=result.reason,
            error_code=f"FOLDER_NOT_DELETED/{result.event_type.upper()}",
        )

    event: FolderDeleted = result

    # Delete from repository and update state
    if sources_ctx and sources_ctx.folder_repo:
        sources_ctx.folder_repo.delete(folder_id)

    state.remove_folder(command.folder_id)

    # Publish event
    event_bus.publish(event)

    # No rollback - would need to recreate folder
    return OperationResult.ok(data=event)
