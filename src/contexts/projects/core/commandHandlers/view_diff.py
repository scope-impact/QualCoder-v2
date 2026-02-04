"""
View Diff Command Handler

Simple query handler to view differences between snapshots.
Returns diff output from Git.

Usage:
    result = view_diff(
        from_ref="HEAD~1",
        to_ref="HEAD",
        git_adapter=git_adapter,
    )
    if result.is_success:
        print(result.data)  # Diff text
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter


def view_diff(
    from_ref: str,
    to_ref: str,
    git_adapter: GitRepositoryAdapter,
) -> OperationResult:
    """
    View differences between two snapshots.

    This is a simple query - no domain logic needed.
    Just calls git_adapter.diff() and returns the results.

    Args:
        from_ref: Starting commit reference (SHA, HEAD~N, etc.)
        to_ref: Ending commit reference
        git_adapter: Adapter for Git operations

    Returns:
        OperationResult.ok(data=str) with diff text on success
        OperationResult.fail() on failure
    """
    # Check if VCS is initialized
    if not git_adapter.is_initialized():
        return OperationResult.fail(
            error="Version control not initialized",
            error_code="DIFF_NOT_VIEWED/NOT_INITIALIZED",
            suggestions=("Initialize version control first",),
        )

    # Simple delegation to git adapter
    return git_adapter.diff(from_ref=from_ref, to_ref=to_ref)
