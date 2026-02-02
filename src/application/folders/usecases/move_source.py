"""
Move Source to Folder Use Case

Functional use case for moving a source to a folder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import MoveSourceToFolderCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import (
    FolderState,
    derive_move_source_to_folder,
)
from src.contexts.projects.core.events import SourceMovedToFolder
from src.contexts.projects.core.failure_events import SourceNotMoved
from src.contexts.shared.core.types import FolderId, SourceId

if TYPE_CHECKING:
    from src.application.contexts import SourcesContext
    from src.application.event_bus import EventBus


def move_source_to_folder(
    command: MoveSourceToFolderCommand,
    state: ProjectState,
    sources_ctx: SourcesContext,
    event_bus: EventBus,
) -> Result[SourceMovedToFolder, str]:
    """
    Move a source to a different folder.

    Args:
        command: Command with source ID and target folder ID
        state: Project state cache
        sources_ctx: Sources context with repositories
        event_bus: Event bus for publishing events

    Returns:
        Success with SourceMovedToFolder event, or Failure with error message
    """
    if state.project is None:
        return Failure("No project is currently open")

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
        return Failure(result.reason)

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

    return Success(event)
