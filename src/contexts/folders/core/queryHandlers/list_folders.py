"""
List Folders Use Case (Query)

Functional query use case for listing all folders in the project.
Returns OperationResult for consistent handling in UI and AI consumers.
"""

from __future__ import annotations

from src.contexts.folders.core.commandHandlers._state import FolderRepository
from src.shared.common.operation_result import OperationResult
from src.shared.infra.state import ProjectState


def list_folders(
    state: ProjectState,
    folder_repo: FolderRepository | None = None,
) -> OperationResult:
    """
    List all folders in the current project.

    Args:
        state: Project state (for project check)
        folder_repo: Repository for folder queries (source of truth)

    Returns:
        OperationResult with list of folder summaries on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="FOLDERS_NOT_LISTED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    # Get folders from repo (source of truth)
    folders = folder_repo.get_all() if folder_repo else []

    return OperationResult.ok(
        data={
            "folders": [
                {
                    "folder_id": folder.id.value,
                    "name": folder.name,
                    "parent_id": folder.parent_id.value if folder.parent_id else None,
                }
                for folder in folders
            ],
            "total_count": len(folders),
        }
    )
