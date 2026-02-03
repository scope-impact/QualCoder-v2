"""
Get Folder Use Case (Query)

Functional query use case for getting a single folder by ID.
Returns OperationResult for consistent handling in UI and AI consumers.
"""

from __future__ import annotations

from src.contexts.folders.core.commandHandlers._state import (
    FolderRepository,
    SourceRepository,
)
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import FolderId
from src.shared.infra.state import ProjectState


def get_folder(
    folder_id: int,
    state: ProjectState,
    folder_repo: FolderRepository | None = None,
    source_repo: SourceRepository | None = None,
) -> OperationResult:
    """
    Get a single folder by ID.

    Args:
        folder_id: ID of the folder to retrieve
        state: Project state (for project check)
        folder_repo: Repository for folder queries (source of truth)
        source_repo: Repository for source queries (to count sources in folder)

    Returns:
        OperationResult with Folder details on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="FOLDER_NOT_FOUND/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    # Get folder from repo (source of truth)
    fid = FolderId(value=folder_id)
    folder = folder_repo.get_by_id(fid) if folder_repo else None

    if folder is None:
        return OperationResult.fail(
            error=f"Folder with id {folder_id} not found",
            error_code="FOLDER_NOT_FOUND/NOT_FOUND",
            suggestions=(
                "Use list_folders to see available folders",
                "Check if the folder ID is correct",
            ),
        )

    # Count sources in this folder using repo
    if source_repo:
        sources_in_folder = source_repo.get_by_folder(fid)
        source_count = len(sources_in_folder)
    else:
        source_count = 0

    return OperationResult.ok(
        data={
            "folder_id": folder.id.value,
            "name": folder.name,
            "parent_id": folder.parent_id.value if folder.parent_id else None,
            "source_count": source_count,
        }
    )
