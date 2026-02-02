"""
Create Folder Use Case

Functional use case for creating a new folder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import CreateFolderCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import FolderState, derive_create_folder
from src.contexts.projects.core.entities import Folder
from src.contexts.projects.core.events import FolderCreated
from src.contexts.projects.core.failure_events import FolderNotCreated
from src.contexts.shared.core.types import FolderId

if TYPE_CHECKING:
    from src.application.contexts import SourcesContext
    from src.application.event_bus import EventBus


def create_folder(
    command: CreateFolderCommand,
    state: ProjectState,
    sources_ctx: SourcesContext,
    event_bus: EventBus,
) -> Result[Folder, str]:
    """
    Create a new folder in the current project.

    Args:
        command: Command with folder name and parent ID
        state: Project state cache
        sources_ctx: Sources context with folder repository
        event_bus: Event bus for publishing events

    Returns:
        Success with Folder entity, or Failure with error message
    """
    if state.project is None:
        return Failure("No project is currently open")

    parent_id = FolderId(value=command.parent_id) if command.parent_id else None

    # Build state and derive event
    folder_state = FolderState(
        existing_folders=tuple(state.folders),
        existing_sources=tuple(state.sources),
    )

    result = derive_create_folder(
        name=command.name,
        parent_id=parent_id,
        state=folder_state,
    )

    if isinstance(result, FolderNotCreated):
        return Failure(result.reason)

    event: FolderCreated = result

    # Create folder entity
    folder = Folder(
        id=event.folder_id,
        name=event.name,
        parent_id=event.parent_id,
        created_at=event.occurred_at,
    )

    # Persist and update state
    if sources_ctx and sources_ctx.folder_repo:
        sources_ctx.folder_repo.save(folder)

    state.add_folder(folder)

    # Publish event
    event_bus.publish(event)

    return Success(folder)
