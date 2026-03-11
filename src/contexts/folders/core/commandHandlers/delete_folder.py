"""
Delete Folder Use Case

Functional use case for deleting an empty folder.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.folders.core.commandHandlers._state import (
    FolderRepository,
    SourceRepository,
    build_folder_state,
)
from src.contexts.folders.core.commands import DeleteFolderCommand
from src.contexts.folders.core.derivers import derive_delete_folder
from src.contexts.folders.core.events import FolderDeleted
from src.contexts.folders.core.failure_events import FolderNotDeleted
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import FolderId
from src.shared.infra.metrics import metered_command
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session


logger = logging.getLogger("qualcoder.folders.core")


@metered_command("delete_folder")
def delete_folder(
    command: DeleteFolderCommand,
    state: ProjectState,
    folder_repo: FolderRepository | None,
    source_repo: SourceRepository | None,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """
    Delete an empty folder.

    Args:
        command: Command with folder ID
        state: Project state cache
        folder_repo: Repository for folder operations
        source_repo: Repository for source operations
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with FolderDeleted event on success, or error details on failure
    """
    logger.debug("delete_folder: folder_id=%s", command.folder_id)

    if state.project is None:
        logger.error("delete_folder: no project is currently open")
        return OperationResult.fail(
            error="No project is currently open",
            error_code="FOLDER_NOT_DELETED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    folder_id = FolderId(value=command.folder_id)

    # Build state and derive event
    folder_state = build_folder_state(folder_repo, source_repo)

    result = derive_delete_folder(folder_id=folder_id, state=folder_state)

    if isinstance(result, FolderNotDeleted):
        logger.error("delete_folder: failed — %s", result.reason)
        return OperationResult.fail(
            error=result.reason,
            error_code=f"FOLDER_NOT_DELETED/{result.event_type.upper()}",
        )

    event: FolderDeleted = result

    # Delete from repository (source of truth)
    if folder_repo:
        folder_repo.delete(folder_id)

    if session:
        session.commit()

    # Publish event
    event_bus.publish(event)

    # No rollback - would need to recreate folder
    logger.info("delete_folder: deleted folder id=%s", command.folder_id)
    return OperationResult.ok(data=event)
