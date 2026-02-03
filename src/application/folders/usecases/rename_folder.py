"""
Rename Folder Use Case

Functional use case for renaming a folder.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.projects.commands import RenameFolderCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import FolderState, derive_rename_folder
from src.contexts.projects.core.events import FolderRenamed
from src.contexts.projects.core.failure_events import FolderNotRenamed
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import FolderId

if TYPE_CHECKING:
    from src.application.contexts import SourcesContext
    from src.application.event_bus import EventBus


def rename_folder(
    command: RenameFolderCommand,
    state: ProjectState,
    sources_ctx: SourcesContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Rename an existing folder.

    Args:
        command: Command with folder ID and new name
        state: Project state cache
        sources_ctx: Sources context with folder repository
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with updated Folder on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="FOLDER_NOT_RENAMED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    folder_id = FolderId(value=command.folder_id)

    # Build state and derive event
    folder_state = FolderState(
        existing_folders=tuple(state.folders),
        existing_sources=tuple(state.sources),
    )

    result = derive_rename_folder(
        folder_id=folder_id,
        new_name=command.new_name,
        state=folder_state,
    )

    if isinstance(result, FolderNotRenamed):
        return OperationResult.fail(
            error=result.reason,
            error_code=f"FOLDER_NOT_RENAMED/{result.event_type.upper()}",
        )

    event: FolderRenamed = result

    # Find and update folder
    folder = state.get_folder(command.folder_id)
    if folder is None:
        return OperationResult.fail(
            error=f"Folder {command.folder_id} not found",
            error_code="FOLDER_NOT_RENAMED/NOT_FOUND",
        )

    updated_folder = folder.with_name(event.new_name)

    # Persist and update state
    if sources_ctx and sources_ctx.folder_repo:
        sources_ctx.folder_repo.save(updated_folder)

    state.update_folder(updated_folder)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(
        data=updated_folder,
        rollback=RenameFolderCommand(
            folder_id=command.folder_id, new_name=event.old_name
        ),
    )
