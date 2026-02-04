"""
List Snapshots Command Handler

Simple query handler to list version control snapshots.
Returns commit history from Git.

Usage:
    result = list_snapshots(
        limit=20,
        git_adapter=git_adapter,
    )
    if result.is_success:
        for commit in result.data:
            print(f"{commit.sha[:8]} - {commit.message}")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import (
        GitRepositoryAdapter,
    )


def list_snapshots(
    limit: int,
    git_adapter: GitRepositoryAdapter,
) -> OperationResult:
    """
    List version control snapshots (commit history).

    This is a simple query - no domain logic needed.
    Just calls git_adapter.log() and returns the results.

    Args:
        limit: Maximum number of snapshots to return
        git_adapter: Adapter for Git operations

    Returns:
        OperationResult.ok(data=list[CommitInfo]) on success
        OperationResult.fail() on failure
    """
    # Check if VCS is initialized
    if not git_adapter.is_initialized():
        return OperationResult.fail(
            error="Version control not initialized",
            error_code="SNAPSHOTS_NOT_LISTED/NOT_INITIALIZED",
            suggestions=("Initialize version control first",),
        )

    # Simple delegation to git adapter
    return git_adapter.log(limit=limit)
