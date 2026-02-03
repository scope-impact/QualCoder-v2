"""
Delete Folder Use Case

Functional use case for deleting an empty folder.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.folders.core.commandHandlers._state import (
    FolderRepository,
    SourceRepository,
)
from src.contexts.projects.core.commands import DeleteFolderCommand
from src.contexts.projects.core.derivers import FolderState, derive_delete_folder
from src.contexts.projects.core.events import FolderDeleted
from src.contexts.projects.core.failure_events import FolderNotDeleted
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import FolderId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def delete_folder(
    command: DeleteFolderCommand,
    state: ProjectState,
    folder_repo: FolderRepository | None,
    source_repo: SourceRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Delete an empty folder.

    Args:
        command: Command with folder ID
        state: Project state cache
        folder_repo: Repository for folder operations
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
    # Get existing data from repos (source of truth) instead of state cache
    existing_folders = tuple(folder_repo.get_all()) if folder_repo else ()
    existing_sources = tuple(source_repo.get_all()) if source_repo else ()
    folder_state = FolderState(
        existing_folders=existing_folders,
        existing_sources=existing_sources,
    )

    result = derive_delete_folder(folder_id=folder_id, state=folder_state)

    if isinstance(result, FolderNotDeleted):
        return OperationResult.fail(
            error=result.reason,
            error_code=f"FOLDER_NOT_DELETED/{result.event_type.upper()}",
        )

    event: FolderDeleted = result

    # Delete from repository (source of truth)
    if folder_repo:
        folder_repo.delete(folder_id)

    # Publish event
    event_bus.publish(event)

    # No rollback - would need to recreate folder
    return OperationResult.ok(data=event)
