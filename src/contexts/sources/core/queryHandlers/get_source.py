"""
Get Source Use Case (Query)

Functional query use case for getting a single source by ID.
Returns OperationResult for consistent handling in UI and AI consumers.
"""

from __future__ import annotations

from src.contexts.sources.core.commandHandlers._state import SourceRepository
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId
from src.shared.infra.state import ProjectState


def get_source(
    source_id: int,
    state: ProjectState,
    source_repo: SourceRepository,
) -> OperationResult:
    """
    Get a single source by ID.

    Args:
        source_id: ID of the source to retrieve
        state: Project state (for project check)
        source_repo: Repository for source queries (source of truth)

    Returns:
        OperationResult with Source details on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_FOUND/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    # Get source from repo (source of truth)
    sid = SourceId(value=source_id)
    source = source_repo.get_by_id(sid)

    if source is None:
        return OperationResult.fail(
            error=f"Source with id {source_id} not found",
            error_code="SOURCE_NOT_FOUND/NOT_FOUND",
            suggestions=(
                "Use list_sources to see available sources",
                "Check if the source ID is correct",
            ),
        )

    return OperationResult.ok(
        data={
            "source_id": source.id.value,
            "name": source.name,
            "source_type": source.source_type.value,
            "status": source.status.value,
            "file_path": str(source.file_path) if source.file_path else None,
            "file_size": source.file_size,
            "code_count": source.code_count,
            "memo": source.memo,
            "origin": source.origin,
            "folder_id": source.folder_id.value if source.folder_id else None,
            "modified_at": source.modified_at.isoformat()
            if source.modified_at
            else None,
        }
    )
