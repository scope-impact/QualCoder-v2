"""
Create Folder Use Case

Functional use case for creating a new folder.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.folders.core.commandHandlers._state import (
    FolderRepository,
    SourceRepository,
)
from src.contexts.projects.core.commands import CreateFolderCommand, DeleteFolderCommand
from src.contexts.projects.core.derivers import FolderState, derive_create_folder
from src.contexts.projects.core.entities import Folder
from src.contexts.projects.core.events import FolderCreated
from src.contexts.projects.core.failure_events import FolderNotCreated
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import FolderId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def create_folder(
    command: CreateFolderCommand,
    state: ProjectState,
    folder_repo: FolderRepository | None,
    source_repo: SourceRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Create a new folder in the current project.

    Args:
        command: Command with folder name and parent ID
        state: Project state cache
        folder_repo: Repository for folder operations
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with Folder on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="FOLDER_NOT_CREATED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    parent_id = FolderId(value=command.parent_id) if command.parent_id else None

    # Build state and derive event
    # Get existing data from repos (source of truth) instead of state cache
    existing_folders = tuple(folder_repo.get_all()) if folder_repo else ()
    existing_sources = tuple(source_repo.get_all()) if source_repo else ()
    folder_state = FolderState(
        existing_folders=existing_folders,
        existing_sources=existing_sources,
    )

    result = derive_create_folder(
        name=command.name,
        parent_id=parent_id,
        state=folder_state,
    )

    if isinstance(result, FolderNotCreated):
        return OperationResult.fail(
            error=result.reason,
            error_code=f"FOLDER_NOT_CREATED/{result.event_type.upper()}",
        )

    event: FolderCreated = result

    # Create folder entity
    folder = Folder(
        id=event.folder_id,
        name=event.name,
        parent_id=event.parent_id,
        created_at=event.occurred_at,
    )

    # Persist to repository (source of truth)
    if folder_repo:
        folder_repo.save(folder)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(
        data=folder,
        rollback=DeleteFolderCommand(folder_id=folder.id.value),
    )
