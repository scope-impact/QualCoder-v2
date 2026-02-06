"""View Diff Command Handler - Returns diff output between snapshots."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter


def view_diff(
    from_ref: str, to_ref: str, git_adapter: GitRepositoryAdapter
) -> OperationResult:
    """View differences between two snapshots."""
    if not git_adapter.is_initialized():
        return OperationResult.fail(
            error="Version control not initialized",
            error_code="DIFF_NOT_VIEWED/NOT_INITIALIZED",
            suggestions=("Initialize version control first",),
        )
    return git_adapter.diff(from_ref=from_ref, to_ref=to_ref)
