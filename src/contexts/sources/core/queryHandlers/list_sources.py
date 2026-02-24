"""
List Sources Use Case (Query)

Functional query use case for listing all sources in the project.
Returns OperationResult for consistent handling in UI and AI consumers.
"""

from __future__ import annotations

from src.contexts.sources.core.commandHandlers._state import SourceRepository
from src.shared.common.operation_result import OperationResult
from src.shared.infra.state import ProjectState


def list_sources(
    state: ProjectState,
    source_repo: SourceRepository,
) -> OperationResult:
    """
    List all sources in the current project.

    Args:
        state: Project state (for project check)
        source_repo: Repository for source queries (source of truth)

    Returns:
        OperationResult with list of source summaries on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCES_NOT_LISTED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    # Get sources from repo (source of truth)
    sources = source_repo.get_all()

    return OperationResult.ok(
        data={
            "sources": [
                {
                    "source_id": source.id.value,
                    "name": source.name,
                    "source_type": source.source_type.value,
                    "status": source.status.value,
                    "file_size": source.file_size,
                    "code_count": source.code_count,
                    "memo": source.memo,
                    "origin": source.origin,
                    "folder_id": source.folder_id.value if source.folder_id else None,
                }
                for source in sources
            ],
            "total_count": len(sources),
        }
    )
