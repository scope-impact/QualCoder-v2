"""
Rename Folder Use Case

Functional use case for renaming a folder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import RenameFolderCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import FolderState, derive_rename_folder
from src.contexts.projects.core.entities import Folder
from src.contexts.projects.core.events import FolderRenamed
from src.contexts.projects.core.failure_events import FolderNotRenamed
from src.contexts.shared.core.types import FolderId

if TYPE_CHECKING:
    from src.application.contexts import SourcesContext
    from src.application.event_bus import EventBus


def rename_folder(
    command: RenameFolderCommand,
    state: ProjectState,
    sources_ctx: SourcesContext,
    event_bus: EventBus,
) -> Result[Folder, str]:
    """
    Rename an existing folder.

    Args:
        command: Command with folder ID and new name
        state: Project state cache
        sources_ctx: Sources context with folder repository
        event_bus: Event bus for publishing events

    Returns:
        Success with updated Folder, or Failure with error message
    """
    if state.project is None:
        return Failure("No project is currently open")

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
        return Failure(result.reason)

    event: FolderRenamed = result

    # Find and update folder
    folder = state.get_folder(command.folder_id)
    if folder is None:
        return Failure(f"Folder {command.folder_id} not found")

    updated_folder = folder.with_name(event.new_name)

    # Persist and update state
    if sources_ctx and sources_ctx.folder_repo:
        sources_ctx.folder_repo.save(updated_folder)

    state.update_folder(updated_folder)

    # Publish event
    event_bus.publish(event)

    return Success(updated_folder)
