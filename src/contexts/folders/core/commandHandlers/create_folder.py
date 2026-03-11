"""
Create Folder Use Case

Functional use case for creating a new folder.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.folders.core.commandHandlers._state import (
    FolderRepository,
    SourceRepository,
    build_folder_state,
)
from src.contexts.folders.core.commands import CreateFolderCommand, DeleteFolderCommand
from src.contexts.folders.core.derivers import derive_create_folder
from src.contexts.folders.core.entities import Folder
from src.contexts.folders.core.events import FolderCreated
from src.contexts.folders.core.failure_events import FolderNotCreated
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import FolderId
from src.shared.infra.metrics import metered_command
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session


logger = logging.getLogger("qualcoder.folders.core")


@metered_command("create_folder")
def create_folder(
    command: CreateFolderCommand,
    state: ProjectState,
    folder_repo: FolderRepository | None,
    source_repo: SourceRepository | None,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """
    Create a new folder in the current project.

    Args:
        command: Command with folder name and parent ID
        state: Project state cache
        folder_repo: Repository for folder operations
        source_repo: Repository for source operations
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with Folder on success, or error details on failure
    """
    logger.debug(
        "create_folder: name=%s, parent_id=%s", command.name, command.parent_id
    )

    if state.project is None:
        logger.error("create_folder: no project is currently open")
        return OperationResult.fail(
            error="No project is currently open",
            error_code="FOLDER_NOT_CREATED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    parent_id = FolderId(value=command.parent_id) if command.parent_id else None

    # Build state and derive event
    folder_state = build_folder_state(folder_repo, source_repo)

    result = derive_create_folder(
        name=command.name,
        parent_id=parent_id,
        state=folder_state,
    )

    if isinstance(result, FolderNotCreated):
        logger.error("create_folder: failed — %s", result.reason)
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

    if session:
        session.commit()

    # Publish event
    event_bus.publish(event)

    logger.info(
        "create_folder: created folder id=%s name=%s", folder.id.value, folder.name
    )
    return OperationResult.ok(
        data=folder,
        rollback=DeleteFolderCommand(folder_id=folder.id.value),
    )
