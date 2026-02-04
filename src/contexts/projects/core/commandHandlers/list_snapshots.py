"""List Snapshots Command Handler - Returns commit history from Git."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter


def list_snapshots(limit: int, git_adapter: GitRepositoryAdapter) -> OperationResult:
    """List version control snapshots (commit history)."""
    if not git_adapter.is_initialized():
        return OperationResult.fail(
            error="Version control not initialized",
            error_code="SNAPSHOTS_NOT_LISTED/NOT_INITIALIZED",
            suggestions=("Initialize version control first",),
        )
    return git_adapter.log(limit=limit)
