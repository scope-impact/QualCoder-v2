"""
Delete Folder Use Case

Functional use case for deleting an empty folder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import DeleteFolderCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import FolderState, derive_delete_folder
from src.contexts.projects.core.events import FolderDeleted
from src.contexts.projects.core.failure_events import FolderNotDeleted
from src.contexts.shared.core.types import FolderId

if TYPE_CHECKING:
    from src.application.contexts import SourcesContext
    from src.application.event_bus import EventBus


def delete_folder(
    command: DeleteFolderCommand,
    state: ProjectState,
    sources_ctx: SourcesContext,
    event_bus: EventBus,
) -> Result[FolderDeleted, str]:
    """
    Delete an empty folder.

    Args:
        command: Command with folder ID
        state: Project state cache
        sources_ctx: Sources context with folder repository
        event_bus: Event bus for publishing events

    Returns:
        Success with FolderDeleted event, or Failure with error message
    """
    if state.project is None:
        return Failure("No project is currently open")

    folder_id = FolderId(value=command.folder_id)

    # Build state and derive event
    folder_state = FolderState(
        existing_folders=tuple(state.folders),
        existing_sources=tuple(state.sources),
    )

    result = derive_delete_folder(folder_id=folder_id, state=folder_state)

    if isinstance(result, FolderNotDeleted):
        return Failure(result.reason)

    event: FolderDeleted = result

    # Delete from repository and update state
    if sources_ctx and sources_ctx.folder_repo:
        sources_ctx.folder_repo.delete(folder_id)

    state.remove_folder(command.folder_id)

    # Publish event
    event_bus.publish(event)

    return Success(event)
