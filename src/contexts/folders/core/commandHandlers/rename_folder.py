"""
Rename Folder Use Case

Functional use case for renaming a folder.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.folders.core.commandHandlers._state import (
    FolderRepository,
    SourceRepository,
)
from src.contexts.projects.core.commands import RenameFolderCommand
from src.contexts.projects.core.derivers import FolderState, derive_rename_folder
from src.contexts.projects.core.events import FolderRenamed
from src.contexts.projects.core.failure_events import FolderNotRenamed
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import FolderId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def rename_folder(
    command: RenameFolderCommand,
    state: ProjectState,
    folder_repo: FolderRepository | None,
    source_repo: SourceRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Rename an existing folder.

    Args:
        command: Command with folder ID and new name
        state: Project state cache
        folder_repo: Repository for folder operations
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
    # Get existing data from repos (source of truth) instead of state cache
    existing_folders = tuple(folder_repo.get_all()) if folder_repo else ()
    existing_sources = tuple(source_repo.get_all()) if source_repo else ()
    folder_state = FolderState(
        existing_folders=existing_folders,
        existing_sources=existing_sources,
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
    folder = folder_repo.get_by_id(folder_id) if folder_repo else None
    if folder is None:
        return OperationResult.fail(
            error=f"Folder {command.folder_id} not found",
            error_code="FOLDER_NOT_RENAMED/NOT_FOUND",
        )

    updated_folder = folder.with_name(event.new_name)

    # Persist to repository (source of truth)
    if folder_repo:
        folder_repo.save(updated_folder)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(
        data=updated_folder,
        rollback=RenameFolderCommand(
            folder_id=command.folder_id, new_name=event.old_name
        ),
    )
